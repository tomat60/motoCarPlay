#!/usr/bin/env python3
"""Read-only Harley-Davidson Sportster CAN -> LIVI telemetry bridge.

Target: 2017 XL1200CX. The initial signal map is deliberately conservative.
Only signals backed by same-generation XL1200X captures are decoded. Unknown
frames can be written to JSONL for controlled reverse-engineering sessions.

Safety invariant: this process never transmits a CAN frame.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

LIVI_URL = "http://localhost:4000"
CAN_BITRATE = 500_000

# Public 2017 XL1200X reverse-engineering evidence. Values that still lack
# scaling/formula are exposed only as raw extension fields.
FRAME_CONTROLS = 0x550
FRAME_SIDE_STAND = 0x542
FRAME_THROTTLE = 0x544
FRAME_ENGINE_TEMP = 0x541
FRAME_ELECTRICAL = 0x530

def decode_frame(arbitration_id: int, data: bytes) -> dict[str, Any]:
    """Return a conservative LIVI telemetry patch for one CAN frame."""
    patch: dict[str, Any] = {}

    if arbitration_id == FRAME_CONTROLS and len(data) >= 1:
        # 2017 XL1200X captures: low beam byte0=0x00, high beam byte0=0x08.
        patch["highBeam"] = bool(data[0] & 0x08)
        patch["harleyControlsRawByte"] = data[0]

    elif arbitration_id == FRAME_SIDE_STAND and len(data) >= 1:
        # Known examples: up=0x00, down=0x30. Keep raw until validated on CX.
        patch["harleySideStandRawByte"] = data[0]

    elif arbitration_id == FRAME_THROTTLE and len(data) >= 1:
        patch["harleyThrottleRawByte"] = data[0]

    elif arbitration_id == FRAME_ENGINE_TEMP and len(data) >= 6:
        patch["harleyEngineTempRawByte"] = data[5]

    elif arbitration_id == FRAME_ELECTRICAL and len(data) >= 6:
        # Same-generation work places neutral in byte2 and battery in byte5,
        # but published scaling/state mapping is incomplete.
        patch["harleyNeutralRawByte"] = data[2]
        patch["harleyBatteryRawByte"] = data[5]

    return patch


def frame_record(arbitration_id: int, data: bytes) -> dict[str, Any]:
    return {
        "ts_ns": time.time_ns(),
        "id": arbitration_id,
        "id_hex": f"0x{arbitration_id:03X}",
        "data": list(data),
        "data_hex": data.hex(" ").upper(),
    }

def require_socketcan_listen_only(channel: str, allow_active: bool) -> None:
    """Fail closed unless SocketCAN reports listen-only mode."""
    if allow_active:
        print(
            "[harley-can] WARNING: active CAN interface explicitly allowed; "
            "the bridge itself still never calls send().",
            file=sys.stderr,
        )
        return

    result = subprocess.run(
        ["ip", "-details", "link", "show", channel],
        check=False,
        capture_output=True,
        text=True,
    )
    details = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
        raise RuntimeError(
            f"cannot inspect {channel}; configure SocketCAN first. {details.strip()}"
        )

    normalized = details.upper()
    if "LISTEN-ONLY" not in normalized and "LISTEN_ONLY" not in normalized:
        raise RuntimeError(
            f"{channel} is not confirmed LISTEN-ONLY. Refusing to attach. "
            "Configure the interface in listen-only mode first."
        )


def open_capture(path: str | None):
    if not path:
        return None
    capture_path = Path(path).expanduser()
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[harley-can] capturing raw frames -> {capture_path}")
    return capture_path.open("a", encoding="utf-8", buffering=1)


def iter_can_frames(interface: str, channel: str | None, allow_active: bool):
    """Yield arbitration ID and payload while keeping the bus receive-only."""
    selected = interface
    if selected == "auto":
        selected = "gs_usb" if sys.platform == "darwin" else "socketcan"

    if selected == "socketcan":
        actual_channel = channel or "can0"
        require_socketcan_listen_only(actual_channel, allow_active)
        import can  # type: ignore

        bus = can.Bus(interface="socketcan", channel=actual_channel)
        try:
            for message in bus:
                yield int(message.arbitration_id), bytes(message.data)
        finally:
            bus.shutdown()
        return

    if selected == "slcan":
        if not channel:
            raise RuntimeError("--channel is required for slcan, e.g. /dev/cu.usbmodem...@115200")
        import can  # type: ignore

        bus = can.Bus(
            interface="slcan",
            channel=channel,
            bitrate=CAN_BITRATE,
            listen_only=not allow_active,
        )
        try:
            for message in bus:
                yield int(message.arbitration_id), bytes(message.data)
        finally:
            bus.shutdown()
        return

    if selected == "gs_usb":
        from gs_usb.constants import GS_CAN_MODE_LISTEN_ONLY  # type: ignore
        from gs_usb.gs_usb import GsUsb  # type: ignore
        from gs_usb.gs_usb_frame import GsUsbFrame  # type: ignore

        try:
            index = int(channel) if channel is not None else 0
        except ValueError as exc:
            raise RuntimeError("gs_usb --channel must be a numeric device index") from exc

        devices = GsUsb.scan()
        if index < 0 or index >= len(devices):
            raise RuntimeError(f"gs_usb device index {index} not found; detected {len(devices)} device(s)")
        dev = devices[index]

        if not allow_active and not (dev.device_capability.feature & GS_CAN_MODE_LISTEN_ONLY):
            raise RuntimeError("gs_usb firmware does not advertise listen-only mode; refusing to attach")

        if not dev.set_bitrate(CAN_BITRATE):
            raise RuntimeError(f"failed to configure gs_usb bitrate {CAN_BITRATE}")

        flags = 0 if allow_active else GS_CAN_MODE_LISTEN_ONLY
        if not allow_active:
            print("[harley-can] gs_usb listen-only mode confirmed by device capability")
        dev.start(flags)
        try:
            while True:
                frame = GsUsbFrame()
                if dev.read(frame=frame, timeout_ms=1000):
                    payload = bytes(frame.data[: frame.can_dlc])
                    yield int(frame.arbitration_id), payload
        finally:
            dev.stop()
        return

    raise RuntimeError(f"unsupported CAN interface: {selected}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interface",
        choices=("auto", "socketcan", "gs_usb", "slcan"),
        default="auto",
        help="auto uses gs_usb on macOS and SocketCAN elsewhere",
    )
    parser.add_argument(
        "--channel",
        help="SocketCAN name, gs_usb device index, or SLCAN serial port",
    )
    parser.add_argument("--server", default=LIVI_URL)
    parser.add_argument("--capture", help="append every received CAN frame to JSONL")
    parser.add_argument(
        "--emit-raw",
        action="store_true",
        help="also push raw CAN frames into LIVI telemetry (noisy; diagnostics only)",
    )
    parser.add_argument(
        "--unsafe-allow-active-can",
        action="store_true",
        help="bypass interface listen-only verification; not recommended on the bike",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        import socketio  # type: ignore
    except ImportError as exc:
        print(
            "[harley-can] missing dependency. Install: "
            "python3 -m pip install python-socketio",
            file=sys.stderr,
        )
        print(f"[harley-can] import error: {exc}", file=sys.stderr)
        return 3

    capture = open_capture(args.capture)
    sio = socketio.Client(reconnection=True, reconnection_attempts=0)

    try:
        sio.connect(args.server)
        selected = args.interface
        if selected == "auto":
            selected = "gs_usb" if sys.platform == "darwin" else "socketcan"
        display_channel = args.channel if args.channel is not None else ("0" if selected == "gs_usb" else "can0")
        print(
            f"[harley-can] listening via {selected}:{display_channel} @ {CAN_BITRATE} bit/s; "
            "receive-only policy enabled"
        )

        for arbitration_id, data in iter_can_frames(
            args.interface, args.channel, args.unsafe_allow_active_can
        ):
            record = frame_record(arbitration_id, data)
            if capture:
                capture.write(json.dumps(record, separators=(",", ":")) + "\n")

            patch = decode_frame(arbitration_id, data)
            if args.emit_raw:
                patch["can"] = {"id": arbitration_id, "data": list(data)}
            if patch:
                patch["ts"] = int(time.time() * 1000)
                sio.emit("telemetry:push", patch)

    except (RuntimeError, ImportError) as exc:
        print(f"[harley-can] SAFETY STOP: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\n[harley-can] stopped")
    finally:
        if capture:
            capture.close()
        try:
            sio.disconnect()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
