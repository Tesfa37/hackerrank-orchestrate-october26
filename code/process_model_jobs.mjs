/** Optional portable transport for the exact REST jobs prepared by the Python CLI. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

const MODEL = 'gemini-3.5-flash-lite';
const VERSION = 'deletion-audit-extraction-v2';
const retryable = new Set([429, 500, 502, 503, 504]);

function quotaMetadata(payload, headers) {
  const result = {};
  const details = payload?.error?.details ?? payload?.details;
  const violations = [];
  for (const detail of Array.isArray(details) ? details : []) {
    if (detail?.['@type'] === 'type.googleapis.com/google.rpc.QuotaFailure') {
      for (const item of Array.isArray(detail.violations) ? detail.violations : []) {
        const safe = {};
        for (const field of ['quotaMetric', 'quotaId']) if (typeof item?.[field] === 'string' && /^[A-Za-z][A-Za-z0-9._:/-]{0,199}$/.test(item[field])) safe[field] = item[field];
        if (Object.keys(safe).length && !violations.some(other => JSON.stringify(other) === JSON.stringify(safe))) violations.push(safe);
      }
    } else if (detail?.['@type'] === 'type.googleapis.com/google.rpc.RetryInfo' && typeof detail.retryDelay === 'string' && /^[0-9]{1,12}(?:\.[0-9]{1,9})?s$/.test(detail.retryDelay)) {
      result.retryInfoSeconds = Math.max(result.retryInfoSeconds ?? 0, Number(detail.retryDelay.slice(0, -1)));
    }
  }
  if (violations.length) {
    result.violations = violations;
    const names = violations.flatMap(item => Object.values(item)).join(' ').toLowerCase();
    result.quotaScope = ['perday', 'per_day', 'per-day', 'daily'].some(token => names.includes(token)) ? 'daily' : 'rate';
  }
  const retryAfter = headers?.get?.('Retry-After');
  if (typeof retryAfter === 'string') {
    if (/^[0-9]{1,12}(?:\.[0-9]{1,9})?$/.test(retryAfter.trim())) result.retryAfterSeconds = Number(retryAfter.trim());
    else {
      const reset = Date.parse(retryAfter);
      if (Number.isFinite(reset)) {
        result.retryAfterAt = new Date(reset).toISOString();
        result.retryAfterSeconds = Math.max(0, (reset - Date.now()) / 1000);
      }
    }
  }
  const delays = ['retryInfoSeconds', 'retryAfterSeconds'].filter(field => Object.hasOwn(result, field)).map(field => result[field]);
  if (delays.length) result.retryDelaySeconds = Math.max(...delays);
  return result;
}

function httpFailure(status, metadata) {
  let message = `Gemini HTTP ${status}`;
  if (metadata.quotaScope === 'daily') message += '; daily quota exhausted; stopped without retrying';
  if (metadata.violations?.length) message += '; quota: ' + metadata.violations.map(item => ['quotaMetric', 'quotaId'].filter(field => item[field]).map(field => item[field]).join('/')).join(', ');
  if (Object.hasOwn(metadata, 'retryDelaySeconds')) message += `; server retry delay ${metadata.retryDelaySeconds} seconds`;
  if (metadata.retryAfterAt) message += ` (reset ${metadata.retryAfterAt})`;
  const error = new Error(message + '; no paid fallback attempted.');
  error.quotaMetadata = metadata;
  error.httpStatus = status;
  return error;
}

function ordered(value) {
  if (Array.isArray(value)) return value.map(ordered);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(key => [key, ordered(value[key])]));
  return value;
}

function validateSchema(value, schema, location = 'response') {
  const kind = schema.type;
  const types = {object: value !== null && typeof value === 'object' && !Array.isArray(value), array: Array.isArray(value), string: typeof value === 'string', boolean: typeof value === 'boolean', integer: Number.isInteger(value), number: typeof value === 'number' && Number.isFinite(value), null: value === null};
  if (kind && !types[kind]) throw new Error('Invalid structured extraction type at ' + location);
  if (schema.enum && !schema.enum.includes(value)) throw new Error('Invalid structured extraction value at ' + location);
  if (types.object) {
    const properties = schema.properties ?? {};
    if ((schema.required ?? []).some(key => !Object.hasOwn(value, key)) || (schema.additionalProperties === false && Object.keys(value).some(key => !Object.hasOwn(properties, key)))) throw new Error('Invalid structured extraction fields at ' + location);
    for (const [key, child] of Object.entries(value)) if (properties[key]) validateSchema(child, properties[key], location + '.' + key);
  } else if (types.array) {
    if (value.length < (schema.minItems ?? 0) || value.length > (schema.maxItems ?? Infinity)) throw new Error('Invalid structured extraction item count at ' + location);
    for (const [index, child] of value.entries()) validateSchema(child, schema.items ?? {}, location + '[' + index + ']');
  } else if (types.string) {
    if (value.trim().length < (schema.minLength ?? 0)) throw new Error('Empty structured extraction value at ' + location);
    if (schema.pattern && !new RegExp(schema.pattern).test(value)) throw new Error('Invalid structured extraction pattern at ' + location);
    if (schema.format === 'date-time' && (!/(?:Z|[+-]\d\d:\d\d)$/.test(value) || !Number.isFinite(Date.parse(value)))) throw new Error('Invalid observation timestamp at ' + location);
  }
}

function validateResponse(raw, schema) {
  const candidates = raw?.candidates;
  if (!Array.isArray(candidates) || candidates.length !== 1 || candidates[0]?.finishReason !== 'STOP') throw new Error('Gemini extraction is blocked, truncated, or incomplete.');
  const parts = candidates[0]?.content?.parts;
  if (!Array.isArray(parts)) throw new Error('Gemini returned invalid extraction content.');
  const text = parts.filter(part => !part.thought).map(part => part.text ?? '').join('');
  let parsed;
  try { parsed = JSON.parse(text); } catch { throw new Error('Gemini returned no valid structured extraction.'); }
  validateSchema(parsed, schema);
  const expected = schema.properties?.requests?.items?.properties?.case_id?.enum;
  if (expected) {
    const actual = new Set(parsed.requests.map(item => item.case_id));
    if (parsed.requests.length !== expected.length || actual.size !== expected.length || expected.some(id => !actual.has(id))) throw new Error('Intent response did not cover each input exactly once.');
  }
  if (schema.properties?.records?.items?.properties?.reference_kind) validateReinspection(parsed);
}

function validateReinspection(result) {
  if (result.review_complete !== true) throw new Error('Artifact reinspection did not complete; partial source facts cannot mark it ready.');
  const stableNames = new Set(['userid', 'subjectref', 'subjectreference', 'customerreference', 'customerkey', 'stablereference']);
  const directNames = new Set(['name', 'fullname', 'displayname', 'email', 'phone', 'emailhash', 'owneremail', 'ownerphone', 'customeremail', 'requesteremail', 'requesterphone', 'requestername']);
  for (const [index, record] of result.records.entries()) {
    if (['STABLE_SUBJECT_REFERENCE', 'UNRESOLVED'].includes(record.reference_kind) && record.resource_id) throw new Error('A subject/context reference is not a canonical resource ID.');
    if (['RESOURCE_ID', 'BUSINESS_ALIAS'].includes(record.reference_kind) && (!record.resource_id || record.resource_id !== record.literal_reference)) throw new Error('Reviewed resource IDs must match their literal artifact reference.');
    if (record.time_basis === 'CAPTURE_TIME' && Date.parse(record.observed_at) !== Date.parse(result.captured_at)) throw new Error('Event or modified timestamps cannot replace the capture observation time.');
    if (record.last_modified_at) validateSchema(record.last_modified_at, {type:'string', format:'date-time'}, `response.records[${index}].last_modified_at`);
    for (const [eventIndex, event] of record.events.entries()) if (event.timestamp) validateSchema(event.timestamp, {type:'string', format:'date-time'}, `response.records[${index}].events[${eventIndex}].timestamp`);
    const visible = [];
    for (const field of record.stored_fields) {
      const name = field.field_name.toLowerCase().replace(/[^a-z0-9]/g, '');
      if (stableNames.has(name) && field.identifier_role === 'DIRECT_IDENTIFIER') throw new Error('A stable internal user reference is not a prohibited direct identifier.');
      const businessObjectName = name === 'name' && record.reference_kind === 'BUSINESS_ALIAS' && ['SUPPORT_ATTACHMENT', 'USER_EXPORT'].includes(record.record_type) && field.value === record.literal_reference && field.source_quote.trim() === field.value;
      if (directNames.has(name) && field.visibility === 'VALUE' && field.identifier_role !== 'DIRECT_IDENTIFIER' && !businessObjectName) throw new Error('A visible direct identifier cannot be reclassified as a stable/context field.');
      if (field.visibility === 'NOT_SHOWN' && field.value) throw new Error('An undisplayed field cannot have an invented stored value.');
      if (field.visibility === 'BLANK' && field.value && (!['—', '–', '-'].includes(field.value) || !new RegExp('(?:^|[\\s:])' + field.value + '(?:$|\\s)').test(field.source_quote.trim()))) throw new Error('A blank field must be empty or an exactly quoted display blank marker.');
      if (field.identifier_role === 'DIRECT_IDENTIFIER' && field.visibility === 'VALUE') visible.push(JSON.stringify([field.field_name, field.value, field.source_quote]));
    }
    const declared = record.direct_identifiers_visible.map(field => JSON.stringify([field.field_name, field.value, field.source_quote]));
    if (JSON.stringify(visible.sort()) !== JSON.stringify(declared.sort())) throw new Error('Visible direct identifiers must agree with the reviewed stored fields.');
    if (record.direct_fields_coverage === 'partial_view' && record.field_coverage === 'COMPLETE') throw new Error('A partial identifier view cannot establish complete field coverage.');
  }
}

async function readKey(root) {
  if (process.env.GEMINI_API_KEY) return process.env.GEMINI_API_KEY;
  let text;
  try { text = await fs.readFile(path.join(root, '.env'), 'utf8'); }
  catch (error) { if (error.code !== 'ENOENT') throw new Error('Cannot read the ignored credential file.'); }
  const entry = text?.replace(/^\uFEFF/, '').split(/\r?\n/).find(line => line.trim().startsWith('GEMINI_API_KEY='));
  const key = entry?.split('=').slice(1).join('=').trim().replace(/^['"]|['"]$/g, '');
  if (!key) throw new Error('GEMINI_API_KEY is not configured.');
  return key;
}

async function atomicJSON(target, value) {
  const temporary = target + '.' + crypto.randomUUID() + '.tmp';
  try {
    await fs.writeFile(temporary, JSON.stringify(value), {encoding: 'utf8', mode: 0o600, flag: 'wx'});
    await fs.rename(temporary, target);
  } finally { await fs.unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
}

export async function processJobs(root, {limit = Infinity, onProgress = () => {}} = {}) {
  root = path.resolve(root);
  if (limit !== Infinity && (!Number.isInteger(limit) || limit < 0)) throw new Error('Job limit must be a nonnegative integer.');
  const jobs = JSON.parse(await fs.readFile(path.join(root, '.cache', 'model_jobs.json'), 'utf8'));
  if (!Array.isArray(jobs)) throw new Error('Prepared jobs must be an array.');
  const summary = [];
  let key;
  for (const job of jobs) {
    if (summary.length >= limit) break;
    if (job.model !== MODEL || job.version !== VERSION) throw new Error('No alternate model, paid fallback, or unsupported request version is permitted.');
    const signature = JSON.stringify(ordered({model: job.model, version: job.version, task: job.task, body: job.body}));
    const expectedKey = crypto.createHash('sha256').update(signature, 'utf8').digest('hex');
    if (job.key !== expectedKey) throw new Error('Prepared request signature is invalid.');
    if (job.repair_of !== undefined && (!Array.isArray(job.repair_of) || job.repair_of.length !== 1 || !job.repair_of.every(key => /^[a-f0-9]{64}$/.test(key)))) throw new Error('Invalid one-stage repair provenance.');
    const expectedDirectory = path.resolve(root, '.cache', 'gemini');
    const target = path.resolve(job.cache_file);
    if (path.dirname(target) !== expectedDirectory || path.basename(target) !== job.key + '.json') throw new Error('Invalid response cache destination.');
    const schema = job.body?.generationConfig?.responseFormat?.text?.schema;
    if (!schema) throw new Error('Prepared extraction must include a response schema.');
    try {
      const stat = await fs.lstat(target);
      if (stat.isSymbolicLink() || !stat.isFile()) throw new Error('Response cache is not a regular file.');
      const cached = JSON.parse(await fs.readFile(target, 'utf8'));
      if (['key', 'model', 'task', 'version'].some(field => cached[field] !== job[field])) throw new Error('Extraction cache metadata does not match its request.');
      validateResponse(cached.response, schema);
      continue;
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
    key ??= await readKey(root);
    const attempts = [];
    let data;
    for (let attempt = 0; attempt < 3; attempt++) {
      const record = {attempt_id: crypto.randomUUID(), key: job.key, task: job.task, model: job.model, created_at: new Date().toISOString(), usage: {}};
      let response;
      try {
        response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${job.model}:generateContent`, {
          method: 'POST', headers: {'x-goog-api-key': key, 'Content-Type': 'application/json'},
          body: JSON.stringify(job.body), signal: AbortSignal.timeout(90000)
        });
        record.status = response.ok ? 'received' : `HTTP_${response.status}`;
        try { data = await response.json(); }
        catch { throw new Error('Gemini returned an invalid response; no result was cached.'); }
        record.usage = data.usageMetadata ?? {};
        if (!response.ok) {
          const metadata = quotaMetadata(data, response.headers);
          if (Object.keys(metadata).length) record.quota = metadata;
        }
      } catch (error) {
        record.status ??= 'network_error';
        throw new Error(record.status === 'network_error' ? 'Gemini network access failed; no paid fallback attempted.' : 'Gemini returned an invalid response; no result was cached.');
      } finally {
        attempts.push(record);
        await fs.mkdir(path.join(root, '.cache'), {recursive: true});
        await fs.appendFile(path.join(root, '.cache', 'gemini_attempts.jsonl'), JSON.stringify(record) + '\n', 'utf8');
      }
      if (response.ok) break;
      const metadata = record.quota ?? {};
      const delay = metadata.retryDelaySeconds ?? 3 * (attempt + 1);
      if (!retryable.has(response.status) || attempt === 2 || metadata.quotaScope === 'daily' || delay > 60) throw httpFailure(response.status, metadata);
      await new Promise(resolve => setTimeout(resolve, delay * 1000));
    }
    try { validateResponse(data, schema); }
    catch (error) {
      const rejectedDirectory = path.join(root, '.cache', 'rejected');
      await fs.mkdir(rejectedDirectory, {recursive: true});
      const rejected = path.join(rejectedDirectory, job.key + '.' + crypto.randomUUID() + '.json');
      await atomicJSON(rejected, {status: 'rejected', key: job.key, model: job.model, version: job.version, task: job.task, created_at: new Date().toISOString(), reason: error.message, response: data, attempts});
      throw new Error(error.message + '; received response quarantined at ' + path.relative(root, rejected));
    }
    const result = {key: job.key, model: job.model, version: job.version, task: job.task, created_at: new Date().toISOString(), response: data, attempts, ...(job.repair_of ? {repair_of: job.repair_of, repair_stage: 1} : {})};
    await fs.mkdir(expectedDirectory, {recursive: true});
    await atomicJSON(target, result);
    const item = {task: job.task, key: job.key, usage: data.usageMetadata, attempts: attempts.length};
    summary.push(item); onProgress(item);
  }
  return summary;
}

if (typeof process !== 'undefined' && process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
  const result = await processJobs(root, {onProgress: item => console.log(JSON.stringify({task: item.task, usage: item.usage, attempts: item.attempts}))});
  console.log(JSON.stringify({completed: result.length}));
}
