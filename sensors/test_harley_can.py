#!/usr/bin/env python3

import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).with_name("harley_can.py")
SPEC = importlib.util.spec_from_file_location("harley_can", MODULE_PATH)
assert SPEC and SPEC.loader
harley_can = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harley_can)


class DecodeFrameTests(unittest.TestCase):
    def test_high_beam_off(self):
        patch = harley_can.decode_frame(0x550, bytes([0x00, 0x00, 0x02]))
        self.assertIs(patch["highBeam"], False)
        self.assertEqual(patch["harleyControlsRawByte"], 0x00)

    def test_high_beam_on_uses_bit_three_only(self):
        patch = harley_can.decode_frame(0x550, bytes([0x09, 0x00, 0x02]))
        self.assertIs(patch["highBeam"], True)
        self.assertEqual(patch["harleyControlsRawByte"], 0x09)

    def test_side_stand_is_raw_until_validated_on_roadster(self):
        self.assertEqual(
            harley_can.decode_frame(0x542, bytes([0x30])),
            {"harleySideStandRawByte": 0x30},
        )
    def test_throttle_is_raw_until_scaling_is_verified(self):
        self.assertEqual(
            harley_can.decode_frame(0x544, bytes([0xC8])),
            {"harleyThrottleRawByte": 0xC8},
        )

    def test_electrical_frame_keeps_unverified_values_raw(self):
        data = bytes([0x00, 0x00, 0x81, 0x00, 0x00, 0x73, 0x00, 0x00])
        self.assertEqual(
            harley_can.decode_frame(0x530, data),
            {
                "harleyNeutralRawByte": 0x81,
                "harleyBatteryRawByte": 0x73,
            },
        )

    def test_short_frames_never_index_past_payload(self):
        self.assertEqual(harley_can.decode_frame(0x530, bytes([0x00])), {})
        self.assertEqual(harley_can.decode_frame(0x541, bytes()), {})

    def test_unknown_frame_is_not_guessed(self):
        self.assertEqual(
            harley_can.decode_frame(0x521, bytes([1, 2, 3, 4, 5, 6, 7])),
            {},
        )

    def test_capture_record_preserves_raw_frame(self):
        record = harley_can.frame_record(0x550, bytes([0x08, 0x00]))
        self.assertEqual(record["id"], 0x550)
        self.assertEqual(record["id_hex"], "0x550")
        self.assertEqual(record["data"], [0x08, 0x00])
        self.assertEqual(record["data_hex"], "08 00")
        self.assertIsInstance(record["ts_ns"], int)


if __name__ == "__main__":
    unittest.main()
