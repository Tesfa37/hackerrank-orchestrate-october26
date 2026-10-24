# case_07 attachment source-scope correction

The implementation previously interpreted the body of an uploaded customer PDF as a separate live support message. This was a demonstrated source-scope error, independently of the public expected answer.

## Participant-visible proof

`evidence_58`, `evidence/documents/delivery_correction_attachment.pdf`, captured `2026-09-12T07:30:00Z`:

- Page 1 is titled `DELIVERY ADDRESS CORRECTION REQUEST`, prints `Support reference CS-4827 / support_001`, and contains the customer's original address-correction request and direct identifiers.
- Page 2 repeats that document title and says `Continued - Attachment properties and upload history`. It identifies `file delivery_address_correction.pdf`, `ticket CS-4827`, `uploader customer`, a checksum prefix, and the capture time.
- These facts establish the uploaded file and its body. They do not independently establish the current contents of a separate live ticket at the audit cutoff.

No account key, ticket key or attachment key was derived from a user-ID suffix. `support_001` is printed in full in the PDF. The file and ticket names are joined only within the explicitly continued document, using its quoted parent-ticket reference. No activity claim or expected answer supplies an identifier.

## Implementation and safeguards

Source-fact hydration now combines that body and its unique attachment-properties section into one `SUPPORT_ATTACHMENT` observation. It retains the body identifiers and all raw provider records, records a source-scope correction, and applies the supplied attachment `DELETE` rule. It no longer emits a separate `SUPPORT_MESSAGE` observation or an unsupported live-ticket redaction plan from that body.

The generic correction requires a PDF, one attachment, a continued attachment-properties section, explicit customer-upload provenance, the same document title, a quoted matching parent reference, and exactly one fully quoted technical support key. Ambiguous files or keys, unquoted keys, unknown attachment state, independent live-ticket views, and unrelated references are not merged. Manifest capture and cutoff eligibility are preserved. The immutable cached provider response is unchanged.

Synthetic regression fixtures verify body identifiers remain attributable to the attachment, its policy produces finding/delete/verify steps, future captures remain ineligible, and the ambiguous/independent cases do not receive this correction. No expected sample data is used by these fixtures.

## Measured effect and remaining mismatch

Three unsupported live-ticket steps disappear. The sample still has one missing account verification whose eligible ownership link is absent, and three additional steps for `object_storage/object_19` in `evidence_46`. The object browser prints a different filename, `delivery_confirmation_19.pdf`; no supplied link proves it is the same physical file as the PDF upload. That object remains subject to its independently established policy. It is not discarded to match the public sample.

Across all 32 samples, coverage remains 23/32 and exact sequence remains 8/32. Content matches remain 139; predicted steps fall from 145 to 142, so precision improves from 95.86% to 97.89%, recall stays 72.02%, F1 improves from 82.25% to 82.99%, and aligned field accuracy improves from 67.70% to 68.73%.

The full run still resolves 419/518 with 99 holds. The two confirmed organizer exclusions produce a separate 418/516 coverage view with 98 holds, rather than changing prediction behavior. No new API calls were made; the paid budget remains $0.
