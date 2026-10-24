/** Optional portable transport for the exact REST jobs prepared by the Python CLI. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export async function processJobs(root, {limit = Infinity, onProgress = () => {}} = {}) {
  const envText = await fs.readFile(path.join(root, '.env'), 'utf8');
  const entry = envText.replace(/^\uFEFF/, '').split(/\r?\n/).find(line => line.trim().startsWith('GEMINI_API_KEY='));
  const key = entry?.split('=').slice(1).join('=').trim().replace(/^['"]|['"]$/g, '');
  if (!key) throw new Error('GEMINI_API_KEY is not configured.');
  const jobs = JSON.parse(await fs.readFile(path.join(root, '.cache', 'model_jobs.json'), 'utf8'));
  const summary = [];
  for (const job of jobs.slice(0, limit)) {
    if (job.model !== 'gemini-3.5-flash-lite') throw new Error('No paid or alternate model fallback is permitted.');
    const expectedDirectory = path.resolve(root, '.cache', 'gemini');
    if (path.dirname(path.resolve(job.cache_file)) !== expectedDirectory) throw new Error('Invalid response cache destination.');
    try { await fs.access(job.cache_file); continue; } catch {}
    let response;
    for (let attempt = 0; attempt < 3; attempt++) {
      response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${job.model}:generateContent`, {
        method: 'POST', headers: {'x-goog-api-key': key, 'Content-Type': 'application/json'},
        body: JSON.stringify(job.body), signal: AbortSignal.timeout(90000)
      });
      if (response.ok || ![429, 500, 502, 503, 504].includes(response.status) || attempt === 2) break;
      await new Promise(resolve => setTimeout(resolve, 3000 * (attempt + 1)));
    }
    const data = await response.json();
    if (!response.ok) throw new Error(`Gemini HTTP ${response.status}; no paid fallback attempted.`);
    const candidate = data.candidates?.[0];
    if (candidate?.finishReason !== 'STOP') throw new Error(`Extraction not complete: ${candidate?.finishReason ?? 'no candidate'}`);
    const result = {key: job.key, model: job.model, task: job.task, created_at: new Date().toISOString(), response: data};
    await fs.mkdir(expectedDirectory, {recursive: true});
    await fs.writeFile(job.cache_file + '.tmp', JSON.stringify(result), 'utf8');
    await fs.rename(job.cache_file + '.tmp', job.cache_file);
    const item = {task: job.task, key: job.key, usage: data.usageMetadata};
    summary.push(item); onProgress(item);
  }
  return summary;
}

if (typeof process !== 'undefined' && process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
  const result = await processJobs(root, {onProgress: item => console.log(JSON.stringify({task: item.task, usage: item.usage}))});
  console.log(JSON.stringify({completed: result.length}));
}
