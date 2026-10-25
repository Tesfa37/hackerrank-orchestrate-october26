# Selected submission model usage and cost

**Selected output: 518/518 evidence-based predictions**, not the historical 419-row strict audit. Root `output.csv` is bound to its assumptions/usage ledger by SHA256 `dab79bc63c7a8d5357c3b865e091f34f2cc9a7c49a940aec3e326e85669f64d1`. It contains 153 COMPLETE, 355 INCOMPLETE and 10 NOT_APPLICABLE, with 99 assumption-dependent cases (98 conditional COMPLETE and 1 inferred archive-risk case).

Provider: Google Gemini Developer API. Application model: `gemini-3.5-flash-lite`. All application extraction calls use this model; no paid fallback or model switch is used.

| Final full-dataset attribution | Value |
| --- | ---: |
| Requested / predicted cases | 518 / 518 |
| Unique referenced genuine extraction responses | 44 |
| Reused cached responses | 44 |
| New model calls in the candidate publication process | 0 |
| Attributed production attempts, including retries/repairs | 51 |
| Attempts with unavailable provider token usage | 5 |
| Known input tokens | 77,429 |
| Known output tokens | 68,176 |
| Known thinking tokens | 0 |
| Known total tokens | 145,605 |
| Known tokens per requested/predicted case | 281.091 |
| Configured paid API budget | $0 |
| Estimated billed cost under the configured free project | $0 total / $0 per case |

These totals include the original production work behind every genuine response reused by the final candidate, including attributable retry and corrective ancestry. Reusing a response means zero new generation, not zero historical production work. The same extraction work feeds strict and prediction policies; do not multiply it by three or add overlapping public-sample replay totals.

5 attempts have no provider token usage. Their usage is unknown, not silently counted as zero. The 145,605 total is the known provider-reported attribution, not a claim that all failed-attempt work is measured. Invoices, current project billing state, remaining quota and provider-side charges were not independently inspected. The user configured a free-tier project with billing disabled; this configuration and the $0 paid budget were preserved. The application does not enforce a dollar cap on an already billed project. No new live calls or billing/credential changes were made during finalization.

## Historical development and strict baseline

The earlier strict run returned 419/518 rows using the same 44 referenced responses and known 145,605 production tokens. It was an incomplete audit baseline, not the selected final output. Its usage must not be added again to the candidate totals.

The previously recorded cloud development ledger contains 69 attempts (64 received, 5 HTTP429), 116,262 known input tokens, 87,744 known output tokens and 204,006 known total tokens; five attempts have unavailable usage. This historical development work overlaps the production attribution and includes superseded prompts, rejected interpretations and corrections. These totals must not be summed with the production totals. The earlier local setup smoke test used 6 input and 1 output token separately.

Current finalization, comparison, regression and archive-replay commands are offline or stop before a missing-key request; they add zero application-model calls. Dependency downloads are not generation calls. Exact coding-assistant runtime model metadata and coding-assistant token/cost accounting are not exposed by this session; they are not invented or conflated with the application model.

Original genuine response envelopes and attempt ledgers remain private local provenance. They are excluded from Git/code.zip, together with credentials and caches. The selected candidate records its measured usage summary in output.assumptions.json. Uncertain predictions are not promoted into source facts or certified deletion events.
