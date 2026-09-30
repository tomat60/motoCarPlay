#!/usr/bin/env python3
"""Analyze labeled Harley CAN JSONL captures without guessing signal maps."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

SignalKey = tuple[int, str]


def load_records(path: str) -> list[dict]:
    records: list[dict] = []
    with Path(path).expanduser().open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                arbitration_id = int(record["id"])
                data = [int(value) for value in record["data"]]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_no}: invalid capture record: {exc}") from exc
            records.append({"id": arbitration_id, "data": data})
    if not records:
        raise ValueError(f"{path}: no CAN records")
    return records


def frame_candidates(data: list[int]) -> Iterable[tuple[str, int]]:
    for index, value in enumerate(data):
        yield f"b{index}", value
    for index in range(len(data) - 1):
        left, right = data[index], data[index + 1]
        yield f"u16be@{index}", (left << 8) | right
        yield f"u16le@{index}", left | (right << 8)


def collect_values(records: list[dict]) -> dict[SignalKey, list[int]]:
    values: dict[SignalKey, list[int]] = defaultdict(list)
    for record in records:
        arbitration_id = record["id"]
        for name, value in frame_candidates(record["data"]):
            values[(arbitration_id, name)].append(value)
    return values


def aggregate(records: list[dict]) -> dict[SignalKey, float]:
    return {
        key: float(statistics.median(samples))
        for key, samples in collect_values(records).items()
    }


def aggregate_stats(records: list[dict]) -> dict[SignalKey, tuple[float, float]]:
    stats: dict[SignalKey, tuple[float, float]] = {}
    for key, samples in collect_values(records).items():
        median = float(statistics.median(samples))
        spread = float(statistics.pstdev(samples)) if len(samples) > 1 else 0.0
        stats[key] = (median, spread)
    return stats


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx, my = statistics.mean(xs), statistics.mean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    denominator = math.sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    if denominator == 0:
        return 0.0
    return sum(x * y for x, y in zip(dx, dy)) / denominator


def regression(raw: list[float], labels: list[float]) -> tuple[float, float, float]:
    mean_x, mean_y = statistics.mean(raw), statistics.mean(labels)
    variance = sum((x - mean_x) ** 2 for x in raw)
    slope = 0.0 if variance == 0 else sum(
        (x - mean_x) * (y - mean_y) for x, y in zip(raw, labels)
    ) / variance
    intercept = mean_y - slope * mean_x
    rmse = math.sqrt(
        statistics.mean((label - (slope * value + intercept)) ** 2 for value, label in zip(raw, labels))
    )
    return slope, intercept, rmse


def cmd_summary(args: argparse.Namespace) -> int:
    records = load_records(args.capture)
    counts = Counter(record["id"] for record in records)
    print(f"frames={len(records)} ids={len(counts)}")
    for arbitration_id, count in counts.most_common():
        lengths = Counter(len(record["data"]) for record in records if record["id"] == arbitration_id)
        print(f"0x{arbitration_id:03X}  frames={count:6d}  dlc={dict(sorted(lengths.items()))}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    left = aggregate(load_records(args.baseline))
    right = aggregate(load_records(args.changed))
    rows = []
    for key in left.keys() & right.keys():
        delta = right[key] - left[key]
        if delta:
            rows.append((abs(delta), delta, key, left[key], right[key]))
    rows.sort(reverse=True)
    print("rank  CAN    candidate   baseline   changed   delta")
    for rank, (_, delta, (arbitration_id, name), before, after) in enumerate(rows[: args.top], 1):
        print(f"{rank:>4}  0x{arbitration_id:03X}  {name:<9}  {before:>8.1f}  {after:>8.1f}  {delta:>+8.1f}")
    return 0


def parse_series(items: list[str]) -> list[tuple[float, str]]:
    parsed: list[tuple[float, str]] = []
    for item in items:
        if "=" not in item:
            raise ValueError(f"series item must be VALUE=FILE, got {item!r}")
        label_text, path = item.split("=", 1)
        parsed.append((float(label_text), path))
    if len(parsed) < 3:
        raise ValueError("series analysis needs at least three labeled captures")
    return parsed


def cmd_series(args: argparse.Namespace) -> int:
    series = parse_series(args.samples)
    labels = [label for label, _ in series]
    captures = [aggregate_stats(load_records(path)) for _, path in series]
    common = set(captures[0])
    for capture in captures[1:]:
        common &= set(capture)

    rows = []
    for key in common:
        raw = [capture[key][0] for capture in captures]
        spreads = [capture[key][1] for capture in captures]
        correlation = pearson(raw, labels)
        if abs(correlation) < args.min_correlation:
            continue
        between_span = max(raw) - min(raw)
        mean_spread = statistics.mean(spreads)
        stability = between_span / (between_span + mean_spread) if between_span else 0.0
        slope, intercept, rmse = regression(raw, labels)
        score = abs(correlation) * stability
        rows.append((score, abs(correlation), correlation, stability, rmse, key, slope, intercept, raw))
    rows.sort(reverse=True)

    print("rank  CAN    candidate   score    corr     stable    rmse      label ~= raw*slope + intercept")
    for rank, (_, _, corr, stability, rmse, (arbitration_id, name), slope, intercept, raw) in enumerate(
        rows[: args.top], 1
    ):
        print(
            f"{rank:>4}  0x{arbitration_id:03X}  {name:<9}  {abs(corr) * stability:>6.4f}  "
            f"{corr:>+7.4f}  {stability:>7.4f}  {rmse:>8.3f}   "
            f"{slope:.8g} * raw {intercept:+.5g}   raw={raw}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    summary = sub.add_parser("summary", help="list observed CAN IDs and frame counts")
    summary.add_argument("capture")
    summary.set_defaults(func=cmd_summary)

    diff = sub.add_parser("diff", help="rank signals that changed between two captures")
    diff.add_argument("baseline")
    diff.add_argument("changed")
    diff.add_argument("--top", type=int, default=30)
    diff.set_defaults(func=cmd_diff)

    series = sub.add_parser("series", help="correlate labeled captures with byte/u16 candidates")
    series.add_argument("samples", nargs="+", metavar="VALUE=FILE")
    series.add_argument("--top", type=int, default=30)
    series.add_argument("--min-correlation", type=float, default=0.90)
    series.set_defaults(func=cmd_series)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError) as exc:
        print(f"[harley-can-analyze] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
