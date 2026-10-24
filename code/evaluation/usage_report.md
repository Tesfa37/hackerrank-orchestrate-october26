# Model usage and cost analysis

This is an incomplete full-dataset attempt: 419/518 rows, with no final output.csv. Model: `gemini-3.5-flash-lite`; provider: Google Gemini Developer API. The existing Free Tier configuration and $0 paid API budget were preserved. No billing or credential changes or paid fallback occurred. Provider invoices were not independently inspected; $0 is the configured free-tier billed-cost estimate.

| Measure | Value |
| --- | ---: |
| referenced_calls | 44 |
| new_calls_this_process | 0 |
| cached_results_reused | 44 |
| production_attempts | 51 |
| attempts_with_unavailable_usage | 5 |
| input_tokens | 77429 |
| output_tokens | 68176 |
| thinking_tokens | 0 |
| total_tokens | 145605 |
| Known total tokens per requested case | 281.091 |
| Estimated billed cost total / per requested case (USD) | 0 / 0 |

The last full run was offline. Counts include original production usage of every reused response, associated failures/retries and repair predecessors. Unknown provider usage is not estimated as zero. Output and thinking tokens are separate; total uses provider-reported totals. Denominator is all 518 requested cases, including unresolved cases.

Current cloud development ledger: 69 attempts, {'received': 64, 'HTTP_429': 5}; 116262 known input, 87744 known output, 204006 known total tokens. 5 attempts have unavailable usage. These development totals overlap the production attribution above and must not be added to it. They include superseded prompts, rejected source interpretations and corrective calls. The earlier local setup smoke test (6 input + 1 output tokens) is separate.

Caches and rejected responses are genuine provider envelopes, not answer labels; neither is committed or archived. Formatting corrections recovered only envelopes whose exact request, original received-attempt ledger, response integrity and current semantics validated; provider content was not edited. Reinspection separated observation times from Modified/Created dates and retained partial field coverage as uncertainty. Bounded one-stage corrections addressed source reference-role and coverage inconsistencies without expected labels. All application calls used this one model.

Organizer-guidance and attachment-scope follow-up: all 518 requests were rerun offline with zero new calls. Known production attribution remains 145,605 tokens, including cached work and known retries; the paid budget remains $0. The original run returns419/518 with99holds; the separate confirmed-exclusion evaluation view is418/516 with98holds. Neither is a successful final518-row output run. Exclusion reporting and the deterministic source-scope correction use no model requests and change no credentials or billing settings.
