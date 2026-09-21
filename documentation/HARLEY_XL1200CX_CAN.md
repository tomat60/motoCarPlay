# Harley-Davidson XL1200CX CAN integration

Status: experimental, read-only bring-up for a 2017 Sportster Roadster XL1200CX.

The first milestone is intentionally not a replacement instrument. It is a
safe telemetry bridge that can capture the bike bus and feed verified signals
into LIVI. The stock gauge stays installed until critical data and failure
behaviour are validated on the actual motorcycle.

## Why this target is promising

Public reverse-engineering already exists for a **2017 XL1200X Forty-Eight**,
the same Sportster generation as the target XL1200CX:

- https://github.com/earnaz/Harley-Davidson-CAN-Bus
- 6-pin Deutsch diagnostic connector
- CAN High: diagnostic connector pin 1
- CAN Low: diagnostic connector pin 3
- published example code uses 500 kbit/s

Treat these as a starting point, not as proof that every XL1200CX signal is
identical. Verify electrically and from controlled captures on the target bike.

## Safety policy

During reverse-engineering the adapter is **receive-only**:

1. Configure the Linux SocketCAN interface in listen-only mode.
2. sensors/harley_can.py refuses to start unless listen-only is visible in
   ip -details link show.
3. The bridge contains no bus.send() call.
4. Do not add a 120-ohm terminator across the motorcycle bus by default.
5. Do not remove the OEM cluster during this phase.
## Pi / SocketCAN setup

The exact command depends on the chosen CAN interface. For a native SocketCAN
device exposed as can0, the intended configuration is:

    sudo ip link set can0 down
    sudo ip link set can0 type can bitrate 500000 listen-only on
    sudo ip link set can0 up
    ip -details link show can0

Install the two Python dependencies:

    python3 -m pip install python-can python-socketio

Start LIVI, then start a capture:

    python3 sensors/harley_can.py --channel can0 \
      --capture ~/harley-can/idle-01.jsonl

--emit-raw is available for diagnostics, but normally raw high-rate traffic
should go to JSONL instead of through the live UI telemetry store.

## What is decoded now

The first bridge only promotes evidence-backed values:

| CAN ID | Current handling | Confidence |
| --- | --- | --- |
| 0x550 | high-beam bit + raw controls byte | high for 2017 XL1200X, verify CX |
| 0x542 | raw side-stand byte | mapping example known, semantics not promoted |
| 0x544 | raw throttle byte | location known, scaling not published |
| 0x541 | raw engine-temperature byte | location known, scaling not published |
| 0x530 | raw neutral + battery bytes | byte locations known, scaling/state incomplete |

Speed (0x521 in public captures) and RPM are deliberately **not guessed** yet.
They become first-class speedKph / rpm only after repeatable CX captures prove
the frame, byte order and scaling.
## Controlled capture plan

Use separate files and change one variable at a time:

1. Ignition on, engine off, all controls untouched.
2. Low beam then high beam, several clean transitions.
3. Side stand up/down.
4. Neutral versus first gear with the bike stationary and safely supported.
5. Engine idle for 30-60 seconds.
6. Controlled RPM holds visible on the OEM tachometer: idle / 1500 / 2000 /
   2500 / 3000 RPM.
7. Controlled speed samples with OEM speed visible or GPS reference:
   0 / 20 / 40 / 60 / 80 km/h.
8. Short real ride only after stationary capture is clean.

For RPM and speed, correlate candidate bytes across captures rather than
selecting a plausible-looking formula from one frame.

## Product milestones

**M0 - bridge:** receive-only CAN capture + LIVI transport.
**M1 - core cluster:** verified speed, RPM, neutral/gear and battery voltage.
**M2 - telltales:** high beam, indicators, warning/MIL, fuel/range where available.
**M3 - replacement-gauge safety:** startup time, brownout recovery, thermal tests,
weather sealing, readable-in-sun UI and defined fail-safe behaviour.
**M4 - wider Sportster support:** model/year compatibility matrix backed by logs,
not assumptions.

The replacement-gauge milestone is complete only when the OEM cluster can be
removed without losing required rider information or creating a single-point
failure that leaves the rider blind to speed or warnings.
