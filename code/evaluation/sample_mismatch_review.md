# Public-sample mismatch review

Expected answers are confined to evaluation. This report never supplies identity edges, resource IDs or labels to the predictor. Missing/extra content ignores step numbering; exact sequence still includes numbering and order.

| Case | Returned / expected status | Missing / extra steps |
| --- | --- | --- |
| case_01 | unresolved / COMPLETE | 1 / 0 |
| case_02 | unresolved / COMPLETE | 1 / 0 |
| case_03 | COMPLETE / COMPLETE | 1 / 0 |
| case_04 | unresolved / COMPLETE | 2 / 0 |
| case_05 | INCOMPLETE / INCOMPLETE | 0 / 0 |
| case_06 | INCOMPLETE / INCOMPLETE | 1 / 0 |
| case_07 | INCOMPLETE / INCOMPLETE | 1 / 6 |
| case_08 | INCOMPLETE / INCOMPLETE | 1 / 0 |
| case_09 | INCOMPLETE / INCOMPLETE | 2 / 0 |
| case_10 | INCOMPLETE / INCOMPLETE | 1 / 0 |
| case_11 | INCOMPLETE / INCOMPLETE | 0 / 0 |
| case_12 | INCOMPLETE / INCOMPLETE | 0 / 0 |
| case_13 | INCOMPLETE / INCOMPLETE | 0 / 0 |
| case_14 | INCOMPLETE / INCOMPLETE | 0 / 0 |
| case_15 | INCOMPLETE / INCOMPLETE | 0 / 0 |
| case_16 | INCOMPLETE / INCOMPLETE | 0 / 0 |
| case_17 | unresolved / INCOMPLETE | 5 / 0 |
| case_18 | INCOMPLETE / INCOMPLETE | 2 / 0 |
| case_19 | INCOMPLETE / INCOMPLETE | 0 / 0 |
| case_20 | INCOMPLETE / INCOMPLETE | 2 / 0 |
| case_21 | unresolved / COMPLETE | 3 / 0 |
| case_22 | INCOMPLETE / INCOMPLETE | 1 / 0 |
| case_23 | INCOMPLETE / INCOMPLETE | 2 / 0 |
| case_24 | INCOMPLETE / INCOMPLETE | 1 / 0 |
| case_25 | unresolved / COMPLETE | 3 / 0 |
| case_26 | unresolved / COMPLETE | 6 / 0 |
| case_27 | unresolved / COMPLETE | 6 / 0 |
| case_28 | unresolved / COMPLETE | 6 / 0 |
| case_29 | INCOMPLETE / INCOMPLETE | 2 / 0 |
| case_30 | INCOMPLETE / INCOMPLETE | 2 / 0 |
| case_31 | COMPLETE / COMPLETE | 1 / 0 |
| case_32 | INCOMPLETE / INCOMPLETE | 1 / 0 |

## case_01

Audit cutoff: `2026-09-03T11:30:00Z`. No eligible evidence links this subject to a resource

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_001 | evidence_54: evidence/databases/customer_accounts_failover_replica_20260902.sql; capture 2026-09-02T23:00:00Z | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_02

Audit cutoff: `2026-09-04T15:00:00Z`. No eligible evidence links this subject to a resource

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_002 | evidence_54: evidence/databases/customer_accounts_failover_replica_20260902.sql; capture 2026-09-02T23:00:00Z | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_03

Audit cutoff: `2026-09-26T11:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ANONYMIZED | analytics_platform / analytics_9406 | evidence_94: evidence/logs/resource_lookup_trace_20260926_103856.log; capture 2026-09-26T10:38:56Z; evidence_94: evidence/logs/resource_lookup_trace_20260926_103856.log (ANALYTICS_PROFILE/ANONYMIZED; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_04

Audit cutoff: `2026-09-07T10:20:00Z`. No eligible evidence links this subject to a resource

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_004 | evidence_54: evidence/databases/customer_accounts_failover_replica_20260902.sql; capture 2026-09-02T23:00:00Z | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_ANONYMIZED | analytics_platform / analytics_901 | evidence_56: evidence/records/customer_analytics_report_20260907.json; capture 2026-09-07T09:45:00Z; evidence_56: evidence/records/customer_analytics_report_20260907.json (ANALYTICS_PROFILE/ANONYMIZED; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_05

Audit cutoff: `2026-09-08T13:40:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |

## case_06

Audit cutoff: `2026-09-10T09:15:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_006 | activity_3545: dataset/system_activity.csv (DELETE_RECORD; event 2026-08-30T17:08:20Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_07

Audit cutoff: `2026-09-12T08:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_007 | activity_3590: dataset/system_activity.csv (DELETE_RECORD; event 2026-09-01T19:28:39Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| extra | FINDING / REPORT_REMAINING_RECORD | object_storage / object_19 | evidence_46: evidence/images/object_storage_browser_20260213.png; capture 2026-02-13T08:00:00Z; evidence_46: evidence/images/object_storage_browser_20260213.png (SUPPORT_ATTACHMENT/PRESENT; eligible) | Additional source-backed physical object omitted by the reference; its visible filename differs from the support attachment, so a same-object alias is unproven. |
| extra | FINDING / REPORT_EXPOSED_PII | support_platform / CS-4827 | evidence_58: evidence/documents/delivery_correction_attachment.pdf; capture 2026-09-12T07:30:00Z; evidence_58: evidence/documents/delivery_correction_attachment.pdf (SUPPORT_MESSAGE/PRESENT; eligible) | Unresolved document-body versus live-ticket interpretation: a customer-upload PDF contains a ticket reference, but independent current message state and ticket/attachment identity are not established. |
| extra | REMEDIATION / DELETE_RECORD | object_storage / object_19 | evidence_46: evidence/images/object_storage_browser_20260213.png (SUPPORT_ATTACHMENT/PRESENT; eligible) | Additional source-backed physical object omitted by the reference; its visible filename differs from the support attachment, so a same-object alias is unproven. |
| extra | REMEDIATION / REDACT_RECORD | support_platform / CS-4827 | evidence_58: evidence/documents/delivery_correction_attachment.pdf (SUPPORT_MESSAGE/PRESENT; eligible) | Unresolved document-body versus live-ticket interpretation: a customer-upload PDF contains a ticket reference, but independent current message state and ticket/attachment identity are not established. |
| extra | VERIFICATION / VERIFY_RECORD_ABSENT | object_storage / object_19 | evidence_46: evidence/images/object_storage_browser_20260213.png (SUPPORT_ATTACHMENT/PRESENT; eligible) | Additional source-backed physical object omitted by the reference; its visible filename differs from the support attachment, so a same-object alias is unproven. |
| extra | VERIFICATION / VERIFY_RECORD_REDACTED | support_platform / CS-4827 | evidence_58: evidence/documents/delivery_correction_attachment.pdf (SUPPORT_MESSAGE/PRESENT; eligible) | Unresolved document-body versus live-ticket interpretation: a customer-upload PDF contains a ticket reference, but independent current message state and ticket/attachment identity are not established. |

## case_08

Audit cutoff: `2026-09-14T16:10:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_008 | activity_3554: dataset/system_activity.csv (DELETE_RECORD; event 2026-08-31T13:48:58Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_09

Audit cutoff: `2026-09-16T09:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_3960 | evidence_06: evidence/logs/structured_service_events_eu_west_20260918.log (USER_PROFILE/ABSENT; after cutoff) | Timestamp exclusion: available source/capture/observation is after cutoff. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_4902 | evidence_06: evidence/logs/structured_service_events_eu_west_20260918.log (SECURITY_AUDIT_LOG/PRESENT; after cutoff) | Timestamp exclusion: available source/capture/observation is after cutoff. |

## case_10

Audit cutoff: `2026-09-18T12:25:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_010 | activity_3595: dataset/system_activity.csv (DELETE_RECORD; event 2026-09-02T10:08:37Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_11

Audit cutoff: `2026-10-01T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |

## case_12

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |

## case_13

Audit cutoff: `2026-10-01T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |

## case_14

Audit cutoff: `2026-10-01T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |

## case_15

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |

## case_16

Audit cutoff: `2026-09-21T10:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |

## case_17

Audit cutoff: `2026-09-15T12:00:00Z`. The most recent update timestamp (10 Mar 2026 07:18 UTC) is later than the supplied manifest capture timestamp (2026-03-10T06:00:00Z).; A displayed lifecycle/event timestamp is later than manifest capture; both times are preserved without repair; The reference view does not explicitly establish removal of name, email, phone and email hash; fields not shown are not redaction proof

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | FINDING / REPORT_RESTORE_RISK | backup_service / backup_3245 | evidence_01: evidence/logs/service_events_ap_south_20260915.log; capture 2026-09-15T11:59:39Z; evidence_01: evidence/logs/service_events_ap_south_20260915.log (BACKUP_ARCHIVE/ACTIVE; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | REMEDIATION / BLOCK_RESTORE | backup_service / backup_3245 | evidence_01: evidence/logs/service_events_ap_south_20260915.log; capture 2026-09-15T11:59:39Z; evidence_01: evidence/logs/service_events_ap_south_20260915.log (BACKUP_ARCHIVE/ACTIVE; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_4092 | evidence_01: evidence/logs/service_events_ap_south_20260915.log (USER_PROFILE/ABSENT; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_1797 | evidence_01: evidence/logs/service_events_ap_south_20260915.log (SECURITY_AUDIT_LOG/PRESENT; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RESTORE_BLOCKED | backup_service / backup_3245 | evidence_01: evidence/logs/service_events_ap_south_20260915.log; capture 2026-09-15T11:59:39Z; evidence_01: evidence/logs/service_events_ap_south_20260915.log (BACKUP_ARCHIVE/ACTIVE; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |

## case_18

Audit cutoff: `2026-09-26T11:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_5521 | activity_3732: dataset/system_activity.csv (DELETE_RECORD; event 2026-09-09T09:52:26Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_6645 | No matching direct source row found; reference citation alone is not a join. | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_19

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| none | Exact content match | — | — | Check exact sequence independently for numbering/order. |

## case_20

Audit cutoff: `2026-09-26T11:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_5037 | activity_3734: dataset/system_activity.csv (DELETE_RECORD; event 2026-09-09T10:14:55Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_5569 | No matching direct source row found; reference citation alone is not a join. | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_21

Audit cutoff: `2026-09-15T12:00:00Z`. Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_6440 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_92: evidence/records/service_resource_export_20260915_114455.json (USER_PROFILE/ABSENT; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_3737 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (SECURITY_AUDIT_LOG/PRESENT; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_ANONYMIZED | analytics_platform / analytics_5335 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (ANALYTICS_PROFILE/ANONYMIZED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (ANALYTICS_PROFILE/ANONYMIZED; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_22

Audit cutoff: `2026-09-21T10:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_4990 | activity_3573: dataset/system_activity.csv (DELETE_RECORD; event 2026-09-01T09:12:11Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_23

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_410 | activity_3662: dataset/system_activity.csv (DELETE_RECORD; event 2026-09-05T11:10:55Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_4128 | evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff) | Timestamp exclusion: available source/capture/observation is after cutoff. |

## case_24

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_7095 | evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff) | Timestamp exclusion: available source/capture/observation is after cutoff. |

## case_25

Audit cutoff: `2026-09-15T12:00:00Z`. Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_3136 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_92: evidence/records/service_resource_export_20260915_114455.json (USER_PROFILE/ABSENT; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_451 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (SECURITY_AUDIT_LOG/PRESENT; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_ANONYMIZED | analytics_platform / analytics_1895 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (ANALYTICS_PROFILE/ANONYMIZED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (ANALYTICS_PROFILE/ANONYMIZED; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_26

Audit cutoff: `2026-09-15T12:00:00Z`. Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_5684 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (USER_PROFILE/PRESENT; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (USER_PROFILE/ABSENT; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_5416 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (SECURITY_AUDIT_LOG/PRESENT; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_REDACTED | support_platform / support_4715 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SUPPORT_MESSAGE/REDACTED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (SUPPORT_MESSAGE/REDACTED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_ANONYMIZED | analytics_platform / analytics_4566 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (ANALYTICS_PROFILE/ANONYMIZED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (ANALYTICS_PROFILE/ANONYMIZED; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_DATA_FLOW_DISABLED | integration_service / data_flow_6244 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (DATA_FLOW/DISABLED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (DATA_FLOW/DISABLED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RESTORE_BLOCKED | backup_service / backup_3120 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (BACKUP_ARCHIVE/BLOCKED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (BACKUP_ARCHIVE/BLOCKED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |

## case_27

Audit cutoff: `2026-09-15T12:00:00Z`. Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_3866 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (USER_PROFILE/PRESENT; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (USER_PROFILE/ABSENT; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_3830 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (SECURITY_AUDIT_LOG/PRESENT; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_REDACTED | support_platform / support_4707 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SUPPORT_MESSAGE/REDACTED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (SUPPORT_MESSAGE/REDACTED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_ANONYMIZED | analytics_platform / analytics_4574 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (ANALYTICS_PROFILE/ANONYMIZED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (ANALYTICS_PROFILE/ANONYMIZED; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_DATA_FLOW_DISABLED | integration_service / data_flow_2295 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (DATA_FLOW/DISABLED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (DATA_FLOW/DISABLED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RESTORE_BLOCKED | backup_service / backup_5970 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (BACKUP_ARCHIVE/BLOCKED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (BACKUP_ARCHIVE/BLOCKED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |

## case_28

Audit cutoff: `2026-09-15T12:00:00Z`. Complete subject audit lacks evidence of deleted primary account or compliant deletion tombstone

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_5482 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_92: evidence/records/service_resource_export_20260915_114455.json (USER_PROFILE/ABSENT; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_9265 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (SECURITY_AUDIT_LOG/PRESENT; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_REDACTED | support_platform / support_2351 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SUPPORT_MESSAGE/REDACTED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (SUPPORT_MESSAGE/REDACTED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RECORD_ANONYMIZED | analytics_platform / analytics_6077 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (ANALYTICS_PROFILE/ANONYMIZED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (ANALYTICS_PROFILE/ANONYMIZED; eligible) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_DATA_FLOW_DISABLED | integration_service / data_flow_2337 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (DATA_FLOW/DISABLED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (DATA_FLOW/DISABLED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |
| missing | VERIFICATION / VERIFY_RESTORE_BLOCKED | backup_service / backup_838 | evidence_92: evidence/records/service_resource_export_20260915_114455.json; capture 2026-09-15T11:44:55Z; evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (BACKUP_ARCHIVE/BLOCKED; after cutoff); evidence_92: evidence/records/service_resource_export_20260915_114455.json (BACKUP_ARCHIVE/BLOCKED; eligible) | Case held by another unresolved obligation; this independently supported step was not emitted as a partial case. |

## case_29

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_7012 | activity_3532: dataset/system_activity.csv (DELETE_RECORD; event 2026-08-30T11:06:57Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_3954 | evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff) | Timestamp exclusion: available source/capture/observation is after cutoff. |

## case_30

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_4163 | activity_3465: dataset/system_activity.csv (DELETE_RECORD; event 2026-08-27T10:55:42Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |
| missing | VERIFICATION / VERIFY_RECORD_PRESENT | security_service / audit_record_1707 | evidence_02: evidence/records/customer_data_snapshot_bundle_20260917.json (SECURITY_AUDIT_LOG/PRESENT; after cutoff) | Timestamp exclusion: available source/capture/observation is after cutoff. |

## case_31

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_4857 | evidence_51: evidence/records/customer_data_snapshot_bundle_20260915.json; capture 2026-09-15T12:00:00Z | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## case_32

Audit cutoff: `2026-09-15T12:00:00Z`. A row was returned; review the step-level discrepancies below.

| Difference | Phase / operation | System / resource | Citation / participant-visible source | Root cause / proof status |
| --- | --- | --- | --- | --- |
| missing | VERIFICATION / VERIFY_RECORD_ABSENT | account_service / account_8858 | activity_3685: dataset/system_activity.csv (DELETE_RECORD; event 2026-09-06T11:05:15Z; operation claim, not state proof) | Missing eligible subject-to-resource ownership edge; sanitized/absent rows cannot be assigned by suffix or adjacency. |

## Finance-register interpretation

The five sample-specific holds came from treating ordinary ORD business references as new privacy-resource observations. The source explicitly says Retain until, but supplies no privacy-resource category. They are now retained as non-destructive business constraints in source facts, without inventing a legal hold or generating deletion actions. Known account/analytics/support resources and uncertain primary privacy records still undergo ordinary policy and uncertainty checks.

## Completeness guard

A mandatory primary-account absence/tombstone anchor is not stated literally by the contract. It is an implementation safeguard for these whole-account deletion requests, preventing peripheral retained-audit evidence alone from proving all relevant copies treated. It is neither a necessary condition for every conceivable scoped audit nor sufficient proof of exhaustive discovery. The reviewed blocked account cases independently lack eligible exact resource ownership/state proof; removing the guard would emit a verdict without recovering their missing verification steps. Scoped engine fixtures deliberately do not require it. No guard was disabled to improve coverage.

## Minimal reproduction: case_01

Run `.venv/bin/python code/evaluation/review_mismatches.py --case case_01 --report /tmp/case_01_review.md`. This evaluation-only reproduction reads the public reference, then searches actual participant observations and activity for its resource; it does not pass that resource to the predictor.

The reference requires account_001 / evidence_54. The SQL snapshot can establish scoped absence only after that account key is grounded. The participant activity names account_001 but does not identify the request subject; the subject identity snapshot supplies user_01, email, phone and hash without an account key. No eligible current/historical identifier bridges them. user_01 -> account_001 would be a suffix assumption, not an evidence join. Required missing proof: an eligible catalog/API/record association between the subject and account_001, or an authoritative keyed negative lookup containing both. The expected key cannot currently be grounded independently from supplied participant evidence. A negative snapshot alone does not manufacture that missing key.

This is a minimal evidence-consistency reproduction, not a generator/hidden-answer investigation. Participant inputs remain unchanged.
