# Style: Reddit threads (distilled from `reddit_exemplars.md` and `reddit_stats.json`)

This guide is for rendering `kind: reddit_thread` artifacts per `briefs/RENDER_BRIEF.md`: an OP post plus a `thread[]` of comments, each with its own `reveals`/`contamination`/`wrong` payload. The goal is a thread that reads as *scraped*, not *written* — noisy, partial, occasionally contradictory, with process facts buried inside human mess rather than presented as a clean answer.

## 1. Post archetypes

**Timeline post.** Dated, bulleted milestones, often started as a promise to "help the next person." *"1) Submitted application 2/23/26 2) Completed and uploaded livescan documents 2/24/26"* (r/CAguns, 1u6xgii). *"08/2024: Filed I-751... 08/2025: Filed N-400 under the 3-yr rule"* (r/USCIS, 1w4z9ji). These end with a totals line ("TOTAL TIME... TOTAL COST") and often a numbered "what I'd tell someone starting out" coda. Longest and most common archetype in solar_permit (median post 258 words; 55% carry timing).

**"How long does X take?" question.** Short, present-tense, sometimes just a title. *"how long should it take to finally receive my license after passing the exam?"* (r/Construction, 143rirw). Usually cites one anecdote heard elsewhere as an anchor before asking.

**Complaint/vent.** No structure, present-tense frustration, day-count as evidence of wrongness. *"it's now been 4 months and I still haven't heard anything"* (r/USCIS, 1vkzqn6). Often escalates mid-post (multiple ❔/😞 emoji, all-caps phrases) rather than staying flat.

**Denial/delay diagnosis request.** OP lists 2-3 candidate causes and asks the sub to pick. *"I am thinking that a combination of these factors led to my denial and I am requesting advice"* (r/CAguns, fmk2dv). Contrast with the vent: this one is trying to solve, not just complain.

**Success report.** Retrospective, hedged relief, usually still lists at least one gripe. *"tl;dr - They are legit... but it took longer than I had hoped for"* (r/solar, spao6t). *"Approved on the spot, given the approval copy"* (r/USCIS, 1wa36gn).

**PSA/guide.** Numbered rules or an FAQ format, addressed to "future posters," written by someone claiming accumulated forum-reading rather than official expertise. *"the 7 Golden Rules of Mobile F&B Survival"* (r/foodtrucks, 1tnt166); an FAQ marked *"[Last Updated 6/9/2020]"* that is now itself stale (r/CAguns, h03tti).

**Wrong-venue / adjacent-program post.** A post that's actually about a sibling program or different jurisdiction, present because subreddits and search terms overlap. *"San Diego General Relief application process questions"* (r/CalFresh, 1i2d3ek) is GR, not CalFresh/SNAP — this is the natural home for `contamination` about a sibling program. Fully off-topic drift also happens (a custody/daycare dispute turns up in the cpra_request bucket, r/sanfrancisco, 1c5qsok) — don't imitate that literally, but know real corpora contain noise, so a thread need not resolve neatly on-topic.

## 2. Comment archetypes

**Me-too with timing.** Anchors to the OP's numbers, then diverges. *"I just received my CCW permit in the mail (Orange County) today... 85 days total and I'm very pleased"* (r/CAguns, 1u6xgii). *"i had one delayed because my weight on 4473 was different than what i had on DL"* (r/CAguns, fmk2dv).

**Advice with steps.** Imperative, numbered or run-on, less polished than a checklist. *"You want to apply. Provide your current income and employment situation"* (r/foodstamps, 1m0tmxh).

**The insider.** Claims a role, never a name or office; hedges on scope, is specific about mechanics, vague about durations. *"I am a former SNAP and TANF Eligibility Supervisor... from LA county, CA"* (r/foodstamps, 1tkxd08). *"I work at the counter so I'll be vague, but..."* is the register even where the exact line isn't in the corpus — insiders self-limit before answering. They hedge on outcomes: *"I could not tell you how long this process will take because they need to examine..."* (1tkxd08).

**Confidently wrong.** States their own single case's number as the universal rule, with no hedge. The CSLB applicant insists *"you patiently wait to be issued your license which takes the issuance unit 2-3 weeks"* (r/Contractor, 1es9xkw) as fact, not experience — and the thread never fully corrects him.

**Stale.** Doesn't always say "before 2024" outright; more often it's a linked FAQ or number that's aged out from under the thread, or a poster noting the number keeps moving: *"Processing times... aren't reliable today. They've climbed month over month for the last 5 months"* (r/USCIS, 1w4z9ji).

**Jurisdiction-drift.** Answers with a neighboring city/county's rule as if it transfers. *"there's an Oakland office, Hayward office & Fremont office"* inside an Alameda County thread (r/foodstamps, 1jix0y5). *"you have to be a Sunnyvale resident though"* corrects an OP who assumed portability (r/CAguns, 1smkq38).

**Off-topic tangent.** Threads wander into unrelated advice or memes and nobody redirects them. *"always invite in the Mormon missionaries and play some nice deep house"* (r/sandiego, 1sgasbb). *"Thanks clanker for this waste of water"* (r/foodtrucks, 1tnt166).

**Moderator/bot.** Fixed boilerplate, italicized signature line, sometimes irrelevant to the actual question. *"It looks like you are posting about an issue in California. For better help, please add what **county** you are in"* (r/foodstamps, 1jix0y5). *"Please remember to change your post flair to `Solved ✔`"* (r/Edd, 1r0mf5v).

## 3. Timing language

Real posters almost never write "the process takes N days" as a flat fact — they anchor to their own dated log (`stats.json`'s medians hide this: posts run 105–258 words, long enough to carry a full date-stamped log) and let the reader compute the delta. Precision correlates with recency and paperwork: exact dates for filings and letters (*"My documents were received on July 18th, 2024"*, r/Contractor, 1es9xkw), rounded ranges for waiting (*"about 2-3 weeks"*, same post), and vague hedges for anything still in flight (*"a few weeks"*, *"a couple months"*). Statutory or published windows get cited as a number to be beaten or missed (*"80% of cases completed in 7 months"*, r/USCIS, 1w4z9ji; the 6-8 week city estimate the fixture ADU thread is written against). Business-vs-calendar distinctions surface only where the poster has been burned by them: *"the 10 day waiting period does not begin until the gun store physically has the gun"* (r/CAguns, h03tti).

Selection bias is visible directly in `reddit_stats.json`: share of **posts** mentioning timing ranges from 0.11–0.12 (cslb_license, cpra_request — dispute- and rant-driven processes) up to 0.41–0.55 (dros_firearm, n400_naturalization, ui_claim, solar_permit — processes with strong "share your timeline to help the next person" norms); calfresh sits at 0.43 despite being a benefits process, driven by denial/appeal posts logging exact dates as evidence. Share of **comments** with timing is far lower everywhere (0.014–0.111) — advice comments describe steps and mechanics, not repeat durations; the timeline dump lives in the post, not the replies. Render accordingly: an OP post should usually carry the spec's timing reveals; comments should mostly carry mechanism, hedges, and corrections, with only the occasional "mine took N days too."

Exaggeration and rounding run in the direction of the poster's mood: vents round up ("10 months later"), success reports round down or add "faster than expected," and diagnosis-request posts give exact day counts as proof something's abnormal (*"61 days since I first submitted"* — the pattern the fixture thread uses).

## 4. Register

Typos and dropped punctuation are constant and untouched — do not clean them up: *"recieved,"* *"amd"* for "and," *"dissapeared,"* *"ot went from"* (r/foodtrucks, 1ua406z). Lowercase sentence starts and run-on paragraphs are common; so are stray line breaks mid-thought. Abbreviations are used without expansion by anyone inside the process — FO (field office), PTO (permission to operate), DROS (Dealer Record of Sale), RFE, GC, SOF (statement of facts), DPSS, EW, SDI, PFL, RESEA, IOE-prefixed case numbers, FSC/HSC, CFARS — and posters mix them with plain English inconsistently in the same post. Emphatic advice runs to bold, caps-lock phrases, and repeated punctuation: *"HUGE ISSUE WITH CSLB APPLICATION and THEIR TECHNICIANS!!!!"* (r/Contractor, 1es9xkw). Edits are appended, not rewritten in: *"Edit: formatting"* (r/solar, spao6t); success is often announced only via an edit tag in the wild, so a renderer using `outcome: approved` can plausibly put the resolution in an "EDIT:" line rather than a clean final paragraph. Profanity is present but not universal, skewing toward frustration posts (*"fuck"*, *"b.s."*) and absent from most procedural/insider comments. Length: hold to the medians in `reddit_stats.json` for the process being rendered — comment medians (18–36 words) are much shorter than most people expect a "reddit comment" to be; most real comments are one or two sentences, not paragraphs.

## 5. Thread dynamics

OP frequently returns to their own post with a dated update rather than editing the body invisibly (*"Update for posterity..."* is the register even when not the exact string). Quoting is done with `>` and is usually partial, snipping a clause to argue with it, not the whole comment. Score is not proportional to correctness: the top-voted comment is usually the most immediately *useful* one — an insider explanation or a concrete correction — not necessarily the most accurate; a hostile or wrong comment can still sit above zero if it's confident and long. Misinformation gets corrected inconsistently: sometimes cleanly and once (*"What you are being sent is what we call the statement of facts (SOF)... I'm guessing the case worker did not input the information"*, r/CalFresh, 1onlkmu), sometimes not at all, and sometimes only partially, leaving the wrong number standing alongside the correction rather than replacing it. Threads routinely end unresolved — OP thanks a commenter and never reports back, or the last comment is a tangent.

## 6. Checklist for renderers

1. Give the OP a dated, first-person log if the spec's `reveals` include multiple timing/step facts — that's where timing belongs, not evenly spread across comments.
2. Match post/comment length to the process's medians in `reddit_stats.json`, not to how much you feel you need to explain.
3. Leave in at least one typo, one dropped-capital sentence start, or one run-on per post — don't polish the prose.
4. Hedge every duration and fee unless the persona is an insider quoting a rule verbatim; round, approximate, or qualify ("about," "I think," "roughly").
5. Give the insider comment (`is_staff_insider`) a self-limiting hedge ("I'll be vague, but...") and specificity about mechanism, not exact timings.
6. Render `wrong` facts as confident, unhedged, first-person assertions — never flagged, never softened.
7. Weave `contamination` in as a tangent or a comparison ("in my county...", a sibling program, a different city) — not as a labeled aside.
8. Let at least one comment drift off-topic or reply to a different comment's clause via `>` quoting rather than to the OP.
9. Don't resolve everything: it's fine (and more realistic) for the thread to end without OP confirming the outcome, or for a wrong fact to stand uncorrected.
10. Never invent a step, fee, or duration beyond what `reveals`/`contamination` license — boilerplate venting, advice tone, and mechanism-flavor are free; process facts are not.

## 7. Five things synthetic posts must not do

1. **Sound like a manual.** No thread should read as a clean, third-person procedural summary — it should read as one person's dated, emotional, first-person account.
2. **List every step in order, completely.** Real posters skip steps that went fine and dwell on the one that didn't; a thread that itemizes the entire process end-to-end with nothing missing is a tell.
3. **Use consistent terminology throughout.** Real posters call the same office, form, or program by two or three different names/abbreviations across one thread, and get some of them slightly wrong.
4. **State exact fees or durations without hedging**, unless the speaker is explicitly an insider quoting a number they handle daily — even then, most real insiders hedge on the outcome even while being exact about mechanism.
5. **Resolve every question raised in the thread.** Real threads leave loose ends: an unanswered follow-up, a correction nobody acknowledges, an OP who never comes back to say what happened.

---

**Report.** Wrote `benchmark/synth/style/reddit_style.md` (~2,250 words) covering seven post archetypes, seven comment archetypes, timing language (with `reddit_stats.json` figures showing post-timing share ranges 0.11–0.55 vs. comment-timing share 0.01–0.11), register, thread dynamics, a 10-bullet renderer checklist, and five negative examples — all evidenced with ≤25-word verbatim quotes cited by subreddit and post id, drawn from `reddit_exemplars.md` (all 8 process buckets) plus a cross-check against the `_fixture` world's rendered `J1__S03__reddit.md`/spec to confirm archetype fit with `RENDER_BRIEF.md`'s `thread[]`/`reveals` mechanics. No other files were modified; nothing was committed.
