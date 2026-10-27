# Cross-agent instructions — LIVI

Read and follow the existing root `CLAUDE.md` as the definitive build, Raspberry Pi, hardware, deployment and screenshot protocol. This file only supplements it with cross-agent critical review behavior.


## Cross-agent critical review and evidence contract (2026-10-14)

Applies to ChatGPT, Claude/Claude Code, Cursor and delegated agents. This supplements, never overrides, the project's canonical state, architecture decisions, security/privacy constraints, external-action approval gates, and cost limits.

1. Optimize for accuracy and working user-facing outcomes, not agreement, reassurance or contrarianism. Challenge flawed or risky assumptions with a specific reason, better alternative and tradeoff; do not invent objections when evidence supports an idea.
2. On consequential claims, distinguish **verified** (current source, exact artifact/run/link), **reasoned inference** and **unknown/not checked**. Model confidence labels and repeated agent agreement are not evidence. Research current claims at authoritative sources.
3. State blockers and negative results prominently. If challenged without new evidence, recheck reasoning rather than reflexively reverse or defensively repeat an answer.
4. Keep statuses distinct: **proposed**, **branch change**, **merged**, **tests passed**, **deployed**, **visually reviewed**, **owner-approved**, **user-visible verified**. A commit, generated artifact, green CI or agent statement does not by itself establish product completion.
5. For delivery, inspect relevant runtime/UI, output artifact, representative inputs, failures, visual QA and deployment evidence where tools allow. Report exact evidence, remaining uncertainty and the next safe action; never claim unattended/background work without an actual scheduled or running process.
6. Prefer the smallest falsifiable change that improves the active product bottleneck. Do not generate additional strategies, reports, orchestration or paid experiments instead of shipping and verifying real outcomes.
7. Retain every repository-specific consent, financial, safety, privacy, release, recovery and authority rule. This section does not authorize external actions or weaken existing gates.

## OWNER-WIDE NON-NEGOTIABLE TYPOGRAPHY RULE (2026-10-27)

Apply to all agents and authored outputs, including email, casting applications, source code copy, UIs, documentation, social posts, notifications and generated text.
- Never emit Unicode long dashes U+2012, U+2013, U+2014, U+2015. Use ASCII hyphen-minus (U+002D), comma, colon or full stop instead.
- Validate final subject/body/signature/payload before external sending, committing or publishing. Add deterministic text lint and regression tests at each outbound boundary.
- Keep source/legal meaning unchanged when reproducing third-party materials.
- Make this a default bootstrap requirement for future repositories.
