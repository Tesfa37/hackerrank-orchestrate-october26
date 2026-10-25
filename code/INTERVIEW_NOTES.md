# Interview notes

## Final selected submission

The user selected evidence-based prediction. The unchanged518-row candidate is
153 COMPLETE,355 INCOMPLETE,10 NOT_APPLICABLE, with99assumption-dependent cases:
98conditional COMPLETE and one archive-risk forecast in excluded case_55.
Mandatory evaluation_report.md and usage_report.md now lead with this candidate;
strict audit results are historical baseline measurements. A bounded review of
all35missing sample verifications and4extras found no evidence-supported accuracy
fix, so predictions and metrics are unchanged from07aa568. Fifty conditional
COMPLETE cases have one qualifying observation, and78have audit-retention-only
facts. Explain this limitation candidly; retained records do not certify global
deletion. The final report/ledger regression suite has201tests.

## Latest prediction-policy experiment

The strict results below remain the evidence-certification baseline. The optional
evidence-based prediction policy produces518 structurally valid rows, compared
with419 strict rows;99 cases depend on additional assumptions. It does not infer
failure from every missing confirmation. One restore-risk finding is a forecast
from known archive existence rather than proven current authorization; its case
is among the two confirmed exclusions, but prediction logic never reads that list.
On all32 public samples the prediction policy covers29 and gets29 statuses right
(90.625%), with step F1 89.01% and exact sequence8/32 unchanged. Three requests still
lack any eligible owned key for an evidence-backed plan and remain absent from
the sample candidate. These are development measurements, not hidden accuracy.
The blanket conservative fallback returns518 labels but99 invalid plans and is
rejected. See evaluation/approach_comparison.md for every count and assumption.
There are196 regression tests after the comparison additions. Say "schema-valid
prediction candidate" rather than "all deletions proved" when discussing output.csv.

## Opening explanation

I built an AI-assisted deletion-audit pipeline. The model interprets multilingual request intent and extracts facts from business screenshots and PDFs. Deterministic code reconstructs identities and resource state at each audit cutoff, applies the supplied deletion rules, and emits an ordered remediation and verification plan. It never performs the proposed deletion actions. The model is not asked to manufacture final answers.

The hard part is proving what happened: a successful workflow is only a claim, a missing row needs a relevant complete scope, and a business document can contain identifiers without proving a separate live-system record exists. I preserve those distinctions and report unresolved proof gaps rather than convert uncertainty into a supported verdict.

## Walk through one request

1. Classify whether the text authorizes deletion or checks a prior deletion. Non-deletion requests return NOT_APPLICABLE with no deletion steps.
2. Resolve a stable subject using current and eligible historical identifiers. Match old email, phone and hash values; do not join people by names or numeric suffixes.
3. Retrieve resource observations and explicit relationships. Keep physical replicas separate. Require source capture, observation and any necessary identity-link event to be available by audit_at.
4. Select current supported state. A known owned key can be absent in its first complete snapshot. A complete empty table does not tell us an unprinted account resource key.
5. Apply deletion policy: delete private attachments, redact shared messages and tombstones, anonymize applicable analytics, preserve required retention, and assess actual flow/restore configuration.
6. Order actions and verification. Stop dangerous flows/restores before dependent records. Validate exact schema, array ordering and citations before publication.

## Current measured results

| Measure | Result |
| --- | ---: |
| Original full-set coverage | 419/518 (80.89%); 99 unresolved |
| Excluding only confirmed case_39 and case_55 | 418/516 (81.01%); 98 unresolved |
| Public-sample coverage | 23/32 (71.875%) |
| Status accuracy on all 32 public cases | 23/32 (71.875%) |
| Exact ordered step sequence on all 32 | 8/32 (25%) |
| Step precision / recall / F1 | 97.89% / 72.02% / 82.99% |
| Aligned field accuracy | 68.73% |
| Regression checks | 186 tests pass |

Coverage and accuracy answer different questions. Returning 23 correct statuses is not 100% accuracy across 32 cases. Missing cases remain failures in primary sample metrics. Full-set hidden accuracy is unknown. The public examples are development data, so improvements on them are not an independent generalization estimate. The sample evaluator compares complete step content, including citations; exact sequence also checks array order and numbering.

## Demonstrated fixes worth discussing

- Finance references with explicit retention instructions were incorrectly promoted into unknown privacy-resource obligations. I preserved their non-destructive business constraints without inventing an active legal hold or a new privacy-resource type.
- A customer-upload PDF body was incorrectly treated as a separate live ticket. Its continued attachment-properties section and fully printed technical reference establish its document scope. Correcting that removes three false ticket steps; an independently evidenced storage object remains because no grounded same-object alias equates it with the upload.
- Stable user_id alone is permitted in an account tombstone. That is separate from proving the removal of name/email/phone/hash: fields not shown are not redaction proof.
- Negative snapshots can prove absence for grounded keys. Observation time, capture time and catalog-link availability prevent future evidence from leaking into an earlier audit.

These are generic source/policy corrections with synthetic regression fixtures. Case IDs and expected steps do not branch prediction behavior.

## Remaining limitations and exact missing proof

After the two confirmed exclusions, 98 holds remain: 69 eligible account ownership-link gaps despite negative scopes, 25 primary-evidence capture/cutoff gaps, 3 missing eligible direct primary proof or complete scope, and one tombstone field-removal proof gap. The complete list and examples are in the blocker reports. An unspecified promise to exclude other invalid cases does not establish that these 98 are all invalid.

For case_01, the expected account key is absent from the cited snapshot; the eligible resource-only deletion claim has no subject identifier. Identity/history supplies the person but not the account key. Missing proof is an eligible subject/account association or keyed readback. I cannot infer it from the user-ID suffix. This example is investigated only inside evaluation, not used as a prediction shortcut.

The whole-account completeness guard is stricter than the contract's literal wording and does not prove exhaustive discovery. It prevents an otherwise-complete verdict supported only by peripheral retention evidence. Removing it would not produce the missing keys/citations; a clearer scoped-audit contract would be a better long-term design.

The schema offers no uncertainty state. NOT_APPLICABLE is reserved for non-deletion requests; missing proof is not automatically a supported INCOMPLETE verdict. The repository still asks for 518 rows. Organizer clarification on excluded/unsupported-row formatting is pending. No completed output.csv is claimed.

## Scalability and robustness questions

**What actually scales?** Intent calls are batched, media interpretation is reused across requests, genuine results are hashed and cached, and identity/resource indexes avoid repeating all model work. Policy and ordering are local computations. All 518 cases were exercised, including diagnostic failures.

**What is not established?** No production throughput benchmark, large-scale load test, distributed queue, concurrent cache-writer support or persistent evidence index. Some global scans and per-cutoff caches still cost memory/time. Provider latency and free-tier quota limit fresh generation. A missing media review can block unrelated deletion cases because the present pipeline requires complete media discovery.

**Why combine AI and deterministic code?** AI handles language and varied business artifacts; explicit code makes cutoff, policy, retention, dependency order and serialization inspectable. Schema validation reduces malformed output but cannot certify semantic extraction. Source quotes and uncertainty checks are still necessary.

**Why retain safeguards despite lower coverage?** A fabricated key or future observation can yield a plausible CSV while making the audit wrong. I expose precise missing proof and keep supported rows separate. I would improve grounding and the output contract before weakening those checks.

**How is $0 maintained?** The user configured a free-tier project with billing disabled. The program has one fixed model, no paid fallback and bounded transport retries; daily quota exhaustion stops work. It does not inspect or enforce project billing itself. This finalization made zero generation calls. Live no-cache regeneration is documented, not claimed as newly tested.

**Can another machine run it?** The archive was extracted, dependencies installed in a new virtual environment, and tests/CLI commands exercised. Empty-cache preparation and missing-cache/key failures were tested. A separate offline replay with copied genuine envelopes reproduces the supported predictions. A clean machine cannot infer those model results merely from code or partial output files; it needs real configured free-tier extraction.

**Next engineering work?** Clarify the uncertainty/excluded-row contract; obtain exact missing participant proof where available; improve source-grounded extraction; then add incremental indexes, per-subject readiness and quota-aware work scheduling. None of these changes authorizes invented verdicts.

## Interview cautions

Use the evaluation report's denominators. Say "proposed remediation," not actions performed. Describe model extraction as fallible. Distinguish tests of mocked provider failures from current live quota behavior. The organizer screenshot recommends an agent and scalability/robustness; it does not establish a mandatory API rule. Keep credentials private, do not call a partial CSV a completed submission, and do not claim excluded cases have known answers.
