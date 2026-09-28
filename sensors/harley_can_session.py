#!/usr/bin/env python3
"""Guided, receive-only XL1200CX stationary CAN capture session.

This helper deliberately avoids road-speed calibration. It orchestrates short,
labeled captures through harley_can.py and then prints/runs useful offline
analysis commands. The underlying CAN bridge remains receive-only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaptureStep:
    key: str
    prompt: str
    seconds: int = 8


STATIONARY_STEPS = (
    CaptureStep("baseline", "Ignition ON, engine OFF, controls untouched.", 10),
    CaptureStep("highbeam_off", "High beam OFF / normal low beam."),
    CaptureStep("highbeam_on", "High beam ON."),
    CaptureStep("stand_up", "Side stand UP. Keep bike safely supported."),
    CaptureStep("stand_down", "Side stand DOWN."),
    CaptureStep("neutral", "Select NEUTRAL."),
    CaptureStep(
        "first",
        "Select FIRST gear with engine OFF and clutch held, only if this is safe/easy.",
    ),
    CaptureStep("idle", "Start engine, select neutral and let it idle steadily.", 12),
    CaptureStep("rpm_1500", "Hold about 1500 RPM using the OEM tachometer."),
    CaptureStep("rpm_2000", "Hold about 2000 RPM using the OEM tachometer."),
    CaptureStep("rpm_2500", "Hold about 2500 RPM using the OEM tachometer."),
    CaptureStep("rpm_3000", "Hold about 3000 RPM using the OEM tachometer."),
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", choices=("auto", "gs_usb", "slcan", "socketcan"), default="auto")
    parser.add_argument("--channel", help="gs_usb index, SLCAN port, or SocketCAN channel")
    parser.add_argument(
        "--output",
        default="~/harley-can/sessions",
        help="root directory for timestamped capture sessions",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the complete session without opening CAN hardware",
    )
    return parser


def capture_command(script_dir: Path, args: argparse.Namespace, capture: Path) -> list[str]:
    command = [
        sys.executable,
        str(script_dir / "harley_can.py"),
        "--interface",
        args.interface,
        "--no-livi",
        "--capture",
        str(capture),
    ]
    if args.channel is not None:
        command.extend(["--channel", args.channel])
    return command


def run_capture(command: list[str], seconds: int) -> int:
    proc = subprocess.Popen(command)
    try:
        time.sleep(seconds)
        proc.send_signal(signal.SIGINT)
        return proc.wait(timeout=5)
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=5)
        raise
    except subprocess.TimeoutExpired:
        proc.terminate()
        return proc.wait(timeout=3)

def run_analysis(script_dir: Path, session: Path) -> None:
    analyzer = [sys.executable, str(script_dir / "harley_can_analyze.py")]

    print("\n=== Automatic analysis ===")
    baseline = session / "baseline.jsonl"
    subprocess.run([*analyzer, "summary", str(baseline)], check=False)

    for left, right in (
        ("highbeam_off", "highbeam_on"),
        ("stand_up", "stand_down"),
        ("neutral", "first"),
    ):
        print(f"\n--- diff: {left} -> {right} ---")
        subprocess.run(
            [
                *analyzer,
                "diff",
                str(session / f"{left}.jsonl"),
                str(session / f"{right}.jsonl"),
                "--top",
                "15",
            ],
            check=False,
        )

    rpm_files = [
        f"{rpm}={session / f'rpm_{rpm}.jsonl'}"
        for rpm in (1500, 2000, 2500, 3000)
    ]
    print("\n--- RPM series candidates ---")
    subprocess.run([*analyzer, "series", *rpm_files, "--top", "20"], check=False)


def main() -> int:
    args = build_parser().parse_args()
    script_dir = Path(__file__).resolve().parent
    root = Path(args.output).expanduser()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    session = root / stamp

    print("XL1200CX stationary CAN discovery")
    print("Safety: bike stationary, ventilated area, OEM cluster retained.")
    print("The CAN bridge is opened in listen-only mode and never sends frames.")
    print(f"Session directory: {session}")

    if args.dry_run:
        for step in STATIONARY_STEPS:
            path = session / f"{step.key}.jsonl"
            print(f"{step.key:14} {step.seconds:2}s  {step.prompt}")
            print("  " + " ".join(capture_command(script_dir, args, path)))
        return 0

    session.mkdir(parents=True, exist_ok=False)

    try:
        for index, step in enumerate(STATIONARY_STEPS, 1):
            print(f"\n[{index}/{len(STATIONARY_STEPS)}] {step.prompt}")
            answer = input("Press Enter when ready, or type SKIP: ").strip().lower()
            if answer == "skip":
                print(f"Skipped {step.key}")
                continue

            capture = session / f"{step.key}.jsonl"
            print(f"Capturing {step.seconds}s -> {capture.name}")
            code = run_capture(capture_command(script_dir, args, capture), step.seconds)
            if code not in (0, 130):
                print(f"Capture exited with code {code}; stopping for safety.", file=sys.stderr)
                return code or 2

    except KeyboardInterrupt:
        print("\nSession interrupted. Existing captures are preserved.")
        return 130

    required = {
        "baseline",
        "highbeam_off",
        "highbeam_on",
        "stand_up",
        "stand_down",
        "neutral",
        "first",
        "rpm_1500",
        "rpm_2000",
        "rpm_2500",
        "rpm_3000",
    }
    existing = {path.stem for path in session.glob("*.jsonl")}
    if required <= existing:
        run_analysis(script_dir, session)
    else:
        missing = sorted(required - existing)
        print(f"\nAnalysis not auto-run because captures are missing: {', '.join(missing)}")

    print(f"\nSaved session: {session}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

