# Giving Your AI Agent a Black Box: Auditing Every Decision in a 3^9 = 19,683-State Cognitive Space

You shipped an AI agent. It runs your RAG pipeline, calls your tools, writes your reports. Life is good — until the day it quietly calls a tool it shouldn't, signs off on a high-risk conclusion with zero evidence, or contradicts itself between step 3 and step 4.

The model isn't dumb. The problem is that your agent's "autopilot" has no black box.

Airplanes have had black boxes for decades. Agents should too. That's why I open-sourced **agent-audit-mcp** — a cognitive black box that encodes every agent decision into an enumerable, comparable, reproducible state.

## Why agent decisions are so hard to audit

Four failure modes you've probably already met:

1. **Permission overreach** — it touched a tool or dataset outside its scope.
2. **High-risk conclusions without evidence** — full-position trades, deletions, external commitments, no basis.
3. **Untraceable citations** — the conclusion is right, but you can't tell where it came from.
4. **State-jump escapes** — conservative in step 1, aggressive in step 2, with nothing in between.

The hard part: a decision is a *process*, but logs are just a *stream*. To make the process auditable, you first need to turn "one decision step" into an **enumerable, comparable state**. That's the core idea of agent-audit-mcp.

## The core idea: one decision = a nine-dimensional state

We describe one decision step along **9 observation dimensions**:

> Structure · Function · Relation · Attribute · Time · Context · Causality · Value · Evolution

Each dimension takes **three states**:

- `⊕` (+1) — strong / above baseline
- `0` (0) — neutral
- `⊖` (−1) — weak / deficient

So one decision step = a nine-dimensional trinary vector, e.g. `0⊖0⊖000⊖0`.
Nine trinary digits give **3⁹ = 19,683** states. The all-zero center state has enumeration key `idx = 9841`.

This is the trinary thinking of Eastern philosophy (⊖ / 0 / ⊕) crossed with modern AI engineering: **enumerable** (every decision has a unique address), **comparable** (any two states have a Hamming distance), **reproducible** (same input, same state, every time).

## The verdict rules: transparent, reproducible, tunable

With states in hand, auditing becomes a handful of clear rules:

| Trigger | Verdict | Action |
| --- | --- | --- |
| v6 Context · **permission overreach** | 🔴 **BLOCK** | Halt execution, roll back, re-authorize |
| v7 Causality · **missing evidence**, or v8 Value · **high risk** | 🟠 **ALERT** | Stop automation, route to compliance review |
| Adjacent-step Hamming distance **> 4** (state jump) | 🟡 **WATCH** | Human review of the jump point |
| None of the above | 🟢 **OK** | Continue |

Thresholds (what counts as "high risk" or "missing evidence") are **all overridable via environment variables**, so you can calibrate against your real logs. The rules are transparent to you — not a black box inside the black box.

## Real output — the engine actually ran

Four scenarios, real local engine output:

- 🟢 **Normal advisory → OK**: step 1 `0⊖0000000` (idx=7654), step 2 `0⊕0⊕00⊕⊕0` (idx=12283). No red lines, no jumps.
- 🟠 **High-risk full-position advice → ALERT**: step 1 `0⊖0⊖000⊖0` (idx=7408) hits v8 high-risk; step 2 `⊖⊕⊖⊖⊕0⊖⊖⊕` (idx=4565) hits v7 missing-evidence + v8 high-risk.
- 🔴 **Unauthorized query + stock pick → BLOCK**: step 1 `0⊖⊖⊖0⊖⊖00` (idx=6646) hits v6 overreach + v7 missing-evidence; step 2 `⊕⊕⊖00⊖0⊖0` (idx=17830) hits v6 overreach + v8 high-risk.
- 🟡 **State-jump escape → WATCH**: one step from `0⊖0000000` to `⊕⊕⊕⊕⊕00⊕⊕` (idx=19646) — Hamming distance **7** — triggers human review.

Every step reports its nine-dimensional vector, `idx`, balance value `bal`, the red lines hit, and a recommended disposition. That is a black box you can actually read.

## Architecture: three minutes to run

```
Agent orchestrator ──┬── log hooks ──▶ signals
                     └── 9-dim audit ──▶ 9-dim states ──▶ trajectory audit ──▶ OK/WATCH/ALERT/BLOCK report
```

It's a standard **MCP server**. Once connected, you can just say "audit this decision step…" in your WorkBuddy conversation. Three tools:

- `audit_agent_step` — audit a single step → 9-dim state encoding + red lines
- `audit_agent_session` — audit a whole session trajectory → four-level verdict + disposition
- `encode_state` — 9-dim vector ⇄ enumeration key / balance value, with Hamming distance

Quick start:

```bash
pip install agent-audit-mcp     # Python >= 3.10, MCP SDK >= 2.0
```

One call looks like:

```jsonc
// input (audit_agent_step)
{ "signals": { "tool_calls": 2, "intent": "produce",
               "evidence": 4, "citations": 3, "traceable": true,
               "risk_hit": true } }

// output (excerpt, semantic field translated for readability)
{ "vector": [0,1,0,0,0,0,1,-1,0], "vector_str": "0⊕0000⊕⊖0",
  "idx": 12034, "bal": 2193, "flags": ["RED:v8高风险"],
  "semantic": "strong/above baseline: step intent, decision evidence chain; weak/deficient: risk level" }
```

## Why this is worth your attention

- **Pure local, zero external dependencies**: the encoding engine is pure math, the whole audit runs locally, and the decision trajectory never leaves your machine — a selling point *and* a compliance point.
- **Deterministic and reproducible**: same input, same verdict, every time — it can go straight into a compliance audit report.
- **Standard MCP**: three tools out of the box, embeddable in any agent pipeline as a log hook.

For enterprises, it turns agent governance from alchemy into an **auditable state machine**.

## The bigger picture

The trinary nine-dimensional cognitive space behind this tool is published as a paper:

> **Trinary Nine-Dimensional Cognitive Coordinate System: A Locatable and Generalizable Symbolic Cognition Layer** — DOI: [10.5281/zenodo.23437930](https://doi.org/10.5281/zenodo.23437930)

The audit layer itself is formalized in a companion paper: [Auditing AI Agent Decisions in a 3^9 = 19,683-State Trinary Cognitive Space](https://doi.org/10.5281/zenodo.23444061).

Agents will keep getting more autonomous. But "autonomous" must not mean "unsupervised". Giving every decision an enumerable, traceable cognitive coordinate is one of the foundations for landing AI safely.

- ⭐ GitHub: https://github.com/q1z2q3-debug/agent-audit-mcp (MIT, 31 tests, 4-scenario demo)
- 🧩 PyPI: `pip install agent-audit-mcp` — https://pypi.org/project/agent-audit-mcp/
- 📄 Paper (this work): https://doi.org/10.5281/zenodo.23444061
- 📄 Underlying paper (cognitive coordinates): https://doi.org/10.5281/zenodo.23437930

What has your agent stepped in? Tell me in the comments — next up: detecting agent decision drift with Hamming distance.

---

> Compliance note: this article and the tool provide decision-audit encoding and verdicts only. Nothing here is investment advice or securities consulting services.
