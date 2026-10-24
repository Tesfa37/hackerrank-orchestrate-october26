# Unresolved audit investigation

Reproduced 518 requests using participant data and genuine offline model caches: 419 resolved, 99 blocked.

No expected answers or hidden labels were read. No API calls, billing changes, credential edits, prediction files, or manufactured resource IDs were produced.

| Diagnostic group | Cases |
| --- | ---: |
| Reviewed image/PDF does not establish required fields, category, or state | 2 |
| Post-request negative scope without an eligible primary resource ownership edge | 69 |
| No eligible direct primary evidence or complete primary scope | 3 |
| Direct primary evidence excluded by source/capture/observation cutoff | 25 |

The groups identify the next missing proof; they do not establish that an unresolved case is COMPLETE or INCOMPLETE. A SQL table tagged complete by the adapter is scoped snapshot evidence, not permission to guess an absent user's resource ID. A missing row can prove absence only with applicable exhaustive coverage and a grounded identity/resource relationship. A snapshot before the request is separately identified; evidence captured after audit_at remains excluded even when its event is earlier.

Historical email, phone, and hash values at or before each cutoff are checked against the resolved subject. Raw SQL/JSON entities and explicit log traces are independently inventoried for primary records missed by parsing. Screenshots/PDFs use their genuine cached interpretation; this is not independent verification that a model extracted every visual fact.

Independent raw inventory: 731 explicit primary SQL/JSON/log/text records. Historical identifier gaps among blocked cases: 0. Eligible raw primary records requiring parser review: 0.

Identity checks: 518 requests resolve to exactly one subject; 0 fail identity resolution. 100 request emails match an old email in an eligible past change; 11 of those requests remain blocked. Hydrated media: 15; source-fact reinspections: 15.

Primary-anchor blockers were separately reviewed for negative snapshots: 90 of 97 have eligible complete primary scopes at or after the request, 4 have only pre-request scopes, and 3 have none. These counts identify useful scoped negative evidence, rather than asserting that all anchor blockers lack every kind of evidence. No scope supplies an unprinted resource ID or an absent person's ownership link merely because no identifier matched a row.

## Reviewed image/PDF does not establish required fields, category, or state

Cases: case_46, case_55.

**case_46** (user_17); request `2026-03-08T03:00:00Z`, audit cutoff `2026-03-11T08:00:00Z`.

Missing proof: The most recent update timestamp (10 Mar 2026 07:18 UTC) is later than the supplied manifest capture timestamp (2026-03-10T06:00:00Z).; A displayed lifecycle/event timestamp is later than manifest capture; both times are preserved without repair; The reference view does not explicitly establish removal of name, email, phone and email hash; fields not shown are not redaction proof.

- `evidence_01`: `evidence/logs/service_events_ap_south_20260915.log`, resource `account_4092` (ABSENT); capture `2026-09-15T11:59:39Z`, observation `2026-09-15T11:51:19Z`.
- `evidence_67`: `evidence/logs/resource_lookup_trace_20260310_061801.log`, resource `account_6523` (ABSENT); capture `2026-03-10T06:18:01Z`, observation `2026-03-10T06:18:01Z`.
- `evidence_42`: `evidence/images/deleted_account_reference_20260310.png`, resource `tombstone_17` (UNKNOWN); capture `2026-03-10T06:00:00Z`, observation `2026-03-10T06:00:00Z`, required catalog link `2026-03-10T06:07:01Z`.

Reviewed source `evidence_42`, `evidence/images/deleted_account_reference_20260310.png`, resource `tombstone_17`: The most recent update timestamp (10 Mar 2026 07:18 UTC) is later than the supplied manifest capture timestamp (2026-03-10T06:00:00Z).; A displayed lifecycle/event timestamp is later than manifest capture; both times are preserved without repair; The reference view does not explicitly establish removal of name, email, phone and email hash; fields not shown are not redaction proof Capture `2026-03-10T06:00:00Z`, observation `2026-03-10T06:00:00Z`.

Latest eligible primary scope: `evidence_66`, `evidence/databases/customer_data_inventory_20260310.sql`, table/collection `customer_profiles`, capture `2026-03-10T05:38:48Z`, observation `2026-03-10T05:38:48Z`, 0 resource rows. No account resource ownership edge is inferred from that row count or from an identifier suffix.

**case_55** (user_16); request `2026-04-27T06:00:00Z`, audit cutoff `2026-04-30T11:00:00Z`.

Missing proof: Archive existence, health, retention or past restore events do not establish current restore authorization for this subject.

- `evidence_01`: `evidence/logs/service_events_ap_south_20260915.log`, resource `account_9494` (ABSENT); capture `2026-09-15T11:59:39Z`, observation `2026-09-15T11:52:44Z`.

Reviewed source `evidence_32`, `evidence/images/backup_restore_console_20260429.png`, resource `backup_9287`: Archive existence, health, retention or past restore events do not establish current restore authorization for this subject Capture `2026-04-29T09:00:00Z`, observation `2026-04-29T09:00:00Z`.

Latest eligible primary scope: `evidence_33`, `evidence/databases/customer_data_regional_replicas_20260424.sql`, table/collection `customer_data_primary`, capture `2026-04-24T08:00:00Z`, observation `2026-04-24T08:00:00Z`, 0 resource rows. No account resource ownership edge is inferred from that row count or from an identifier suffix.

## Post-request negative scope without an eligible primary resource ownership edge

Cases: case_45, case_57, case_58, case_59, case_60, case_97, case_103, case_107, case_108, case_111, case_112, case_150, case_151, case_152, case_155, case_157, case_162, case_178, case_183, case_190, case_191, case_204, case_206, case_225, case_226, case_243, case_244, case_253, case_257, case_260, case_274, case_276, case_277, case_294, case_295, case_297, case_299, case_304, case_308, case_309, case_343, case_345, case_346, case_351, case_354, case_362, case_393, case_395, case_398, case_403, case_408, case_409, case_411, case_412, case_424, case_427, case_448, case_452, case_456, case_457, case_458, case_462, case_480, case_493, case_494, case_497, case_502, case_506, case_512.

**case_45** (user_03); request `2026-09-03T04:00:00Z`, audit cutoff `2026-09-06T09:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

Latest eligible primary scope: `evidence_90`, `evidence/databases/customer_data_inventory_20260905.sql`, table/collection `customer_profiles`, capture `2026-09-05T07:18:01Z`, observation `2026-09-05T07:18:01Z`, 0 resource rows. No account resource ownership edge is inferred from that row count or from an identifier suffix.

**case_57** (user_55); request `2026-08-27T10:00:00Z`, audit cutoff `2026-09-21T10:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

Latest eligible primary scope: `evidence_05`, `evidence/databases/customer_data_read_replica_20260921.sql`, table/collection `customer_data_primary`, capture `2026-09-21T10:00:00Z`, observation `2026-09-21T10:00:00Z`, 0 resource rows. No account resource ownership edge is inferred from that row count or from an identifier suffix.

**case_58** (user_56); request `2026-08-26T10:00:00Z`, audit cutoff `2026-09-21T10:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

Latest eligible primary scope: `evidence_05`, `evidence/databases/customer_data_read_replica_20260921.sql`, table/collection `customer_data_primary`, capture `2026-09-21T10:00:00Z`, observation `2026-09-21T10:00:00Z`, 0 resource rows. No account resource ownership edge is inferred from that row count or from an identifier suffix.

## No eligible direct primary evidence or complete primary scope

Cases: case_524, case_530, case_532.

**case_524** (user_522); request `2026-01-17T12:00:00Z`, audit cutoff `2026-01-29T12:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

No eligible direct account/tombstone row or complete primary scope was found for this subject.

**case_530** (user_528); request `2026-01-11T12:00:00Z`, audit cutoff `2026-01-29T12:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

No eligible direct account/tombstone row or complete primary scope was found for this subject.

**case_532** (user_530); request `2026-01-09T12:00:00Z`, audit cutoff `2026-01-29T12:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

No eligible direct account/tombstone row or complete primary scope was found for this subject.

## Direct primary evidence excluded by source/capture/observation cutoff

Cases: case_64, case_69, case_70, case_126, case_127, case_175, case_213, case_215, case_218, case_219, case_221, case_231, case_313, case_314, case_319, case_322, case_335, case_336, case_339, case_423, case_430, case_463, case_464, case_467, case_470.

**case_64** (user_62); request `2026-09-04T09:00:00Z`, audit cutoff `2026-09-16T09:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

- `evidence_06`: `evidence/logs/structured_service_events_eu_west_20260918.log`, resource `account_565` (ABSENT); capture `2026-09-18T11:55:24Z`, observation `2026-09-16T08:56:26Z`.

Latest eligible primary scope: `evidence_93`, `evidence/databases/customer_data_inventory_20260916.sql`, table/collection `customer_profiles`, capture `2026-09-16T08:37:39Z`, observation `2026-09-16T08:37:39Z`, 1 resource rows. No account resource ownership edge is inferred from that row count or from an identifier suffix.

**case_69** (user_67); request `2026-08-30T09:00:00Z`, audit cutoff `2026-09-16T09:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

- `evidence_06`: `evidence/logs/structured_service_events_eu_west_20260918.log`, resource `account_6138` (ABSENT); capture `2026-09-18T11:55:24Z`, observation `2026-09-16T08:57:19Z`.

Latest eligible primary scope: `evidence_93`, `evidence/databases/customer_data_inventory_20260916.sql`, table/collection `customer_profiles`, capture `2026-09-16T08:37:39Z`, observation `2026-09-16T08:37:39Z`, 1 resource rows. No account resource ownership edge is inferred from that row count or from an identifier suffix.

**case_70** (user_68); request `2026-08-29T09:00:00Z`, audit cutoff `2026-09-16T09:00:00Z`.

Missing proof: Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone.

- `evidence_06`: `evidence/logs/structured_service_events_eu_west_20260918.log`, resource `account_6633` (PRESENT); capture `2026-09-18T11:55:24Z`, observation `2026-09-10T08:56:20Z`.
- `evidence_06`: `evidence/logs/structured_service_events_eu_west_20260918.log`, resource `account_6633` (ABSENT); capture `2026-09-18T11:55:24Z`, observation `2026-09-16T08:56:42Z`.

Latest eligible primary scope: `evidence_93`, `evidence/databases/customer_data_inventory_20260916.sql`, table/collection `customer_profiles`, capture `2026-09-16T08:37:39Z`, observation `2026-09-16T08:37:39Z`, 1 resource rows. No account resource ownership edge is inferred from that row count or from an identifier suffix.

## Reproduction

```bash
python3 code/investigate.py --reinspect-media
```

The JSON companion contains every blocked case, provenance, scope timestamps, and history checks. This report records a development investigation, not final prediction accuracy or a completed submission.

## Changes from the initial 98 blockers

Initial groups were 69 negative snapshots without owned keys, 25 capture exclusions, 3 missing primary-scope proofs and 1 registry interpretation error. The registry category error is corrected: rule 15 permits its stable user_id and it is not counted as exposed PII. Required name/email/phone/hash removal remains unverified. One newly held archive case needs current restore authorization, increasing the final total to 99.

Software fixes were kept separate from genuine missing proof: exact UTC text parsing, date-only retention intervals, printed internal record IDs versus external ticket/report aliases, blank UI markers, object names, known-key negative snapshots, and replica-state coverage. None of those repairs authorizes using future captures or inventing an unknown resource ID. Some candidate lines above are intentionally ineligible and are listed only to explain exclusion; they were not used as audit proof.
