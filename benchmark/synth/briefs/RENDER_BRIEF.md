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
1a. **Fee-administration boilerplate: policy yes, quantities no.** A fee schedule may carry the general policy notes a real one carries -- non-refundability, state surcharges collected in addition, supersession of a prior schedule, the ordinance controlling on conflict, a cost-recovery basis -- and none of these needs a reveal. What needs a reveal is a QUANTITY attached to a fee: a denominator ("per application", "per unit", "per year", "annually"), a rate or percentage, a proration, or a blanket "unless otherwise noted" that supplies a basis for every row. Payer cost is scored, so a denominator is a burden claim; a policy rule is not. If a `fee` reveal gives a basis for a row, state it on that row only.
1b. **`criterion` reveals** (`ref` = a predicate id such as `P2`) state an eligibility or compliance criterion *as this jurisdiction applies it*: `exact` = the reading verbatim, number included ("a ceiling height of at least 7 feet"); `approximate` = the hedged phrasing supplied; `vague` = name the standard without any number ("the unit must not be substandard"); `wrong` = state the supplied wrong reading confidently. Never state a threshold or standard for a predicate listed in `must_not_reveal_criteria`, and never invent a threshold that no `criterion` reveal licenses: a criterion with no reveal may be mentioned only as "reviewed" with no number. In reddit threads a criterion reveal with `from_case: true` is the poster's own story ("they failed me on ceiling height, said it needs 7 feet").
1c. **"You" is an actor attribution — but only where the step is not the applicant's.** An activity
    reveal with no `actor` field licenses the step's EXISTENCE, not who performs it, and the reveal's
    value is a bare imperative with no subject ("Mail and post the required public notice", "Carry
    out the home occupation compliance inspection", "Submit the application"). So the packet does not
    tell you who acts, and you must not guess a department. What you MAY rely on is the same thing
    `VERIFY_BRIEF` allows: the supplied public-law relationship. The statute puts filing, paying,
    signing, hiring an inspector and opening a portal account on the applicant, so a municipal page
    written in the second person or the imperative — "Create an account, select your program, upload
    what the checklist asks for", "submit the application and pay the fee before review" — is the
    correct register for those steps and needs no actor reveal. That is how real programme pages read
    and you should not passive-ise them.
    The error is second person or an imperative on a step the applicant does NOT perform. "You mail
    and post the required public notice", "the applicant shall mail and post the notice", or a notice
    step folded into a list of things the reader does, all assign agency work to the applicant — and
    four artifacts in one batch failed on exactly that sentence, across an FAQ, an ordinance and two
    programme pages. Issuing notice, reviewing, inspecting, granting, routing, reconciling and
    archiving are the agency's; write them so the sentence says the step happens without saying who
    does it ("the required public notice is mailed and posted"). Two guards on that passive: it must
    not acquire an actor instead ("...by the Department" is the same error the other way), and it must
    not disappear — the reveal still requires the step to appear.
    Where an `actor` IS supplied, name it exactly and put it on that step alone. A department named
    for one step is not thereby licensed for another.
2. **Never mention anything about the ids in `must_not_reveal`** — you don't know what they are, and that's the point: do not speculate about internal steps.
3. `contamination` facts must be woven in naturally (a commenter talking about a different city; an FAQ that also covers a sibling program).
4. `stale: true` artifacts describe things as of `date`; do not hint that anything changed.
5. Reddit threads: follow `thread[]` exactly — OP by the persona (their `reported_timeline`, their `why_posting`, their outcome), then each comment with its own `reveals`/`contamination`/`wrong`; write in the register of the real exemplars in `style/reddit_exemplars.md` (typos, digressions, emphatic advice, partial memory, replies quoting each other). Insider comments (`is_staff_insider`) sound like counter staff/inspectors, not like manuals.
6. Municipal pages: mirror `style/municipal_pages.md` (nav breadcrumbs, "Contact", hours, links written as `[text](url)` using ONLY `links_to` urls). Forms: numbered fields, signature blocks, "For office use only" box (with nothing revealing). Ordinances/statutes: sectioned legal prose per `style/legal_text.md`. Staff reports: `style/staff_reports.md` (Recommendation / Background / Discussion / Fiscal Impact).
7. Length within `style.length_words`.
8. Preserve supplied `measurement_clock` metadata in the meaning of timing claims.
   **A timing reveal belongs to the step it names, and to no other.** Attaching a
   figure to a neighbouring step is not a rounding error: a forecast moved onto the
   decision step reads as a decision shot clock, and one moved onto a status update
   describes work nobody measured. If the reveal names A04, name A04's own activity
   in the sentence that carries the figure. If the artifact's register cannot name a
   step (a council member asking a question, say), name the activity in the words the
   spec uses rather than referring to "one of the steps above" — a vague referent has
   failed here too, because it leaves the figure attached to nothing.
   **A single-visit forecast is not a service commitment and is not additive**: say
   it covers one pass through that step, and never sum such figures into a total.
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
