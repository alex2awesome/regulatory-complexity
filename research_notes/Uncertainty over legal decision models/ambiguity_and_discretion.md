# Ambiguity vs. Discretion: Conceptual Treatments and Empirical Measurement

Scope: (a) jurisprudence of ambiguity / vagueness / open texture / discretion; (b) empirical measurement of textual ambiguity and clarity (surveys, corpora, embeddings, LLMs); (c) measuring discretion as heterogeneity across adjudicators; (d) work that separates the two or models both. Compiled 2026-10-05.

Verification tags used below:
- **[V-full]**: I read the primary text this session (full text or the relevant pages).
- **[V-pub]**: confirmed on a publisher, repository or court page (abstract or landing page).
- **[V-xref]**: bibliographic metadata (authors, venue, volume, pages, year, DOI) confirmed in the Crossref registry by a scripted query.
- **[S]**: the claim comes only from a secondary or aggregator page.
- **[U]**: the substantive content is not verified this session.

Process note: the session's shared web-search budget ran out partway through. Later checks were made with Crossref API queries, direct fetches of known URLs and reading of downloaded PDFs. One source, the Dworkin PDF, sits behind a Cloudflare bot check. Per project rules I did not try to get around it.

---

## Q1. Jurisprudence: how do ambiguity, vagueness, open texture and discretion differ (Hart, Dworkin, Solan, Endicott, Waldron, Farnsworth et al., Kavanaugh, Chevron/Loper Bright)?

### Takeaway
The legal-theory literature mostly supports the working distinction. An ambiguity is uncertainty about which rule the text states; a discretion is a rule that delegates a choice. Doctrine now draws this exact line: Loper Bright (2024) holds that "an ambiguity is simply not a delegation." There are two important qualifications. First, for Hart and for Endicott, vagueness or open texture leaves borderline cases undetermined, and in those cases the adjudicator has discretion in practice. So irreducible vagueness turns into discretion. Second, evaluative standards such as "reasonable" and "appropriate" are both vague and delegating. Loper Bright itself treats such words as delegations.

### Cited Findings

**Hart: open texture, the penumbra, and discretion**
- Hart's 1958 Holmes Lecture, "Positivism and the Separation of Law and Morals," 71 Harv. L. Rev. 593 (1958), is the source of the core/penumbra ("vehicle in the park") argument [V-xref] — [Crossref DOI 10.2307/1338225](https://doi.org/10.2307/1338225). [U] on content: I did not re-read the text this session. The open-texture argument is also developed in *The Concept of Law* (1961), ch. VII. I could not fetch that text.
- Fischman, in a primary text I read, characterizes Hart's view this way: positivists "such as Hart (1961) ... agree that legal rules are occasionally indeterminate, but assert that the law is clear and binding in most cases." He contrasts it with interpretivists "such as Dworkin (1986)," who hold "that law is always determinate, although it does not always constrain judicial decision making in practice" [V-full] — [Fischman, NBER conference draft, p. 1](https://conference.nber.org/conf_papers/f66640/f66640.pdf).
- Hart's lost 1956 Harvard essay "Discretion" was published in 2013 with an introduction by Nicola Lacey, "The Path Not Taken," 127 Harv. L. Rev. 636. On the Harvard Law Review's account, Hart treats discretion as "a special mode of reasoned, constrained decisionmaking that occupies a middle ground between arbitrary choice and determinate rule application." For Hart, discretion soundly exercised is "a principled way of coping with legal indeterminacy" that is consistent with the rule of law [V-pub] — [Harvard Law Review, 127 Harv. L. Rev. 636](https://harvardlawreview.org/print/vol-127/the-path-not-taken-h-l-a-harts-harvard-essay-on-discretion/); [LSE eprint](https://researchonline.lse.ac.uk/id/eprint/55299). A companion essay by Geoffrey Shaw, "H.L.A. Hart's Lost Essay: Discretion and the Legal Process School," appears in the same issue [S: the title is from PhilArchive; I am inferring that it is the HLR "Legal Theory Essay, 127 Harv. L. Rev. 666" listing] — [PhilArchive](https://philarchive.org/rec/SHAHHL); [HLR listing](https://harvardlawreview.org/?p=2110). The page on which Hart's essay itself starts is [U].

**Dworkin: weak vs. strong discretion**
- Ronald M. Dworkin, "The Model of Rules," 35 U. Chi. L. Rev. 14 (1967) [V-xref, V-pub] — [Chicago Unbound](https://chicagounbound.uchicago.edu/uclrev/vol35/iss1/3/); [DOI 10.2307/1598947](https://doi.org/10.2307/1598947). It was Dworkin's first sustained attack on the positivist claim that judges exercise discretion "when the rules ran out" [V-pub] — [NUS CLT event page](https://law.nus.edu.sg/?p=1179).
- [U: the full text is behind a bot check, so this content was not re-read this session.] As the article is standardly read, Dworkin separates two "weak" senses of discretion from a "strong" one. In the first weak sense, standards cannot be applied mechanically and require judgment. In the second, an official's decision is final and cannot be reviewed. In the strong sense, the official "is simply not bound by standards set by the authority in question." His example is a sergeant told to "pick any five men" (strong) versus "pick the five most experienced men" (weak). On this reading, the working notion of discretion as an explicit delegation of choice is close to Dworkin's strong sense. Vague evaluative standards fall under weak discretion.

**Waldron: ambiguity vs. vagueness vs. contestability**
- Jeremy Waldron, "Vagueness in Law and Language: Some Philosophical Issues," 82 Cal. L. Rev. 509 (1994) [V-xref] — [DOI 10.2307/3480971](https://doi.org/10.2307/3480971); [Berkeley LawCat record](https://lawcat.berkeley.edu/record/1114946). The abstract describes "a philosophical account of the various problems with meaning that lawyers associate with the 'void-for-vagueness' doctrine" [V-pub] — [Stafforini abstract page](https://stafforini.com/works/waldron-1994-vagueness-law-language/).
- Waldron distinguishes ambiguity, contestability and vagueness, and uses "indeterminacy" as the general term covering all three [S: from a search-result summary; the full text returned HTTP 403] — [LawCat](https://lawcat.berkeley.edu/record/1114946).
- Related: Waldron, "Vagueness and the Guidance of Action," in *Philosophical Foundations of Language in the Law* (OUP 2011), pp. 58–82 [V-xref] — [DOI 10.1093/acprof:oso/9780199572380.003.0004](https://doi.org/10.1093/acprof:oso/9780199572380.003.0004).

**Endicott: vagueness**
- Timothy Endicott, *Vagueness in Law* (OUP 2000). It argues that vagueness belongs to law itself, not only to legal language. Because law is vague, "judges cannot always decide cases by giving effect to the legal rights and obligations of the parties, cannot always treat like cases alike." The book then re-articulates the rule of law so that it does not require determinacy, and treats "resolution of unresolved disputes" as an independent judicial duty [V-pub] — [PhilPapers](https://api.philpapers.org/rec/ENDVIT); [OUP chapter](https://academic.oup.com/book/10826/chapter/158987929).
- Endicott, "Law Is Necessarily Vague," 7 Legal Theory 379–385 (2001) [V-xref] — [DOI](https://doi.org/10.1017/s135232520170403x). Also "Vagueness and Legal Theory," 3 Legal Theory 37–63 (1997) [V-xref] — [DOI](https://doi.org/10.1017/s135232520000063x).
- Further conceptual pieces, citations confirmed but content [U]:
  - Ralf Poscher, "Ambiguity and Vagueness in Legal Interpretation," *Oxford Handbook of Language and Law* 128–145 (2012) — [DOI](https://doi.org/10.1093/oxfordhb/9780199572120.013.0010).
  - Andrei Marmor, "Varieties of Vagueness in the Law," in *The Language of Law* 85–106 (OUP 2014) — [DOI](https://doi.org/10.1093/acprof:oso/9780198714538.003.0004).
  - Marmor, "Pragmatic Vagueness in Statutory Law," in *Vagueness and Law* (OUP 2016) — [DOI](https://doi.org/10.1093/acprof:oso/9780198782889.003.0007).

**Solan: "pernicious ambiguity"**
- Lawrence M. Solan, "Pernicious Ambiguity in Contracts and Statutes," 79 Chi.-Kent L. Rev. 859 (2004). Pernicious ambiguity is "an interpretive problem where various actors involved in a dispute all believe a text to be clear, but assign different meanings to it" [V-pub] — [Chicago-Kent repository](https://scholarship.kentlaw.iit.edu/cklawreview/vol79/iss3/22). The page cite is confirmed by its citation in Arbel & Hoffman, 99 N.Y.U. L. Rev. at 465 n.65 [V-full] — [NYU L. Rev. PDF](https://nyulawreview.org/wp-content/uploads/2024/05/99-NYU-L-Rev-451-1.pdf).
- Arbel & Hoffman quote a contracts authority on the vague/ambiguous line: "Courts seldom distinguish between 'vague' and 'ambiguous' terms ... a word is vague to the extent that it can apply to a wide spectrum of referents, or to referents that cluster around a modal 'best instance,' or to somewhat different referents in different people" [V-full] — [99 N.Y.U. L. Rev. 451, n.~67–68](https://nyulawreview.org/wp-content/uploads/2024/05/99-NYU-L-Rev-451-1.pdf).

**Farnsworth, Guzior & Malani: internal vs. external ambiguity**
- Ward Farnsworth, Dustin F. Guzior & Anup Malani, "Ambiguity About Ambiguity: An Empirical Inquiry into Legal Interpretation," 2 J. Legal Analysis 257–300 (2010) [V-xref] — [DOI 10.1093/jla/2.1.257](https://doi.org/10.1093/jla/2.1.257).
  - The paper asks "what ambiguity in law *is*." It separates **internal** ambiguity (the judge is personally uncertain) from **external** ambiguity (ordinary English readers, as a group, would disagree about the meaning). In a survey of roughly 1,000 law students, asking whether a statute was ambiguous to the respondent produced answers "strongly biased by their policy preferences." Asking whether others would agree about the meaning did not [V-pub] — [OUP JLA](https://academic.oup.com/jla/article-lookup/doi/10.1093/jla/2.1.257).
- Follow-up: Farnsworth, Guzior & Malani, "Policy Preferences and Legal Interpretation," 1 J. L. & Courts 115–138 (2013) [V-xref] — [DOI](https://doi.org/10.1086/668603). Also "Implicit Bias in Legal Interpretation," SSRN (2011) [V-xref] — [DOI](https://doi.org/10.2139/ssrn.1944273).

**Kavanaugh's critique of ambiguity thresholds**
- Brett M. Kavanaugh, "Fixing Statutory Interpretation," 129 Harv. L. Rev. 2118 (2016) (reviewing Katzmann) [V-full]:
  - "judges often cannot make that initial clarity versus ambiguity decision in a settled, principled, or evenhanded way."
  - At 2137–38: "If the statute is 60-40 in one direction, is that enough to call it clear? How about 80-20? Who knows?" Also: "I probably apply something approaching a 65-35 rule ... a few of my colleagues apply more of a 90-10 rule ... other colleagues ... appear to apply a 55-45 rule." And: "One judge's clarity is another judge's ambiguity."
  - He cites Farnsworth et al. at 276 for the point that there is "no way to falsify a judge's claim one way or the other."
  - His remedy is that courts "should seek the *best reading* of the statute."
  - Source: [HLR PDF](https://harvardlawreview.org/wp-content/uploads/2016/06/2118-2163-Online.pdf).
- Richard M. Re, "Clarity Doctrines," 86 U. Chi. L. Rev. 1497–1562 (2019). Re argues that the meaning of clarity should depend on each doctrine's purpose. The reasons for caring about clarity involve either "the deciding court's certainty about the right answer or the predictability that other interpreters would converge on a given answer." He applies this to habeas, Chevron, qualified immunity, avoidance and lenity [V-pub] — [Chicago Unbound](https://chicagounbound.uchicago.edu/uclrev/vol86/iss6/5); [U. Chi. L. Rev.](https://lawreview.uchicago.edu/publication/clarity-doctrines).

**Chevron and Loper Bright: does ambiguity equal delegated discretion?**
- *Loper Bright Enterprises v. Raimondo*, 603 U.S. ___ (2024), slip opinion. The U.S. Reports page (369) is [U]. All of the following are [V-full] — [Supreme Court slip opinion](https://www.supremecourt.gov/opinions/23pdf/22-451_7m58.pdf):
  - **Majority, slip op. 17–18.** "the statute's meaning may well be that the agency is authorized to exercise a degree of discretion." Some statutes "'expressly delegate[ ]' to an agency the authority to give meaning to a particular statutory term." Others empower an agency "to 'fill up the details' of a statutory scheme," or to regulate subject to "a term or phrase that 'leaves agencies with flexibility' ... such as 'appropriate' or 'reasonable.'"
  - Footnotes 5–6 give lexical examples:
    - "as such terms are defined and delimited by regulations of the Secretary" (29 U.S.C. §213(a)(15));
    - "as defined by regulations which the Commission shall promulgate";
    - "in the judgment of the [EPA] Administrator";
    - "if the Administrator finds such regulation is appropriate and necessary."
  - **Majority, slip op. 22.** Quoting Sunstein (1989): "[a]n ambiguity is simply not a delegation of law-interpreting power. Chevron confuses the two." Also: "many or perhaps most statutory ambiguities may be unintentional"; "the ambiguity is not a delegation to anybody"; statutes "do—in fact, must—have a single, best meaning."
  - **Majority, on workability.** "the concept of ambiguity has always evaded meaningful definition ... '"[A]mbiguity" is a term that may have different meanings for different judges' ... One judge might see ambiguity everywhere; another might never encounter it." Also: "statutory ambiguity ... is not a reliable indicator of actual delegation of discretionary authority to agencies."
  - **Kagan dissent, slip op. 2–3.** "Congress knows that it does not—in fact cannot—write perfectly complete regulatory statutes. It knows that those statutes will inevitably contain ambiguities that some other actor will have to resolve, and gaps that some other actor will have to fill." On this view deference rests on "an implicit congressional delegation of interpretive authority." Later she warns that attending to every express delegation using "flexib[le]" words like "appropriate" or "reasonable" "involves complexities of its own." She cites Gluck & Bressman, 65 Stan. L. Rev. 901, 928 (fig. 2), 994 (2013), for the point that drafters "knew all about Chevron."
- Background cited inside Loper Bright [V-xref]:
  - Cass Sunstein, "Interpreting Statutes in the Regulatory State," 103 Harv. L. Rev. 405, 445 (1989) — [DOI](https://doi.org/10.2307/1341272).
  - Antonin Scalia, "Judicial Deference to Administrative Interpretations of Law," 1989 Duke L.J. 511 ("How clear is clear?") — [DOI](https://doi.org/10.2307/1372576).
- Lawrence B. Solum & Cass R. Sunstein, "Chevron as Construction," 105 Cornell L. Rev. 1465 (2020). They separate **interpretation** (finding the meaning of a term) from **construction** (developing implementing principles, or specifying a term the meaning leaves open). Their conclusion is that those who reject Chevron for interpretation should still accept it for construction [V-pub] — [Cornell L. Rev.](https://scholarship.law.cornell.edu/clr/vol105/iss5/5).
- Lawrence B. Solum, "The Interpretation-Construction Distinction," 27 Const. Comment. 95 (2010) [V-xref] — [DOI](https://doi.org/10.24926/26390742.1829). [U] on content: this is the source of the "construction zone" for underdeterminate text.
- Abbe R. Gluck, "The End of Ambiguity (in Statutory Interpretation)," SSRN (2026) [V-xref; abstract not retrieved, HTTP 403] — [DOI 10.2139/ssrn.6304281](https://doi.org/10.2139/ssrn.6304281). Also Gluck, "Overruling Chevron Without a Coherent Theory of Statutory Interpretation..." SSRN (2024) [V-xref] — [DOI](https://doi.org/10.2139/ssrn.5024685).
- Louis Kaplow, "Rules Versus Standards: An Economic Analysis," 42 Duke L.J. 557 (1992). Standards "will be given content only after individuals act." Rules are costlier to make; standards are costlier for individuals to interpret and for adjudicators to apply [V-pub, V-xref] — [Duke repository](https://scholarship.law.duke.edu/dlj/vol42/iss3/2); [DOI](https://doi.org/10.2307/1372840).

### Inferences
- **Support for the working answer.**
  - The Loper Bright majority, and Sunstein (1989) whom it quotes, draw the same line Isabel's question needs. Ambiguity means the text has one best meaning that is hard to find, and the court must find it. Discretion means the best reading of the text is that it delegates a choice ("appropriate," "reasonable," "as defined by regulations," "in the judgment of"), and the reviewer only polices the boundaries.
  - Dworkin's strong sense ("pick any five") matches "the rule explicitly delegates."
- **Refinement 1: external ambiguity is itself heterogeneity.** Farnsworth et al.'s "external ambiguity" is defined as expected *disagreement among readers*. Solan's "pernicious ambiguity" is confident, divergent readings. In both cases ambiguity shows up as heterogeneity across adjudicators, not as shared uncertainty. So "shared uncertainty vs. heterogeneity" is not a clean behavioral marker. Ambiguity can produce adjudicator-specific readings, each held with confidence.
- **Refinement 2: irreducible vagueness yields discretion.** For Hart and Endicott, the borderline cases of vague terms have no legally determined answer, and adjudicators must decide them. That is discretion in Dworkin's weak sense. On this view, the "reducible by better readings" clause holds for true ambiguity (a choice among discrete senses). It does not hold for vagueness, where more reading cannot resolve borderline cases. Choi's information/determinacy split (Q2) says the same thing in empirical language.
- **Refinement 3: evaluative standards sit in the overlap.** Words like "reasonable" and "appropriate" are vague (Endicott, Waldron) and also delegations (Loper Bright n.6; Kaplow's standards). For modeling, these should probably be coded as **delegation** rather than ambiguity. That is the conservative default, and it matches current doctrine.
- **Refinement 4: whether ambiguity counts as a delegation is itself a legal rule.** Kagan's dissent treats ambiguity as an implied delegation; the majority rejects that. The mapping from "uncertain text" to "permitted adjudicator choice" has changed over time: Chevron (1984–2024), then Loper Bright.
- **Meta-level heterogeneity in thresholds.** Kavanaugh's 55-45 / 65-35 / 90-10 thresholds show that even where the posterior over readings is shared, judges differ on whether to *call* it ambiguous. Ambiguity-triggered doctrines (lenity, Chevron step two, legislative history) can therefore turn shared uncertainty into between-judge heterogeneity.

### Gaps
- I did not read primary text this session for Hart (1958; *Concept of Law*), Dworkin (1967; Cloudflare challenge), Waldron (1994; HTTP 403), Poscher, Marmor, or Solum (2010). The content descriptions for these are flagged [U] or [S].
- Not located because the search budget ran out:
  - Endicott, "The Value of Vagueness" (in Marmor & Soames eds., 2011). Crossref returned other Endicott chapters but not this one.
  - Greenawalt, "Discretion and Judicial Decision" (Colum. L. Rev. 1975).
  - Barak, *Judicial Discretion* (1989).
  - Lacey, "The Jurisprudence of Discretion" (in *The Uses of Discretion*, 1993). Crossref shows this chapter exists — [DOI](https://doi.org/10.1093/oso/9780198257622.003.00011) — but I did not read it.
- Gluck & Bressman (2013): the citation is verified through its quotation in the Kagan dissent. I did not read the findings on how drafters understand ambiguity as delegation.

---

## Q2. Empirical measurement of textual ambiguity and clarity (surveys, corpus linguistics, embeddings, LLMs)

### Takeaway
There are four families of methods:
1. Surveys of readers: Farnsworth et al.; Tobia; Ben-Shahar & Strahilevitz; Tobia, Slocum & Nourse.
2. Corpus linguistics: Lee & Mouritsen.
3. Embedding or semantic-similarity measures: Choi (2024); Arbel & Hoffman.
4. Repeated-sampling LLM output distributions: Arbel & Hoffman; Engel & McAdams.

A run of 2025–26 papers finds that LLM-based ambiguity estimates are unstable across prompts and models. Choi (2025) reports a cross-model correlation of r = 0.051. Waldon et al., Purushothama et al. and Sobel, Grimmelmann & Stein reach similar conclusions. Measured "ambiguity" can therefore partly reflect heterogeneity in the instrument rather than the text.

### Cited Findings

**Survey-based measures**
- Farnsworth, Guzior & Malani (2010) surveyed about 1,000 law students. Self-reported ambiguity is contaminated by policy preference; predicted agreement among other readers is not. This is a framing-based elicitation that separates the two ambiguity concepts [V-pub] — [OUP JLA](https://academic.oup.com/jla/article-lookup/doi/10.1093/jla/2.1.257).
- Kevin P. Tobia, "Testing Ordinary Meaning," 134 Harv. L. Rev. 726 (2020). Experiments with ordinary people, law students, and U.S. judges [V-pub] — [HLR page](https://harvardlawreview.org/2020/12/testing-ordinary-meaning/); [PDF](https://harvardlawreview.org/wp-content/uploads/2020/11/134-Harv.-L.-Rev.-726.pdf):
  - Dictionary definitions and corpus-linguistics data "diverged from ordinary meaning — at a conservative divergence rate between 20–35%."
  - For harder categorizations, relying on them "led 80–100% of users to the incorrect verdict."
  - Dictionaries push toward extensive judgments (roller skates count as vehicles). Corpus linguistics pushes toward narrow, prototypical ones (a car is a vehicle). Tobia calls this the "Nonappearance Fallacy."
  - "Judges, law students, and ordinary people were strikingly similar in their ordinary conceptual judgments."
- Kevin Tobia, Brian Slocum & Victoria Nourse:
  - "Statutory Interpretation from the Outside," SSRN (2021) [V-xref] — [DOI](https://doi.org/10.2139/ssrn.3786090).
  - "Ordinary Meaning and Ordinary People," SSRN (2022) [V-xref] — [DOI](https://doi.org/10.2139/ssrn.4034992).
  - The published venues (Colum. L. Rev. 2022; U. Pa. L. Rev. 2023) are [U].
- Tobia, Egbert & Lee, "Triangulating Ordinary Meaning," SSRN (2023) [V-xref] — [DOI](https://doi.org/10.2139/ssrn.4441512). Tobia, "New Methods in Statutory Interpretation: Surveys, Corpus Linguistics, ChatGPT," SSRN (2024) [V-xref] — [DOI](https://doi.org/10.2139/ssrn.4932610).
- Omri Ben-Shahar & Lior Strahilevitz, "Interpreting Contracts via Surveys and Experiments," SSRN (2017) [V-xref; content and published venue U] — [DOI](https://doi.org/10.2139/ssrn.2905873).

**Corpus linguistics**
- Thomas R. Lee & Stephen C. Mouritsen, "Judging Ordinary Meaning," 127 Yale L.J. 788 (2018). It frames ordinary meaning as an empirical question about "the sense of a word or phrase most likely implicated in a given linguistic context," to be answered with corpus tools [V-pub] — [Yale L.J.](https://yalelawjournal.org/article/judging-ordinary-meaning). Page 788 is confirmed by Arbel & Hoffman n.68 [V-full].
- Lee & Mouritsen, "The Corpus and the Critics," SSRN (2020) [V-xref] — [DOI](https://doi.org/10.2139/ssrn.3727504). Egbert & Lee, "Prototype-by-component analysis," 4 Applied Corpus Linguistics 100078 (2024) [V-xref] — [DOI](https://doi.org/10.1016/j.acorp.2023.100078).

**Embedding and semantic-similarity measures**
- Jonathan H. Choi, "Measuring Clarity in Legal Text," 91 U. Chi. L. Rev. 1 (2024) [V-pub] — [Chicago Unbound](https://chicagounbound.uchicago.edu/uclrev/vol91/iss1/1/); SSRN [DOI](https://doi.org/10.2139/ssrn.4151849):
  - It offers a theory of clarity that "distinguishes between information and determinacy." Unclarity can come from an information deficit (reducible) or from fundamental indeterminacy (not reducible).
  - It measures clarity with NLP semantic-similarity techniques.
  - Findings: "text is frequently indeterminate in real-world legal cases," and "estimates of similarity vary substantially from corpus to corpus, even for large and reputable corpora."
- Yonathan A. Arbel & David A. Hoffman, "Generative Interpretation," 99 N.Y.U. L. Rev. 451 (2024). LLMs can "ascertain ordinary meaning in context, quantify ambiguity, and fill gaps" [V-full] — [NYU L. Rev. PDF](https://nyulawreview.org/wp-content/uploads/2024/05/99-NYU-L-Rev-451-1.pdf). Concrete techniques:
  - **Embedding distance (pp. ~456–57, nn.22–24).** Cosine distance between a candidate term and an insurance exclusion clause, averaged over the "ten top performing [embedding] models." They found that "while results using this method seem sensible, they are also fragile." They also warn that "What gets measured is word 'relatedness,'" not meaning.
  - **Token probabilities (pp. 484–85).** A worked illustration, with the caveat that "the probabilities shouldn't be interpreted literally" (n.165).
  - **Repeated sampling as an ambiguity distribution (pp. 486–89, *Trident*).** GPT-4, Claude 2 and Llama-2-70b were run at temperature 1 and asked to score from 0 to 100 whether the note is "reasonably susceptible" to an early-repayment reading. The mean was about 41. "the probability distribution suggests that at least some probabilistic readings of the contract permit early repayment."
  - Code: [GitHub](https://github.com/yonathanarbel/generativeinterpretation/tree/main), cited at n.22.

**LLMs for ordinary meaning, and critiques**
- Christoph Engel & Richard H. McAdams, "Asking GPT for the Ordinary Meaning of Statutory Terms," 2024 U. Ill. J.L. Tech. & Pol'y [V-pub] — [UChicago Law](https://www.law.uchicago.edu/node/112326); [Chicago Unbound](https://chicagounbound.uchicago.edu/journal_articles/10562); SSRN [DOI](https://doi.org/10.2139/ssrn.4718347):
  - The most useful evidence is "a distribution of replies," so they used GPT-3.5 Turbo and ran "each prompt 100 times."
  - Benchmark: a survey of more than 2,800 English speakers on whether "vehicle" includes listed objects.
  - The best design was a belief prompt with a Likert reply. They also tested legal-purpose context, 1950s meaning, and extension vs. intension.
- Jonathan H. Choi, "Large Language Models Are Unreliable Judges," SSRN (2025) [V-xref] — [DOI 10.2139/ssrn.5188865](https://doi.org/10.2139/ssrn.5188865):
  - "extreme sensitivity to minor variations in prompt phrasing, giving opposite responses to semantically equivalent questions."
  - "virtually no correlation (r = 0.051) between the judgments of different LLMs on identical interpretive questions."
  - Post-training "can cause LLM assessments to substantially deviate from ... predictions of language use in their corpora" [V-pub] — [HKU LawTech event page](https://www.lawtech.hku.hk/?p=648).
  - The "Off-the-Shelf ..." title variant in the brief is [U]. Crossref and HKU list the title above.
- Brandon Waldon, Nathan Schneider, Ethan Wilcox, Amir Zeldes & Kevin Tobia, "Large Language Models for Legal Interpretation? Don't Take Their Word for It," 114 Geo. L.J. (Issue 1, Nov. 2025). The authors argue that practitioners "run the risk of inappropriately relying on LLMs" for interpretive questions. They note that in 2024 a U.S. judge queried LLM chatbots on an insurance contract and on the Sentencing Guidelines [V-pub] — [Georgetown L.J.](https://www.law.georgetown.edu/georgetown-law-journal/in-print/volume-114/volume-114-issue-1-november-2025/large-language-models-for-legal-interpretation-dont-take-their-word-for-it/); SSRN [DOI](https://doi.org/10.2139/ssrn.5123124).
- Abhishek Purushothama, Junghyun Min, Brandon Waldon & Nathan Schneider:
  - "Prompting from the bench: Large-scale pretraining is not sufficient to prepare LLMs for ordinary meaning analysis," arXiv 2510.25356 (Oct. 2025; revised May 2026). "Slight changes to the format of a question can lead to wildly different conclusions." Agreement with human judgments is moderate at best [V-pub] — [arXiv](https://arxiv.org/abs/2510.25356).
  - Companion paper: "Not ready for the bench: LLM legal interpretation is unstable and uncalibrated to human judgments," NLLP Workshop 2025 [V-xref] — [DOI](https://doi.org/10.18653/v1/2025.nllp-1.22).
- Benjamin L.W. Sobel, James Grimmelmann & David Stein, "Generative Misinterpretation," 63 Harv. J. on Legis. 229–308 (2026). Experimental results using LLMs for interpretation are "brittle and arbitrary." The paper adds a jurisprudential critique of the justifications offered for LLM use [V-pub] — [HJL](https://journals.law.harvard.edu/jol/2026/01/24/generative-misinterpretation); [PDF](https://journals.law.harvard.edu/jol/wp-content/uploads/sites/86/2026/01/06-HLL-63-1_Stein-et.-al.229-308_.pdf).

### Inferences
- Most measurement methods quantify ambiguity as **dispersion**:
  - across survey respondents (external ambiguity);
  - across embedding models or corpora (Choi; Arbel & Hoffman);
  - across repeated samples (Engel & McAdams; Arbel & Hoffman).
  None directly measures the *shared* posterior uncertainty in the working definition. Respondent dispersion mixes true textual ambiguity with reader heterogeneity, which is the same confound Isabel raised.
- Choi's r = 0.051 cross-model correlation is a direct warning. If the instrument (the model) has its own "adjudicator effect," then dispersion across models is model heterogeneity, not text ambiguity. Any LLM ambiguity score should be built as within-model sampling dispersion, with a separate between-model variance component, rather than pooled.
- The Farnsworth et al. design (own uncertainty vs. predicted agreement of others) can be adapted to Gemma or LLM elicitation. Ask both "how confident are you" and "what share of readers would agree." That separates the internal and external concepts in a cheap, offline way.

### Gaps
- Not verified this session (search budget exhausted):
  - Judge Newsom's concurrences in *Snell v. United Specialty Ins. Co.* (11th Cir. 2024) and *United States v. Deleon* (11th Cir. 2024). They are referenced only indirectly, through Waldon et al.
  - Solan, Rosenblatt & Osherson, "False Consensus Bias in Contract Interpretation," Colum. L. Rev. (2008). Crossref did not return it.
  - Exact sample sizes in Tobia (2020).
- I found no paper that validates an LLM ambiguity score against a ground-truth split of ambiguity vs. reader heterogeneity.

---

## Q3. Measuring discretion as adjudicator heterogeneity (leniency designs, variance components, Ho's inspector and mass-adjudication work)

### Takeaway
Discretion is measured empirically as the between-adjudicator component of outcome variance when cases are (quasi-)randomly assigned. There are three main forms:
- dispersion of a judge random effect (Anderson, Kling & Stith 1999);
- judge or examiner "leniency" used as an instrument (Kling 2006; Dobbie, Goldin & Yang 2018; Sampat & Williams 2019; Maestas, Mullen & Strand 2013);
- pairwise-disagreement rates (Fischman 2014; Ho 2017).

Three lines of work show that measured heterogeneity is not pure "preference." Chan, Gentzkow & Yu separate skill from preference. Frakes & Wasserman show that examiner time constraints shift grant rates. Abrams et al. test variance in treatment against a random-assignment null.

### Cited Findings

**Random-effect dispersion and rule changes**
- James M. Anderson, Jeffrey R. Kling & Kate Stith, "Measuring Interjudge Sentencing Disparity: Before and After the Federal Sentencing Guidelines," 42 J.L. & Econ. 271 (1999) [V-xref; DOI 10.1086/467426] — [journal](https://www.journals.uchicago.edu/doi/10.1086/467426); [Chicago Unbound](https://chicagounbound.uchicago.edu/jle/vol42/iss2/3).
  - Disparity is "measured as the dispersion of a random effect in a zero-inflated negative binomial model."
  - The expected difference between two typical judges was about 17% (4.9 months) in 1986–87, before the Guidelines. It fell to about 11% (3.9 months) in 1988–93 [S: numbers from the RePEc abstract via search; Chicago Unbound has no full text] — [IDEAS/RePEc](https://ideas.repec.org/a/ucp/jlawec/v42y1999i1p271-307.html).
  - Crossref gives pp. 271–308; RePEc gives 271–307.
- Crystal S. Yang, "Have Inter-Judge Sentencing Disparities Increased in an Advisory Guidelines Regime? Evidence from Booker," SSRN (2013) [V-xref; published version U] — [DOI](https://doi.org/10.2139/ssrn.2348140).
- Yang, "Free at Last? Judicial Discretion and Racial Disparities in Federal Sentencing," 44 J. Legal Stud. 75–111 (2015) [V-xref] — [DOI](https://doi.org/10.1086/680989).
- Fischman reports that the SSA justified its vocational grid "on the ground that it would reduce inconsistency among adjudicators (43 Fed. Reg. 55,349 [1978])." He also notes that the federal sentencing guidelines were motivated by studies of inter-judge disparity [V-full] — [Fischman draft, p. 3](https://conference.nber.org/conf_papers/f66640/f66640.pdf).

**Leniency or tendency instruments**
- Jeffrey R. Kling, "Incarceration Length, Employment, and Earnings," 96 AER 863–876 (2006). Instruments incarceration length using "randomly assigned judges with different sentencing propensities" [V-xref, V-pub] — [DOI](https://doi.org/10.1257/aer.96.3.863); [NBER w12003](https://www.nber.org/papers/w12003).
- Will Dobbie, Jacob Goldin & Crystal S. Yang, "The Effects of Pretrial Detention on Conviction, Future Crime, and Employment: Evidence from Randomly Assigned Judges," 108 AER 201–240 (2018). Uses "the detention tendencies of quasi-randomly assigned bail judges" [V-xref, V-pub] — [DOI](https://doi.org/10.1257/aer.20161503); [Stanford Law page](https://law.stanford.edu/publications/the-effects-of-pretrial-detention-on-conviction-future-crime-and-employment-evidence-from-randomly-assigned-judges/).
- Bhaven Sampat & Heidi L. Williams, "How Do Patents Affect Follow-On Innovation? Evidence from the Human Genome," 109 AER 203–236 (2019). Uses the "leniency" of the assigned patent examiner as an instrument for grant [V-xref, V-pub] — [AEA](https://www.aeaweb.org/doi/10.1257/aer.20151398).
- Michael D. Frakes & Melissa F. Wasserman, "Is the Time Allocated to Review Patent Applications Inducing Examiners to Grant Invalid Patents? Evidence from Microlevel Application Data," 99 REStat 550–563 (2017) [V-xref, V-pub] — [DOI](https://doi.org/10.1162/rest_a_00605); [RePEc](https://ideas.repec.org/a/tpr/restat/v99y2017i3p550-563.html).
  - A GS-11 to GS-12 promotion cuts allocated review hours by about 10–15%.
  - Promotions bring "reductions in examination scrutiny and increases in granting tendencies," and the marginal patents are of below-average quality.
- Mark A. Lemley & Bhaven Sampat, "Examiner Characteristics and Patent Office Outcomes," 94 REStat 817–827 (2012) [V-xref] — [DOI](https://doi.org/10.1162/rest_a_00194). Iain Cockburn, Samuel Kortum & Scott Stern, "Are All Patent Examiners Equal?" NBER w8980 (2002) [V-xref] — [DOI](https://doi.org/10.3386/w8980). Content for both is [U].
- Nicole Maestas, Kathleen J. Mullen & Alexander Strand, "Does Disability Insurance Receipt Discourage Work? Using Examiner Assignment to Estimate Causal Effects of SSDI Receipt," 103 AER 1797–1829 (2013) [V-pub; Crossref returned only SSRN versions] — [PDF](https://eml.berkeley.edu/~saez/course/maestas-mullen-strandAER13.pdf); [HCP page](https://hcp.hms.harvard.edu/publication/does-disability-insurance-receipt-discourage-work-using-examiner-assignment-estimate).
  - Instruments with DDS examiners' allowance rates.
  - About 23% of applicants are on the margin. Their employment would have been 28 percentage points higher without benefits.
- Eric French & Jae Song, "The Effect of Disability Insurance Receipt on Labor Supply," 6 AEJ: Policy 291–337 (2014) [V-xref; ALJ-assignment design U] — [DOI](https://doi.org/10.1257/pol.6.2.291).
- Method reviews [V-xref, V-pub]:
  - Eric Chyn, Brigham Frandsen & Emily Leslie, "Examiner and Judge Designs in Economics: A Practitioner's Guide," 63 J. Econ. Lit. 401–39 (2025). Covers assumptions (exclusion, monotonicity) and estimation trade-offs, with a pretrial-detention case study — [AEA](https://www.aeaweb.org/doi/10.1257/jel.20241719).
  - Frandsen, Lars Lefgren & Leslie, "Judging Judge Fixed Effects," 113 AER 253–277 (2023) — [DOI](https://doi.org/10.1257/aer.20201860). Content U: it is known for a test of the IV exclusion and monotonicity assumptions.

**Testing variance against a random-assignment null; skill vs. preference**
- David S. Abrams, Marianne Bertrand & Sendhil Mullainathan, "Do Judges Vary in Their Treatment of Race?" 41 J. Legal Stud. 347–383 (2012) [V-xref, V-pub] — [Chicago Unbound](https://chicagounbound.uchicago.edu/jls/vol41/iss2/5); [DOI](https://doi.org/10.1086/666006).
  - Uses random assignment in Cook County felony cases to measure between-judge variation in the Black–white incarceration gap.
  - Variation is significant for incarceration but not for sentence length.
  - The gap rises 18 percentage points from the 10th- to the 90th-percentile judge.
- David C. Chan, Matthew Gentzkow & Chuan Yu, "Selection with Variation in Diagnostic Skill: Evidence from Radiologists," 137 QJE 729–783 (2022) [V-xref, V-pub] — [DOI](https://doi.org/10.1093/qje/qjab048); [NBER w26467](https://www.nber.org/papers/w26467).
  - The framework allows variation in both preferences and diagnostic skill, and shows both can be partially identified under quasi-random assignment.
  - Variation in skill explains 39% of the variation in decisions.
  - "policies that improve skill perform better than uniform decision guidelines."
- Other judge-IV studies, citation only [V-xref; content U]:
  - Arnold, Dobbie & Hull, "Measuring Racial Discrimination in Bail Decisions," 112 AER 2992–3038 (2022) — [DOI](https://doi.org/10.1257/aer.20201653).
  - Kleinberg et al., "Human Decisions and Machine Predictions," 133 QJE 237–293 (2018) — [DOI](https://doi.org/10.1093/qje/qjx032).

**Asylum: "Refugee Roulette"**
- Jaya Ramji-Nogales, Andrew I. Schoenholtz & Philip G. Schrag, "Refugee Roulette: Disparities in Asylum Adjudication," 60 Stan. L. Rev. 295 (2007). Examines decisions at four levels: asylum office, immigration court, BIA, and courts of appeals. The book followed (NYU Press 2009) [V-pub] — [Georgetown repository](https://scholarship.law.georgetown.edu/facpub/1900); [Stanford L. Rev. issue](https://review.law.stanford.edu/print/volume-60/issue-2).
- Headline numbers [S: Wikipedia only]:
  - Some officers granted asylum to no Chinese nationals, while others granted it in up to 68% of cases.
  - In Miami, Colombian applicants had a 5% chance of winning before one judge and 88% before another in the same building.
  - Source: [Wikipedia](https://en.wikipedia.org/wiki/Refugee_roulette).

**Ho and coauthors (Stanford / RegLab)**
- Daniel E. Ho, "Does Peer Review Work? An Experiment of Experimentalism," 69 Stan. L. Rev. (Feb. 2017). An RCT with Public Health—Seattle & King County [V-pub] — [Stanford Law](https://law.stanford.edu/publications/does-peer-review-work-an-experiment-of-experimentalism):
  - "Observing identical conditions, inspectors disagreed 60% of the time."
  - Peer review "caused an increase in violations detected and scored by 17% to 19%" and "appeared to decrease variability across inspectors."
  - Design: random pairing; pairs jointly visited establishments, scored independently, then deliberated on divergences.
- Daniel E. Ho & Sam Sherman, "Managing Street-Level Arbitrariness: The Evidence Base for Public Sector Quality Improvement," 13 Annu. Rev. Law Soc. Sci. 251–272 (2017) [V-xref; abstract not retrieved, HTTP 403] — [DOI](https://doi.org/10.1146/annurev-lawsocsci-110316-113608).
- David Ames, Cassandra Handan-Nader, Daniel E. Ho & David Marcus, "Due Process and Mass Adjudication: Crisis and Reform," 72 Stan. L. Rev. 1 (2020) [V-pub] — [Stanford L. Rev.](https://www.stanfordlawreview.org/print/article/due-process-and-mass-adjudication/):
  - Federal agencies "adjudicate more cases than all Article III courts combined," yet "mass adjudication has struggled to achieve an adequate threshold of accuracy."
  - It proposes redesigning quality assurance, drawing on a BVA pilot.
- Ho, Handan-Nader, Ames & Marcus, "Quality Review of Mass Adjudication: A Randomized Natural Experiment at the Board of Veterans Appeals, 2003–16," 35 JLEO 239–288 (2019) [V-xref, V-pub] — [OUP JLEO](https://academic.oup.com/jleo/article/35/2/239/5422997):
  - 5–10% of draft decisions were randomly sent to quality review.
  - Across about 600,000 cases, review "had no appreciable effects on appeals or remands."
  - The reason: meeting the "accuracy" metric conflicted with actually correcting errors.
- Ho, Zoe C. Ashwood & Handan-Nader, "New Evidence on Information Disclosure through Restaurant Hygiene Grading," 11 AEJ: Policy 404–428 (2019) [V-xref; content U] — [DOI](https://doi.org/10.1257/pol.20180230).

**Text-based measures of delegated discretion (from the statute side)**
- David Epstein & Sharyn O'Halloran, *Delegating Powers* (Cambridge UP 1999) [V-xref] — [DOI](https://doi.org/10.1017/cbo9780511609312).
  - The "discretion index" combines a delegation ratio with a constraint ratio, using systematic coding rules.
  - It covers 257 major laws from 1947–1992, with an average of 12.8 delegating provisions per bill.
  - Constraint categories include reporting requirements, time and spending limits, legislative veto, hearings and appeals procedures.
  - [S: secondary notes] — [Adam Brown notes](https://adambrown.info/p/notes/epstein_and_o_halloran_delegating_powers); [Cambridge sample](https://assets.cambridge.org/97805216/60204/sample/9780521660204wsn01.pdf). The exact functional form (delegation × (1 − constraint)) is [U].
- John D. Huber & Charles R. Shipan, *Deliberate Discretion? The Institutional Foundations of Bureaucratic Autonomy* (Cambridge UP 2002) [V-xref, V-pub] — [Cambridge](https://www.cambridge.org/core/product/identifier/9780511804915/type/book).
  - It asks why some legislatures pass "detailed and specific laws" while others pass "general and vague laws that leave the executive and bureaucrats substantial autonomy."
  - It includes a chapter, "Statutes as Blueprints for Policymaking." The word-count measure of statutory detail is [U].
- Matia Vannoni, Elliott Ash & Massimo Morelli, "Measuring Discretion and Delegation in Legislative Texts: Methods and Application to US States," 29 Political Analysis 43–57 (2021) [V-xref, V-pub] — [Cambridge](https://www.cambridge.org/core/journals/political-analysis/article/measuring-discretion-and-delegation-in-legislative-texts-methods-and-application-to-us-states/281BC160DE55EE6A214C570F713EFC6A); [Bocconi](https://economics.unibocconi.eu/publications/measuring-discretion-and-delegation-legislative-texts-methods-and-application-us).
  - "uses information in syntactic parse trees to identify legally relevant provisions, as well as agents and delegated actions."
  - Legislative detail rises (that is, discretion falls) after reforms that give agencies more independence.
  - Delegation to governors rises under unified government.
  - Companion: Ash, Morelli & Vannoni, "Divided government, delegation, and civil service reform," 10 PSRM 82–96 [V-xref] — [DOI](https://doi.org/10.1017/psrm.2020.51).

**Noise taxonomy**
- Daniel Kahneman, Olivier Sibony & Cass R. Sunstein, *Noise: A Flaw in Human Judgment* (2021) [S: Wikipedia only]. Their taxonomy [Wikipedia](https://en.wikipedia.org/wiki/Noise:_A_Flaw_in_Human_Judgment):
  - **System noise**: unwanted variability in judgments that should be identical.
  - **Level noise**: a judge's average differs consistently from other judges'.
  - **Pattern noise**: splits into stable pattern noise (a judge weighs criteria differently) and occasion noise (mood, time).

### Inferences
- The standard estimand is the variance of adjudicator effects, Var(u_j), in y_ij = f(x_i) + u_j (+ u_j × x_i for "pattern" heterogeneity) + ε_ij, identified by random assignment.
  - Anderson, Kling & Stith report SD(u_j) through a random-effect dispersion.
  - Leniency designs use the leave-out mean of u_j as an instrument.
  - Abrams et al. test Var(u_j × race) against a random-assignment null.
  - Fischman uses pairwise disagreement probabilities.
- Var(u_j) measures **inconsistency**, not discretion in the normative sense. It captures any adjudicator-specific factor: permitted choice, idiosyncratic readings of ambiguous text, skill or noise, or constraints such as examiner time (Frakes & Wasserman). Chan, Gentzkow & Yu show that "preference" (threshold) and "skill" (signal precision) can be partly separated when there is outcome feedback.
- The cleanest evidence that discretion is a **property of the rule text** comes from designs where the rule changes and between-adjudicator variance is measured before and after:
  - the Guidelines (Anderson, Kling & Stith);
  - *Booker* (Yang);
  - the SSA grid (cited in Fischman).
  These identify how much Var(u_j) a textual change in delegation buys.
- Ho's 60% inspector-disagreement result under identical conditions is the closest to a pure measurement of between-adjudicator variance with the case held fixed. The peer-review intervention reduced variance without changing the code text. So some measured "discretion" is reducible by deliberation and calibration. That makes it closer to divergent readings, or Solan's pernicious ambiguity, than to delegated choice.
- On the statute side, Vannoni et al. and Epstein & O'Halloran give text-derived priors for how much discretion a provision delegates. Loper Bright's lexical list ("appropriate," "reasonable," "as defined by regulations," "in the judgment of") is a ready, doctrine-backed feature set for a delegation marker.

### Gaps
- Ho's SSA disability work beyond Ames et al. (2020) could not be located with the remaining budget. That includes any specific ALJ grant-rate-dispersion statistic from Ho's group.
- Not located: Gelbach & Marcus (SSA litigation in federal courts), the ACUS SSA studies, and Ho, "Fudging the Nudge" (Yale L.J. 2012). Crossref did not return the last.
- The Refugee Roulette statistics, the Kahneman et al. noise taxonomy, and the Anderson, Kling & Stith magnitudes rest on secondary or abstract-aggregator pages. The primary full texts were not read.

---

## Q4. Work that separates ambiguity from discretion empirically, or models both in one framework

### Takeaway
The closest direct treatment is Fischman (2014). From random-assignment outcome data he measures **inter-judge inconsistency** (partially identified), but **indeterminacy** (the law does not require a unique result) and **error** can only be bounded *jointly*. Outcome data alone cannot tell "the law left this open" apart from "some judges got it wrong." That is a formal version of the behavioral confound in the working answer. The other separating devices are partial:
- Farnsworth et al.: internal vs. external ambiguity elicitation.
- Choi: information vs. determinacy.
- Chan, Gentzkow & Yu: preference vs. skill.
- Re: certainty vs. convergence.
- Rule-change designs: Guidelines, *Booker*, SSA grid.

I found no study that jointly estimates text ambiguity and delegated discretion as separate variance components.

### Cited Findings
- **Fischman's three constructs.** Joshua B. Fischman, "Measuring Inconsistency, Indeterminacy, and Error in Adjudication," 16 Am. L. & Econ. Rev. 40–85 (2014) [V-xref] — [DOI 10.1093/aler/aht011](https://doi.org/10.1093/aler/aht011); [IDEAS](https://ideas.repec.org/a/oup/amlawe/v16y2014i1p40-85..html). Definitions as stated in the working-paper draft [V-full] — [NBER conference draft](https://conference.nber.org/conf_papers/f66640/f66640.pdf):
  - "inconsistency" is "how often the outcome of a case will depend on the identity of the judge selected to decide it; formally ... the probability that two judges would differ in their disposition of a randomly selected case."
  - "'Indeterminacy' denotes the proportion of cases in which the law fails to require a unique result. 'Error' represents the proportion of cases in which the judge's decision conflicts with the result required by law."
- **What Fischman says can be identified** [V-full, draft pp. 3–4]:
  - Inconsistency is "formulated purely in terms of observable judicial decisions," while indeterminacy and error "are only cognizable from an internal point of view."
  - "although indeterminacy and error cannot be measured in isolation ... it is possible to estimate a minimum rate of error as a function of the proportion of cases that are assumed to be indeterminate." The result is an "indeterminacy-error curve."
  - The method uses partial identification (Manski; Tamer). Even with infinite data it yields only bounds.
- **Fischman's asylum application** (Chinese affirmative asylum claims, New York Immigration Court, 2003) [V-full, draft pp. 30–32; published figures may differ]:
  - Average inconsistency is between 26.6% and 51.7% (99% CI). "a randomly selected pair of judges would disagree about the disposition of a randomly selected case at least one-quarter of the time, and perhaps as often as one-half."
  - "If we assume that each case has only one legally correct result, then ... at least 20% of the cases will be wrongly decided. If ... 20% of the cases are indeterminate, then ... at least 10% of decisions are incorrect. The expected error rate will always be positive unless at least 84% of the cases are indeterminate."
- **Fischman's policy implication** [V-full, draft p. 33]:
  - Better training and appellate scrutiny "would likely decrease the error rate among determinate cases. But to the extent that cases are indeterminate and decisions are purely a product of judicial discretion, it is less obvious why that discretion should be exercised by an appellate court or an adjudicator with better legal training."
  - He notes that Legomsky treats many asylum cases as indeterminate.
- **Internal vs. external ambiguity** (Farnsworth, Guzior & Malani 2010). This is an elicitation design that separates one's own uncertainty from expected disagreement among readers. Only the first is contaminated by policy preference [V-pub] — [OUP JLA](https://academic.oup.com/jla/article-lookup/doi/10.1093/jla/2.1.257).
- **Information vs. determinacy** (Choi 2024). Unclarity from missing information is reducible; indeterminacy is not [V-pub] — [Chicago Unbound](https://chicagounbound.uchicago.edu/uclrev/vol91/iss1/1/).
- **Certainty vs. convergence** (Re 2019). "the deciding court's certainty about the right answer" vs. "the predictability that other interpreters would converge on a given answer" [V-pub] — [Chicago Unbound](https://chicagounbound.uchicago.edu/uclrev/vol86/iss6/5).
- **Preference vs. skill** (Chan, Gentzkow & Yu 2022). Under quasi-random assignment, threshold (preference) heterogeneity and signal-precision (skill) heterogeneity are partially identified. Skill explains 39% of decision variation. Skill-improving policies beat uniform guidelines [V-pub] — [NBER](https://www.nber.org/papers/w26467); [DOI](https://doi.org/10.1093/qje/qjab048).
- **Ambiguity findings track ideology.** Thomas J. Miles & Cass R. Sunstein, "Do Judges Make Regulatory Policy? An Empirical Investigation of Chevron," 73 U. Chi. L. Rev. 823 (2006) [V-pub; start page U] — [Chicago Unbound](https://chicagounbound.uchicago.edu/uclrev/vol73/iss3/1/); [PDF](https://lawreview.uchicago.edu/sites/default/files/73_3_Miles_Sunstein.pdf):
  - Under Chevron, conservative justices validate agency interpretations less often than liberal justices.
  - Validation rates shift with the party of the administration.
  - Republican appointees on appellate panels were more willing to invalidate liberal EPA and NLRB decisions (1990–2004).
- **Doctrine on which ambiguity becomes discretion** (Loper Bright 2024). The majority holds that ambiguity is not delegation, while express flexible terms ("appropriate," "reasonable") are. The dissent treats ambiguity and gaps as implicit delegation [V-full] — [slip opinion](https://www.supremecourt.gov/opinions/23pdf/22-451_7m58.pdf).

### Inferences
- **How the working answer holds up against the literature:**
  - **Supported.** The conceptual split (which rule is stated vs. a rule that delegates a choice) matches Loper Bright, Sunstein (1989), Dworkin's strong discretion, and Fischman's split of indeterminacy from inconsistency.
  - **Refined.**
    - (i) Ambiguity is not always *shared* uncertainty. Solan's pernicious ambiguity and Farnsworth et al.'s external ambiguity show up as confident between-reader disagreement.
    - (ii) Ambiguity is not always *reducible*. Choi's indeterminacy, and Hart's and Endicott's vagueness, leave residual open cases that work like weak discretion.
    - (iii) Evaluative standards are both vague and delegating.
  - **Confirmed as a confound.** Fischman proves the behavioral confound for outcome data. Indeterminacy (which includes delegated choice) and error trade off along a curve. Only outside information can pin down where on the curve the truth lies, for example an assumption about the share of determinate cases.
- **Identification levers the literature suggests for a latent decision model.** Each separates a shared rule uncertainty, call it θ (a posterior over readings), from an adjudicator effect u_j whose variance is set by the delegation:
  1. **Rule-text variation.** Compare Var(u_j) across provisions, or over time, as delegation markers change while case mix is held fixed. Examples: Guidelines, *Booker*, the SSA grid, and Loper Bright's lexical delegation markers or Vannoni et al.'s parse-tree measures.
  2. **Elicitation.** Separate own-confidence from predicted agreement (Farnsworth et al.), from humans or from LLMs with between-model variance modeled explicitly (Choi 2025).
  3. **Identical-case replication.** Pairs observe identical conditions (Ho 2017). Then a deliberation or calibration step tests how much variance is reducible, which points to divergent readings, and how much persists, which points to delegated choice or preference.
  4. **Outcome or ground-truth feedback.** Use appellate reversals or later outcomes to split skill or error from preference (Chan, Gentzkow & Yu; Fischman's error dimension).
- **A testable signature (my inference, not found in the literature).** Ambiguity as a choice among discrete senses should produce *clustered, multimodal* adjudicator behavior: a few reading-types, matching Solan's camps of confident readers. Delegated discretion over a continuous standard should produce *continuous* threshold dispersion, as in Chan, Gentzkow & Yu. A mixture-of-readings vs. continuous-random-effect model comparison could operationalize Isabel's distinction. This is not established in any source found.
- **Implication for an unsupported or ambiguous provision in the project.** Following Loper Bright and Kaplow, a conservative default is to code explicit flexible or delegating language as a discretion parameter (a prior on Var(u_j)). Shared uncertainty over readings, with a single "best reading" target, should be coded as ambiguity, a posterior over θ.

### Gaps
- No paper found that jointly estimates textual ambiguity and delegated discretion in one model with separate components. This may reflect the truncated search, since the web-search budget was exhausted before targeted queries on, for example, "ambiguity" × "judge random effects" × "statutory text features."
- Not checked: Fischman's other work on circuit-panel voting (J.L. Econ. & Org. 2015; J. Legal Stud. 2011) for models that separate law from preference. Kastellec and Lax ("doctrine space") models were also not checked.
- The Fischman numbers are from the NBER conference draft. The published ALER (2014) figures were not checked and may differ.
- Unverified page and venue details:
  - Loper Bright U.S. Reports page (603 U.S. 369);
  - Miles & Sunstein start page (823);
  - Hart's "Discretion" essay start page;
  - the published venues of the Yang (*Booker*), Tobia–Slocum–Nourse and Ben-Shahar–Strahilevitz papers.
