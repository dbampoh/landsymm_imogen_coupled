# `notes/` — per-step development notes + follow-up tracker

One file per Part V step that records the verification protocol,
any deviations from the plan, and unresolved questions surfaced
during execution. Plus `FOLLOWUPS.md`, which centralises non-blocking
action items that came out of step work but aren't urgent enough to
defer the next step (data uploads, future investigations, etc.).

Per `EXECUTION_PLAN.md` §V.0:

> Per-step documentation. Each step's verification protocol is
> recorded in a `notes/STEP_<n>.md` file in the unified codebase, so
> any reader (or successor) can reproduce the verification.

## Convention

```
notes/
├── README.md                          (this file)
├── FOLLOWUPS.md                       ← central tracker for non-blocking
│                                        action items (open + done, with
│                                        triggers and suggested timing).
├── TRUNK_R13078_BACKPORT_LEDGER.md    ← running source-of-truth catalogue
│                                        of every C++ change in lpjguess/
│                                        that needs replication in
│                                        trunk_r13078 at end of Phase-1
│                                        (per follow-up F-11). Updated on
│                                        every lpjguess/ source-level
│                                        commit — discipline enforced.
├── STEP_0.md                          ← created at step 0; documents how
│                                        this scaffolding was constructed
│                                        and verified.
├── STEP_1.md                          ← created at step 1; documents the
│                                        LPJ-GUESS import + verification.
├── STEP_2.md                          ← Fortran IMOGEN import.
├── ...
├── STEP_19.md                         ← CI/CD setup + verification.
└── STEP_<n>_failure.md                ← if step <n>'s verification fails,
                                         this captures the failure state
                                         per §V.5 recovery protocol.
```

## When to use `FOLLOWUPS.md` vs `STEP_<n>.md` vs `TRUNK_R13078_BACKPORT_LEDGER.md`

- **`STEP_<n>.md`**: everything that happened DURING step `<n>` — the
  exact commands, the verification output, the deviations from plan,
  the new bugs surfaced. One per step, immutable after the step lands.
- **`FOLLOWUPS.md`**: action items that surfaced during a step but
  shouldn't block the next one — data uploads, investigations to do
  later, paper-side TODOs, etc. Items move from OPEN to DONE as they
  close. The `STEP_<n>.md` that triggered each item links to it
  (and vice versa).
- **`TRUNK_R13078_BACKPORT_LEDGER.md`**: running ledger of every C++
  source-level change made in `lpjguess/` (or fork-shared Fortran in
  `imogen/code/`) that needs replication in `trunk_r13078` later, as
  part of the end-of-Phase-1 Backport Sprint (follow-up F-11).
  Updated on every commit that touches `lpjguess/` C++ source.
  Distinct from `FOLLOWUPS.md`: that tracks open *tasks*; the ledger
  tracks the *change log* feeding the eventual backport sprint task.

## What goes in each STEP_<n>.md

- The verification milestone from `EXECUTION_PLAN.md` §V.1 step <n>.
- The exact commands used to perform the import / build / run /
  check.
- The output (head / tail / size / line count) of the verification
  command.
- Any deviations from the planned verification (and why).
- Cross-references to subagent-report sections (`[SAn §x.y]`) when
  the step involves an audit-flagged finding.
- Any new open questions surfaced for follow-up.

## Recovery protocol

If a step's verification fails, capture the failure state in
`notes/STEP_<n>_failure.md` and follow `EXECUTION_PLAN.md` §V.5:

1. Document the failure (expected vs actual, `git diff` vs prior
   verified state).
2. Re-investigate the relevant subagent report in `_phase2_findings/`.
3. Spawn focused investigation if needed.
4. Update `EXECUTION_PLAN.md` with the new finding before retrying.
5. Roll back the working tree to the prior verified commit; retry.
