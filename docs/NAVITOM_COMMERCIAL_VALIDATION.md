# NaviTom — Commercial Validation & Preorder Plan

Status: product strategy
Date: 2026-09-24

## Decision

NaviTom should be **customer-funded if validation supports it**, rather than financed with founder-personal debt.

Sequence:

> physical prototype -> convincing demo -> demand validation -> company/compliance gates -> limited preorder -> first production batch -> reinvest into product and brand

Do not use a glossy render as proof that the hardware is ready. The current codebase and Harley read-only integration make a credible prototype possible; prove that first.

## Product thesis

NaviTom is not only a round CarPlay/Android Auto display.

The defensible product is:

> a motorcycle-native smart instrument/navigation platform that identifies and adapts itself to the connected motorcycle, then safely configures its dashboard, telemetry and controls through a guided AI setup experience.

Core customer value:
- navigation / phone projection;
- a clean round motorcycle instrument;
- motorcycle telemetry where available;
- model-specific adaptation;
- simple setup instead of CAN reverse-engineering by the customer;
- profiles and future features delivered through software.

## V1 safety architecture

### Hard rule

**AI does not autonomously write to the motorcycle CAN bus in V1.**

Initial vehicle integration remains passive/read-only.

AI may:
- ask the rider for motorcycle make/model/year/trim;
- inspect supported passive telemetry;
- suggest signal mappings;
- guide a calibration sequence;
- compare observations with known compatibility profiles;
- choose UI modules and layout;
- explain unsupported signals;
- produce a proposed configuration.

Deterministic code must:
- validate signal ranges and units;
- bind a profile to exact motorcycle/hardware versions;
- reject uncertain mappings;
- keep unsupported values unavailable rather than guessed;
- preserve logs needed to diagnose bad mappings.

Any future CAN write/control feature requires a separate safety case, explicit deterministic controls, hardware-in-the-loop testing and model-specific validation.

## AI setup flow

1. Install NaviTom app on phone.
2. Power NaviTom and pair.
3. Select or scan motorcycle profile.
4. App identifies NaviTom hardware/firmware and attached adapter.
5. Passive CAN/telemetry discovery starts where supported.
6. Guided calibration:
   - ignition state;
   - engine off/on;
   - RPM idle/rev test where safe;
   - wheel-speed movement test only when safely possible;
   - turn indicators/high beam/gear state where available.
7. AI ranks candidate mappings against known profiles.
8. Deterministic validation accepts only mappings meeting confidence/range/consistency rules.
9. Rider sees exactly what was detected, inferred and unsupported.
10. Device installs the model-specific dashboard profile.
11. Profile version and compatibility evidence are stored for support/OTA.

## Moat

Do not make the moat "we put CarPlay on a round screen."

Build:
- validated motorcycle compatibility profiles;
- passive CAN decoding library;
- guided calibration data;
- hardware/adapter abstraction;
- per-bike UI layouts;
- safe OTA/profile updates;
- compatibility telemetry and support tooling;
- AI configuration assistant;
- installation knowledge base.

Every supported motorcycle should make the next integration cheaper.

## First target platform

Use the current founder bike / hardware path as the first deeply validated reference:

- 2017 Harley-Davidson Sportster Roadster XL1200CX;
- same-generation Sportster variants only after evidence proves compatible signals;
- 3.4-inch round display as the current reference design;
- OEM cluster retained during beta validation;
- CAN receive-only.

Do not claim broad Harley compatibility from one captured bike.

## Stage 0 — Physical proof

Gate before meaningful marketing spend:

- working round-display prototype;
- stable CarPlay/Android Auto path;
- reliable boot/shutdown;
- readable sunlight/night UI;
- basic touch/control flow;
- GPS;
- passive motorcycle telemetry on the target XL1200CX;
- stable power architecture;
- enclosure/mount prototype;
- real-bike ride video;
- thermal and vibration observations;
- no dangerous interference with OEM electronics.

Current open Harley integration PR is a development step, not hardware validation. Target-bike CAN capture remains required.

## Stage 1 — Landing + demand validation

Launch before paid preorder.

Landing page structure:
1. hero: actual device on motorcycle;
2. short real demo;
3. "adapts to your bike" setup story;
4. navigation + instrument cluster;
5. supported / testing / requested motorcycle matrix;
6. founder prototype story;
7. expected price band only after BOM work;
8. waitlist CTA;
9. form asking make/model/year and must-have features;
10. transparent prototype status.

Primary metric is not page traffic. It is **qualified rider intent**.

Track:
- visitor -> waitlist conversion;
- requested motorcycle models;
- country;
- iPhone vs Android;
- current navigation/device;
- acceptable price band;
- willingness to install DIY vs dealer installation;
- interest in founding batch;
- source/CAC.

## Stage 2 — Free waitlist first

Before there is a legal entity, stable BOM, delivery plan and consumer terms:

**collect interest, not customer money.**

Use:
- email waitlist;
- motorcycle model/year;
- "founding batch" interest;
- optional interview/tester opt-in.

Do not imply a guaranteed ship date.

## Stage 3 — Refundable reservation / preorder gate

Start taking money only after all are true:

- incorporated seller/entity and payment/tax path are ready;
- one validated physical prototype exists;
- target BOM and supplier quotes exist;
- first-batch quantity is capped;
- realistic manufacturing/assembly path exists;
- CE/conformity scope has been mapped;
- EMC and applicable radio/RED requirements are planned;
- RoHS/WEEE/product-safety obligations are mapped;
- warranty, returns, privacy and preorder/refund terms are written;
- software update/support policy exists;
- delivery window includes contingency;
- dependency and open-source license audit is complete;
- trademark/product-marketing review is complete.

Use a **limited founding batch**, not unlimited crowdfunding.

Customer funds should finance an already-estimated batch, not discover whether the product is buildable.

## EU cybersecurity / CRA gate

NaviTom is a connected hardware/software product and should be designed as a secure product from the start.

As of 2026-09-11, EU Cyber Resilience Act reporting duties for manufacturers already apply to actively exploited vulnerabilities and severe incidents affecting products with digital elements. The broader CRA obligations become fully applicable in 2027.

Build now:
- secure update path;
- signed/reproducible firmware/software release process where practical;
- vulnerability intake/disclosure channel;
- dependency/SBOM tracking;
- support-period policy;
- incident logging sufficient to investigate;
- secret/credential handling rules;
- documented security risk assessment before production.

This is cheaper to design in now than retrofit after preorder.

## Open-source / IP

The repository root currently uses the MIT License, which permits commercial use, modification, distribution and sale subject to preserving the required copyright/license notice.

That does **not** automatically clear:
- every transitive dependency;
- adapter firmware;
- Apple/Google marks and programme requirements;
- third-party hardware artwork/firmware;
- patents/design rights;
- upstream trademarks.

Complete a dependency/IP audit before public paid preorder.

## Unit economics gate

Before publishing a hard price, know:

- display;
- compute module;
- PCB/adapters;
- power conditioning;
- enclosure/mount;
- harness/connectors;
- assembly;
- test;
- packaging;
- freight;
- VAT/duties;
- payment fees;
- warranty reserve;
- returns;
- support;
- compliance/testing amortization.

Target a margin that still works after warranty/support/ads — not just BOM markup.

Validate price on the waitlist before locking industrial design.

## Marketing loop

Best acquisition assets are proof, not generic ads:

- real installation;
- side-by-side OEM vs NaviTom;
- 30–60s setup flow;
- day/night ride footage;
- "this bike had no modern dash — NaviTom learned it";
- compatibility additions;
- teardown/build journey;
- honest unsupported-model status.

Channels:
- motorcycle YouTube;
- Instagram/Reels/TikTok short demos;
- model-specific Facebook/Reddit/forums;
- micro-creators with specific motorcycles;
- installers/custom shops after product fit is clearer.

Do not spend heavily until waitlist/reservation conversion proves the message.

## First-batch operating rule

Cap the first paid batch to a quantity we can personally support and replace.

Goals:
- validate assembly;
- validate mounting/weather/vibration;
- validate support burden;
- collect compatibility evidence;
- identify failure modes;
- build high-quality customer proof.

Only then scale inventory and paid acquisition.

## Near-term execution

### Product
- finish/read-review Harley receive-only integration;
- capture target XL1200CX CAN traffic;
- validate RPM/speed/indicators/gear/other available fields conservatively;
- assemble 3.4-inch physical prototype;
- test power/boot/thermal/mounting.

### Software
- define versioned motorcycle profile schema;
- build guided setup/calibration workflow;
- add deterministic signal validation;
- add compatibility evidence/log export;
- keep AI advisory, not authoritative over safety-critical vehicle state.

### Commercial
- reserve/check NaviTom naming/domain/trademark risk;
- build landing/demo;
- launch waitlist with motorcycle-model questionnaire;
- recruit first model-specific testers;
- build BOM + supplier quote sheet;
- set preorder gate only after validation.

### Compliance
- map CE/EMC/RED/RoHS/WEEE/GPSR/CRA applicability with a qualified compliance path;
- plan testing before final enclosure/PCB freeze;
- maintain SBOM and vulnerability intake from prototype stage.

## Kill / pivot rules

Do not mass-produce if:
- riders like the visuals but will not pay the required sustainable price;
- too many motorcycles need bespoke hardware;
- passive telemetry is too fragmented to scale profile creation;
- support/install cost destroys margin;
- compliance/manufacturing cost pushes the product into a price segment with stronger incumbents;
- CarPlay/Android Auto dependency creates an unacceptable legal/technical bottleneck.

If telemetry fragmentation is high, pivot toward:
- premium navigation-first device + optional validated vehicle adapters;
- fewer deeply supported motorcycle families;
- installer/custom-shop channel.

The goal is a durable product business, not a one-off electronics project.
