#!/usr/bin/env python3

import importlib.util
import json
import pathlib
import tempfile
import unittest

MODULE_PATH = pathlib.Path(__file__).with_name("harley_can_analyze.py")
SPEC = importlib.util.spec_from_file_location("harley_can_analyze", MODULE_PATH)
assert SPEC and SPEC.loader
analyze = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyze)


def write_capture(path: pathlib.Path, rpm_raw: int, noise: int) -> None:
    frames = []
    for step in range(9):
        frames.append(
            {
                "id": 0x521,
                "data": [
                    (rpm_raw >> 8) & 0xFF,
                    rpm_raw & 0xFF,
                    (noise + step * 17) & 0xFF,
                    0x55,
                ],
            }
        )
        frames.append(
            {
                "id": 0x550,
                "data": [0x08 if step % 2 else 0x00, 0x00, 0x02],
            }
        )
    with path.open("w", encoding="utf-8") as handle:
        for frame in frames:
            handle.write(json.dumps(frame) + "\n")


class AnalyzerTests(unittest.TestCase):
    def test_frame_candidates_include_both_u16_orders(self):
        candidates = dict(analyze.frame_candidates([0x12, 0x34]))
        self.assertEqual(candidates["b0"], 0x12)
        self.assertEqual(candidates["b1"], 0x34)
        self.assertEqual(candidates["u16be@0"], 0x1234)
        self.assertEqual(candidates["u16le@0"], 0x3412)

    def test_series_can_recover_linear_big_endian_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            labels = [1500.0, 2000.0, 2500.0, 3000.0]
            captures = []
            for index, rpm in enumerate(labels):
                path = tmp_path / f"rpm-{int(rpm)}.jsonl"
                write_capture(path, int(rpm * 2), noise=40 + index * 3)
                captures.append(analyze.aggregate(analyze.load_records(str(path))))

            key = (0x521, "u16be@0")
            raw = [capture[key] for capture in captures]
            correlation = analyze.pearson(raw, labels)
            slope, intercept, rmse = analyze.regression(raw, labels)

            self.assertAlmostEqual(correlation, 1.0)
            self.assertAlmostEqual(slope, 0.5)
            self.assertAlmostEqual(intercept, 0.0)
            self.assertAlmostEqual(rmse, 0.0)

    def test_parse_series_requires_three_sessions(self):
        with self.assertRaises(ValueError):
            analyze.parse_series(["1000=a.jsonl", "2000=b.jsonl"])


if __name__ == "__main__":
    unittest.main()
