# Wave-2 brief: rendering artifacts from specs

You render synthetic documents for a benchmark world. You get: a batch of artifact specs (`benchmark/synth/worlds/<W>/specs/<id>.json`), the world's public-facing facts you are allowed to use (`benchmark/synth/worlds/<W>/render_context/<jur>.json` — jurisdiction names, departments, addresses, hours, statute cites, program names), and the style guides in `benchmark/synth/style/`. You do NOT get the truth files, and you must not open `truth/`.

For each spec write `benchmark/synth/worlds/<W>/artifacts/<id>.md`:
```
---
artifact_id: <id>
url: <spec.url>
kind: <spec.kind>
title: <a title you write>
date: <spec.date>
jur: <spec.jur>
publisher: <spec.publisher>
subreddit: <if reddit_thread>   thread_id: <if reddit_thread>
---
<text>
```
Hard rules:
1. **Every `reveals` entry must appear in the text** at its stated fidelity: `exact` = the value verbatim (a fee "$430", an actor "Building Division", an order "after the inspection…"); `approximate` = a rounded/hedged version ("about $400", "a few weeks"); `vague` = existence without specifics ("the city reviews the application"); `wrong` = state the given wrong value confidently. Do not invent additional process facts (fees, steps, timelines, departments) that are not in `reveals` or `contamination` — generic boilerplate is fine; process facts are not.
2. **Never mention anything about the ids in `must_not_reveal`** — you don't know what they are, and that's the point: do not speculate about internal steps.
3. `contamination` facts must be woven in naturally (a commenter talking about a different city; an FAQ that also covers a sibling program).
4. `stale: true` artifacts describe things as of `date`; do not hint that anything changed.
5. Reddit threads: follow `thread[]` exactly — OP by the persona (their `reported_timeline`, their `why_posting`, their outcome), then each comment with its own `reveals`/`contamination`/`wrong`; write in the register of the real exemplars in `style/reddit_exemplars.md` (typos, digressions, emphatic advice, partial memory, replies quoting each other). Insider comments (`is_staff_insider`) sound like counter staff/inspectors, not like manuals.
6. Municipal pages: mirror `style/municipal_pages.md` (nav breadcrumbs, "Contact", hours, links written as `[text](url)` using ONLY `links_to` urls). Forms: numbered fields, signature blocks, "For office use only" box (with nothing revealing). Ordinances/statutes: sectioned legal prose per `style/legal_text.md`. Staff reports: `style/staff_reports.md` (Recommendation / Background / Discussion / Fiscal Impact).
7. Length within `style.length_words`.
8. Preserve supplied `measurement_clock` metadata in the meaning of timing claims.
   Never invent an acceptance, completeness, first-filing, initial-decision or
   closeout boundary. A median's sample size describes its stated population:
   do not substitute all completed/withdrawn cases for approved-or-denied cases.
   When no clock is supplied, retain that ambiguity instead of supplying a more
   specific-sounding but unsupported definition.
9. Keep a first-visit cycle, a sum of visit cycles, and a first-to-last stage span
   distinct. Cycle time can include waiting; it is not active labor. A sum of
   completed visit cycles can include repeat visits and visits after the reported
   permit decision. Do not turn it into initial packet preparation or an uninterrupted
   request-to-filing span. Preserve whether a number is a forecast, service target,
   completed duration or ongoing lower bound. "Delayed" is a posting-selection
   label, not proof that the decision is still pending.
10. A list of agency names in public context does not assign an activity to one of
    them. Without an explicit activity/actor reveal or licensed public-law relation,
    leave the responsible unit unspecified. Do not fill in plausible departments.
    Only the noisy `reported` phrases are persona timing claims; internal true
    durations are not authorized alternative numbers.
11. Preserve `count_observation` units, populations and observation dates. A retry
    probability per eligible visit at one checkpoint is not the fraction of cases
    with any correction. A planning probability is not an observed sample of ten
    or one hundred. Actual counted numerators/denominators must remain intact.
    Observed corrections among received cases include unfinished cases and may
    include post-decision work; do not relabel that fraction as eventual risk.
When done with the batch, append one line per artifact to `benchmark/synth/worlds/<W>/render_log.jsonl`: {"artifact_id","words","reveals_n","notes"}. Never git commit.
