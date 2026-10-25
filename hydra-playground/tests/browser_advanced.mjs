// Advanced UI smoke test. Run only after the verified gallery is published and
// the local computation slot is free. This starts ONE Deep Hybrid proof search
// and ONE Research Hybrid job that it cancels after worker-emitted progress.
// Use only after confirming the isolated-Chrome fallback is currently allowed.
// No existing browser profile, cookies, credentials, tabs, or unrelated job is used.
//
// HYDRA_TEST_ADVANCED_LIVE=1 HYDRA_TEST_URL=http://127.0.0.1:8767/ \
//   HYDRA_TEST_OUTPUT=output/hydra-advanced-browser-new-run \
//   node hydra-playground/tests/browser_advanced.mjs

import {spawn} from 'node:child_process';
import {mkdtemp, readFile, mkdir, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import assert from 'node:assert/strict';

assert.equal(process.env.HYDRA_TEST_ADVANCED_LIVE, '1',
  'This test starts two bounded local jobs; explicitly set HYDRA_TEST_ADVANCED_LIVE=1.');
const address = process.env.HYDRA_TEST_URL || 'http://127.0.0.1:8767/';
const target = new URL(address);
assert(target.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(target.hostname),
  'Only the local Hydra app may be tested.');
assert(!target.username && !target.password && !target.search && !target.hash && target.pathname === '/',
  'Use the local app root without credentials, query parameters, or fragments.');
const started = new Date().toISOString();
const output = resolve(process.env.HYDRA_TEST_OUTPUT ||
  `output/hydra-advanced-browser-${started.replaceAll(':', '-').replaceAll('.', '-')}`);
await mkdir(output, {recursive: true});
// Refuse to overwrite evidence from an earlier invocation, even if the caller
// supplies a previously used output directory.
await writeFile(join(output, 'browser-advanced-started.json'),
  JSON.stringify({started_at: started, url: address, expected_search_jobs: 2}, null, 2) + '\n', {flag: 'wx'});

const profile = await mkdtemp(join(tmpdir(), 'hydra-advanced-browser-'));
const chrome = spawn(process.env.HYDRA_TEST_CHROME ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-background-networking', '--disable-component-update', '--disable-sync',
  '--disable-extensions', '--disable-features=MediaRouter,OptimizationHints,Translate',
  '--metrics-recording-only', '--remote-debugging-address=127.0.0.1',
  '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank',
], {detached: true, stdio: ['ignore', 'ignore', 'ignore']});
let launchError, socket, serial = 0, closing = false, csrfToken = '';
chrome.once('error', error => { launchError = error; });
const pending = new Map(), requests = [], byRequest = new Map(), ownedJobs = new Map();
const pageErrors = [], captureErrors = [], checks = [], screenshots = [], evidence = {};
const deadline = Date.now() + 300_000;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const terminal = state => ['completed', 'failed', 'cancelled'].includes(state);

async function until(fn, timeout = 15_000, label = 'UI state') {
  const end = Math.min(Date.now() + timeout, deadline);
  let last;
  while (Date.now() < end) {
    try { last = await fn(); if (last) return last; }
    catch (error) { last = error.message; }
    await delay(100);
  }
  throw new Error(`${label} timed out: ${String(last)}`);
}

function call(method, params = {}) {
  if (socket?.readyState !== WebSocket.OPEN) return Promise.reject(new Error('Isolated browser connection is closed.'));
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, closing ? 5_000 : 20_000);
    pending.set(id, {
      resolve: value => { clearTimeout(timer); resolve(value); },
      reject: error => { clearTimeout(timer); reject(error); },
    });
    socket.send(JSON.stringify({id, method, params}));
  });
}

async function evaluate(expression) {
  const result = await call('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text + ': ' +
    (result.exceptionDetails.exception?.description || ''));
  return result.result?.value;
}
const text = id => evaluate(`document.getElementById(${JSON.stringify(id)}).textContent`);
const value = id => evaluate(`document.getElementById(${JSON.stringify(id)}).value`);
const click = id => evaluate(`document.getElementById(${JSON.stringify(id)}).click()`);
async function fill(id, supplied) {
  await evaluate(`(() => { const e=document.getElementById(${JSON.stringify(id)}); e.value=${JSON.stringify(supplied)}; e.dispatchEvent(new Event('input',{bubbles:true})); })()`);
}
async function select(id, supplied) {
  await evaluate(`(() => { const e=document.getElementById(${JSON.stringify(id)}); const option=[...e.options].find(o=>o.value===${JSON.stringify(String(supplied))}); if(!option || option.disabled || e.disabled)throw new Error('Unavailable selection: '+e.id); e.value=option.value; e.dispatchEvent(new Event('change',{bubbles:true})); })()`);
}
const searchRequests = () => requests.filter(item => item.method === 'POST' && item.path === '/api/search');
const replayRequests = () => requests.filter(item => item.method === 'POST' && item.path === '/api/replay');
const postCount = () => requests.filter(item => item.method === 'POST').length;
const latest = path => requests.findLast(item => item.path === path && item.payload);
const writeJSON = (name, payload) => writeFile(join(output, name), JSON.stringify(payload, null, 2) + '\n');

// Observe the real browser network requests rather than replacing fetch or the
// application state. Never retain request headers or publish the CSRF token.
async function captureBody(entry) {
  try {
    const response = await call('Network.getResponseBody', {requestId: entry.requestId});
    const raw = response.base64Encoded ? Buffer.from(response.body, 'base64').toString('utf8') : response.body;
    assert(Buffer.byteLength(raw) <= 8 * 1024 * 1024, 'An observed API response exceeded the test evidence bound.');
    const payload = JSON.parse(raw);
    if (entry.path === '/api/status') {
      if (typeof payload.csrf_token === 'string') csrfToken = payload.csrf_token;
      delete payload.csrf_token;
    }
    entry.payload = payload;
    if (entry.method === 'POST' && entry.path === '/api/search' && /^[0-9a-f]{32}$/.test(payload.job_id || '')) {
      ownedJobs.set(payload.job_id, {id: payload.job_id, request: entry.body, state: payload.state});
      entry.job_id = payload.job_id;
    }
    if (payload.job && ownedJobs.has(payload.job.id)) {
      ownedJobs.set(payload.job.id, {...ownedJobs.get(payload.job.id), ...payload.job});
    }
  } catch (error) {
    if (!closing && captureErrors.length < 32) captureErrors.push({path: entry.path, error: error.message});
  }
}

function receive(message) {
  const item = pending.get(message.id);
  if (item) {
    pending.delete(message.id);
    if (message.error) item.reject(new Error(JSON.stringify(message.error)));
    else item.resolve(message.result);
    return;
  }
  const event = message.params || {};
  if (message.method === 'Runtime.exceptionThrown' && pageErrors.length < 32) {
    pageErrors.push({kind: 'uncaught', text: event.exceptionDetails?.exception?.description || event.exceptionDetails?.text});
  } else if (message.method === 'Runtime.consoleAPICalled' && event.type === 'error' && pageErrors.length < 32) {
    pageErrors.push({kind: 'console.error', text: event.args?.map(arg => arg.value ?? arg.description ?? '').join(' ').slice(0, 2048)});
  } else if (message.method === 'Network.requestWillBeSent') {
    const url = new URL(event.request.url);
    if (url.origin !== target.origin || !url.pathname.startsWith('/api/')) return;
    if (requests.length >= 1024) { captureErrors.push({error: 'Too many observed API requests.'}); return; }
    let body;
    try { if (event.request.postData) body = JSON.parse(event.request.postData); }
    catch { captureErrors.push({path: url.pathname, error: 'Unreadable API request body.'}); }
    const entry = {requestId: event.requestId, path: url.pathname, method: event.request.method, body};
    requests.push(entry); byRequest.set(event.requestId, entry);
  } else if (message.method === 'Network.responseReceived') {
    const entry = byRequest.get(event.requestId);
    if (entry) entry.http_status = event.response.status;
  } else if (message.method === 'Network.loadingFinished') {
    const entry = byRequest.get(event.requestId);
    if (entry) void captureBody(entry);
  } else if (message.method === 'Network.loadingFailed') {
    const entry = byRequest.get(event.requestId);
    if (entry && !closing) captureErrors.push({path: entry.path, error: event.errorText});
  }
}

async function ready() {
  await until(() => evaluate("!document.getElementById('theorem').disabled && !document.getElementById('search-profile').disabled"), 15_000, 'idle controls');
}
async function waitResult(label, timeout = 60_000) {
  await until(() => evaluate("['Kernel verified','No proof found','Step rejected','Search stopped','Search cancelled','Could not start','Check failed','Connection lost'].includes(document.getElementById('result-badge').textContent) && !document.getElementById('theorem').disabled"), timeout, label);
  assert.equal(await text('result-badge'), 'Kernel verified', `${label}: ${await text('page-error')} ${await text('result-caption')}`);
}
async function assertCleared() {
  assert.equal(await text('result-badge'), 'Not checked');
  assert.equal(await text('run-origin'), 'NO RESULT');
  assert.equal(await evaluate("document.getElementById('download-run').disabled && document.getElementById('branch-panel').hidden && document.getElementById('run-details').hidden"), true);
  assert.equal(await evaluate("document.querySelectorAll('#trace .trace-step').length"), 0);
}
async function galleryAction(id, action) {
  await evaluate(`(() => { const card=[...document.querySelectorAll('#showcase-cases article')].find(node=>node.dataset.caseId===${JSON.stringify(id)}); const button=card?.querySelector('button[data-showcase-action="${action}"]'); if(!button || button.disabled)throw new Error('Gallery action is unavailable'); button.click(); })()`);
}
async function screenshot(name, section) {
  if (section) await evaluate(`document.querySelector(${JSON.stringify(section)}).scrollIntoView({block:'start',behavior:'instant'})`);
  await call('Runtime.evaluate', {expression: 'new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))', awaitPromise: true});
  const layout = await evaluate("({width:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth})");
  assert(layout.scroll <= layout.width + 1 && layout.body <= layout.width + 1, `Horizontal overflow in ${name}: ${JSON.stringify(layout)}`);
  const shot = await call('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false});
  await writeFile(join(output, name), Buffer.from(shot.data, 'base64'));
  screenshots.push(name);
}
async function profilesMatch(name, profiles) {
  await select('search-profile', name);
  const controls = await evaluate("Object.fromEntries(['call-budget','beam-width'].map(id=>[id,{value:document.getElementById(id).value,options:[...document.getElementById(id).options].map(o=>Number(o.value)),disabled:document.getElementById(id).disabled}]))");
  assert.deepEqual(controls['call-budget'].options, profiles[name].model_calls);
  assert.deepEqual(controls['beam-width'].options, profiles[name].beams);
  assert.equal(controls['call-budget'].disabled, false);
  assert.equal(controls['beam-width'].disabled, false);
  assert(profiles[name].model_calls.includes(Number(controls['call-budget'].value)));
  assert(profiles[name].beams.includes(Number(controls['beam-width'].value)));
  return {...controls, description: await text('profile-description')};
}
async function assertStepSources(result) {
  const trace = result.trace.filter(row => typeof row.tactic === 'string');
  const expected = trace.map((row, i) => row.origin?.source || result.search?.provenance?.[i]?.source);
  assert(expected.length > 0 && expected.every(source => ['heuristic', 'model', 'vampire'].includes(source)));
  assert.deepEqual(await evaluate("[...document.querySelectorAll('#trace .trace-button code')].map(node=>node.textContent)"), result.commands);
  assert.deepEqual(await evaluate("[...document.querySelectorAll('#trace .step-origin')].map(node=>node.dataset.source)"), expected);
  assert.equal(await evaluate("document.querySelectorAll('#trace .step-reason').length"), expected.length);
  const counts = expected.reduce((all, source) => ({...all, [source]: (all[source] || 0) + 1}), {});
  assert.deepEqual(result.proof_sources, counts);
  assert.equal(await text('metric-calls'), String(result.search.model_calls));
  assert.equal(await text('metric-vampire'), String(result.search.vampire_calls));
  assert.equal(await text('metric-states'), String(result.search.states_expanded));
  assert.equal(await text('metric-attempts'), String(result.search.tactic_attempts));
  return counts;
}
async function assertRenderedGoals(snapshots) {
  assert(Array.isArray(snapshots) && snapshots.every(raw => typeof raw === 'string'),
    'Exact native goal snapshots are required for trace navigation.');
  const expected = snapshots.map((raw, index) => {
    const cut = raw.indexOf('⊢');
    // The UI separates the native snapshot at its turnstile and trims only
    // the boundaries. Preserve every internal character and line break.
    return {label: `GOAL ${index + 1}`, context: cut < 0 ? '' : raw.slice(0, cut).trim(),
      turnstile: '⊢', target: cut < 0 ? raw : raw.slice(cut + 1).trim()};
  });
  const rendered = await evaluate(`Array.from(document.querySelectorAll('#goals > .goal-card'), card => {
    const line = card.querySelector(':scope > .goal-target');
    const spans = line ? Array.from(line.children) : [];
    if (spans.length !== 2 || spans.some(node => node.tagName !== 'SPAN') || !spans[0].classList.contains('turnstile')) {
      throw new Error('Unexpected rendered native goal structure');
    }
    return {label: card.querySelector(':scope > .goal-label')?.textContent,
      context: card.querySelector(':scope > .goal-context')?.textContent || '',
      turnstile: spans[0].textContent, target: spans[1].textContent};
  })`);
  assert.deepEqual(rendered, expected);
  assert.equal(await text('goal-count'), `${snapshots.length} OPEN GOAL${snapshots.length === 1 ? '' : 'S'}`);
  return rendered;
}
async function apiRead(path) {
  return evaluate(`fetch(${JSON.stringify(path)},{cache:'no-store',credentials:'same-origin'}).then(async response=>{const data=await response.json();if(!response.ok || data.ok===false)throw new Error(data.error || 'API request failed');if(data.csrf_token)delete data.csrf_token;return data;})`);
}

// Direct local cleanup survives loss of the temporary browser connection. It
// can cancel only IDs acknowledged by this page's own POST /api/search calls.
async function cleanupOwnedJobs() {
  const cleaned = {owned_job_ids: [...ownedJobs.keys()], jobs: [], slot_released: null, errors: []};
  cleaned.unacknowledged_search_requests = searchRequests().filter(item => !item.job_id).length;
  if (cleaned.unacknowledged_search_requests) {
    cleaned.errors.push('A search acknowledgement was not captured; no unidentified or unrelated job was cancelled.');
  }
  async function local(path, body) {
    const headers = {Accept: 'application/json', Origin: target.origin};
    if (body !== undefined) { headers['Content-Type'] = 'application/json'; headers['X-CSRF-Token'] = csrfToken; }
    const response = await fetch(new URL(path, target), {method: body === undefined ? 'GET' : 'POST', headers,
      ...(body === undefined ? {} : {body: JSON.stringify(body)}), redirect: 'error', signal: AbortSignal.timeout(5_000)});
    const payload = await response.json();
    if (!response.ok || payload.ok === false) throw new Error(`Owned cleanup ${path}: HTTP ${response.status}`);
    return payload;
  }
  try {
    if (!ownedJobs.size) return cleaned;
    const status = await local('/api/status'); csrfToken = status.csrf_token || csrfToken;
    for (const id of ownedJobs.keys()) {
      let job = (await local(`/api/jobs/${id}`)).job;
      let cancelRequested = false;
      if (!terminal(job.state)) { await local(`/api/jobs/${id}/cancel`, {}); cancelRequested = true; }
      const end = Date.now() + 35_000;
      while (!terminal(job.state) && Date.now() < end) { await delay(250); job = (await local(`/api/jobs/${id}`)).job; }
      assert(terminal(job.state), `Owned job ${id} did not reach a terminal state during cleanup.`);
      cleaned.jobs.push({id, state: job.state, cancel_requested_by_cleanup: cancelRequested});
    }
    const end = Date.now() + 5_000;
    do {
      cleaned.slot_released = (await local('/api/status')).computation_active === false;
      if (cleaned.slot_released) break;
      await delay(200);
    } while (Date.now() < end);
    assert.equal(cleaned.slot_released, true, 'The computation slot was not released; no unrelated job was cancelled.');
  } catch (error) { cleaned.errors.push(error.message); }
  return cleaned;
}

let failure, cleanup;
try {
  const port = await until(async () => {
    if (launchError) throw launchError;
    return Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]);
  }, 15_000, 'isolated Chrome startup');
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`, {signal: AbortSignal.timeout(5_000)})).json();
  const page = tabs.find(tab => tab.type === 'page'); assert(page, 'No isolated page was created.');
  socket = new WebSocket(page.webSocketDebuggerUrl);
  socket.addEventListener('message', event => {
    try { receive(JSON.parse(String(event.data))); }
    catch (error) { if (!closing) captureErrors.push({error: error.message}); }
  });
  socket.addEventListener('error', () => { if (!closing) captureErrors.push({error: 'Isolated browser WebSocket error.'}); });
  await until(() => socket.readyState === WebSocket.OPEN, 15_000, 'isolated browser connection');
  await call('Page.enable'); await call('Runtime.enable'); await call('Network.enable', {maxTotalBufferSize: 32 * 1024 * 1024, maxResourceBufferSize: 8 * 1024 * 1024});
  await call('Emulation.setDeviceMetricsOverride', {width: 1360, height: 1100, deviceScaleFactor: 1, mobile: false});
  await call('Emulation.setEmulatedMedia', {features: [{name: 'prefers-color-scheme', value: 'light'}, {name: 'prefers-reduced-motion', value: 'reduce'}]});
  await call('Page.navigate', {url: address});
  await until(() => evaluate("document.querySelectorAll('#showcase-cases .showcase-card').length>=4 && !document.getElementById('theorem').disabled"), 20_000, 'published verified gallery');
  const status = await until(() => latest('/api/status')?.payload, 10_000, 'initial status response');
  const catalog = await until(() => latest('/api/showcase')?.payload, 10_000, 'gallery response');
  assert.equal(status.ok, true); assert.equal(status.computation_active, false, 'Leave existing work untouched; run when the slot is free.');
  assert.equal(status.search_modes?.hybrid?.available, true, 'The Hybrid runtime must be available.');
  assert.equal(catalog.schema, 'hydra-verified-showcase-v1');
  const cases = catalog.cases.filter(item => item.kernel_verified === true && item.independent_replay === true);
  assert(cases.length >= 4);
  assert.equal(await evaluate("document.querySelectorAll('#showcase-cases .showcase-card').length"), cases.length);
  assert.equal(await text('showcase-count'), `${cases.length} VERIFIED`);
  assert.equal(searchRequests().length, 0);
  evidence.gallery = {schema: catalog.schema, cases: cases.map(item => ({id: item.id, kernel_verified: item.kernel_verified,
    independent_replay: item.independent_replay, proof_steps: item.proof_steps, proof_nodes: item.proof_nodes,
    model_calls: item.model_calls, vampire_calls: item.vampire_calls, proof_sources: item.proof_sources}))};
  checks.push('at least four independently verified gallery records, loaded without starting a search');
  await screenshot('gallery-desktop.png', '#showcase');
  await call('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
  await screenshot('gallery-mobile.png', '#showcase');
  await call('Emulation.setDeviceMetricsOverride', {width: 1360, height: 1100, deviceScaleFactor: 1, mobile: false});
  await call('Emulation.setEmulatedMedia', {features: [{name: 'prefers-color-scheme', value: 'dark'}]});
  await screenshot('gallery-dark.png', '#showcase');
  await call('Emulation.setEmulatedMedia', {features: [{name: 'prefers-color-scheme', value: 'light'}]});

  const selected = cases.find(item => /fermat.*5/i.test(item.id)) || cases.find(item => /coupled/i.test(item.id)) || cases[0];
  const beforeInspectPosts = postCount();
  await galleryAction(selected.id, 'proof'); await waitResult('recorded proof inspection');
  const saved = (await until(() => latest(`/api/showcase/${selected.id}`)?.payload, 10_000, 'saved proof response')).record;
  assert.equal(saved.case_id, selected.id); assert.equal(saved.theorem, selected.theorem);
  assert.equal(saved.result.kernel_checked, true); assert.equal(saved.result.status, 'proved');
  assert.match(selected.artifact_sha256, /^[0-9a-f]{64}$/);
  assert.equal(selected.proof_steps, saved.result.commands.length);
  assert.equal(selected.proof_nodes, saved.result.proof_nodes);
  assert.equal(selected.model_calls, saved.result.search.model_calls);
  assert.equal(selected.vampire_calls, saved.result.search.vampire_calls);
  assert.deepEqual(selected.proof_sources, saved.result.proof_sources);
  const cardStats = await evaluate(`[...document.querySelectorAll('#showcase-cases article')].find(node=>node.dataset.caseId===${JSON.stringify(selected.id)}).querySelector('.showcase-stats').textContent`);
  assert(cardStats.includes(`${selected.proof_steps} steps`));
  assert(cardStats.includes(`model ${selected.model_calls} / Vampire ${selected.vampire_calls}`));
  assert.equal(postCount(), beforeInspectPosts, 'Inspecting a saved proof must not start a search or replay.');
  assert.equal(await text('run-origin'), `RECORDED ${saved.request.search_mode.toUpperCase()} PROOF`);
  assert.equal(await text('example-kind'), `RECORDED ${saved.request.search_mode.toUpperCase()} PROOF`);
  assert.match(await text('result-caption'), /Recorded, independently checked proof/);
  assert.equal(await value('tactics'), saved.result.commands.join('\n'));
  assert.equal(await text('metric-steps'), String(saved.result.commands.length));
  assert.equal(await text('metric-nodes'), String(saved.result.proof_nodes));
  const savedDetails = JSON.parse(await text('run-details-content'));
  assert.equal(savedDetails.origin, `recorded-${saved.request.search_mode}-search`);
  assert.equal(savedDetails.recorded_case, selected.id);
  assert.equal(savedDetails.artifact_sha256, selected.artifact_sha256);
  assert.equal(savedDetails.recorded_at, saved.recorded_at_utc);
  const savedSources = await assertStepSources(saved.result);
  const savedTrace = saved.result.trace.filter(row => typeof row.tactic === 'string');
  await click('trace-start');
  const initialGoals = await assertRenderedGoals(savedTrace[0].goals_before);
  await click('trace-next');
  await assertRenderedGoals(savedTrace[0].goals_after);
  const splitPosition = savedTrace.findIndex(row => row.goals_after?.length > 1);
  const position = splitPosition >= 0 ? splitPosition + 1 : Math.min(2, savedTrace.length);
  await evaluate(`document.querySelector('#trace button[data-position="${position}"]').click()`);
  const intermediateGoals = await assertRenderedGoals(savedTrace[position - 1].goals_after);
  await click('trace-end'); await assertRenderedGoals([]);
  assert.equal(await evaluate("document.querySelector('#goals .qed-state strong')?.textContent"), 'Proof verified by the kernel');
  await screenshot('recorded-proof.png', '.workspace');
  await call('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
  await screenshot('recorded-proof-mobile.png', '.proof-column');
  await call('Emulation.setDeviceMetricsOverride', {width: 1360, height: 1100, deviceScaleFactor: 1, mobile: false});
  await writeJSON('recorded-proof-ui.json', {case_id: selected.id, source_counts: savedSources,
    rendered_goals: {initial: initialGoals, intermediate_position: position, intermediate: intermediateGoals, final: []},
    ui: savedDetails, record: saved});
  checks.push('recorded provenance, actual saved counters, source badges, and exact initial/intermediate/final goals');

  const beforeReplay = replayRequests().length;
  await click('check-script'); await waitResult('fresh complete replay of saved proof', 90_000);
  const replay = await until(() => replayRequests()[beforeReplay]?.payload && replayRequests()[beforeReplay], 10_000, 'fresh replay receipt');
  assert.deepEqual(replay.body.tactics, saved.result.commands);
  assert.equal(replay.body.theorem, saved.theorem);
  assert.equal(replay.payload.result.kernel_checked, true);
  assert.equal(replay.payload.result.proof_nodes, saved.result.proof_nodes);
  assert.equal(await text('run-origin'), 'MANUAL KERNEL REPLAY');
  assert.equal(await text('metric-calls'), '—'); assert.equal(await text('metric-vampire'), '—');
  assert((await evaluate("[...document.querySelectorAll('#trace .step-origin')].map(node=>node.dataset.source)")).every(source => source === 'manual'));
  assert.equal(searchRequests().length, 0);
  await writeJSON('saved-proof-fresh-replay.json', {request: replay.body, response: replay.payload});
  await fill('theorem', 'forall n. n=n'); await assertCleared();
  assert.equal(await text('example-kind'), 'CUSTOM TEST');
  await galleryAction(selected.id, 'proof'); await waitResult('restored recorded proof');
  await galleryAction(selected.id, 'theorem'); await ready();
  assert.equal(await value('theorem'), saved.theorem); assert.equal(await value('tactics'), '');
  await assertCleared(); assert.equal(searchRequests().length, 0);
  checks.push('fresh manual replay makes no advisor call; custom edits and Load theorem clear the saved result and script');

  await select('search-mode', 'hybrid');
  const profiles = status.limits?.profiles;
  assert(profiles?.standard && profiles.deep && profiles.research, 'Public bounded profiles are required.');
  evidence.profile_controls = {};
  for (const name of ['deep', 'research']) evidence.profile_controls[name] = await profilesMatch(name, profiles);
  await select('call-budget', Math.max(...profiles.research.model_calls));
  await select('beam-width', Math.max(...profiles.research.beams));
  await select('search-mode', 'model');
  assert.equal(await value('search-profile'), 'standard');
  assert.deepEqual(await evaluate("[...document.getElementById('call-budget').options].map(o=>Number(o.value))"), profiles.standard.model_calls);
  assert.deepEqual(await evaluate("[...document.getElementById('beam-width').options].map(o=>Number(o.value))"), profiles.standard.beams);
  assert.equal(await evaluate("[...document.getElementById('search-profile').options].filter(o=>o.value!=='standard').every(o=>o.disabled)"), true);
  await assertCleared();
  checks.push('Deep and Research expose the exact public call/branch options; model-only resets to Standard');

  await select('search-mode', 'hybrid'); await select('search-profile', 'deep');
  const calls = Math.min(...profiles.deep.model_calls), beam = Math.min(...profiles.deep.beams);
  await select('call-budget', calls); await select('beam-width', beam);
  const theorem = 'forall n. exists k. n*n*n=n+3*k';
  await fill('theorem', theorem); await fill('tactics', '');
  assert.equal(await value('tactics'), '');
  assert.equal((await apiRead('/api/status')).computation_active, false);
  await click('search');
  const deepRequest = await until(() => searchRequests()[0]?.job_id && searchRequests()[0], 20_000, 'owned Deep search acknowledgement');
  assert.deepEqual(deepRequest.body, {theorem, max_model_calls: calls, beam_width: beam, search_profile: 'deep', search_mode: 'hybrid'});
  await waitResult('fresh Deep Hybrid cubic proof', 150_000);
  const deepJob = await until(() => ownedJobs.get(deepRequest.job_id)?.state === 'completed' && ownedJobs.get(deepRequest.job_id), 10_000, 'completed Deep job receipt');
  const deepResult = deepJob.result;
  assert.equal(deepResult.kernel_checked, true); assert.equal(deepResult.status, 'proved');
  assert.equal(deepResult.search.settings_profile, 'deep');
  for (const [key, setting] of Object.entries(profiles.deep.search)) assert.equal(deepResult.search.limits[key], setting, key);
  assert.equal(deepResult.search.limits.max_model_calls, calls);
  assert.equal(deepResult.search.limits.max_frontier, profiles.deep.frontiers[String(beam)]);
  assert.equal(deepResult.search.requested_beam_width, beam);
  assert.equal(deepResult.execution.quiescent, true); assert(deepResult.execution.peak_sampled_rss_bytes > 0);
  assert.equal(await text('run-origin'), 'HYBRID SEARCH');
  assert.equal(await text('example-kind'), 'FRESH HYBRID SCRIPT');
  const deepDetails = JSON.parse(await text('run-details-content'));
  assert.equal(deepDetails.origin, 'fresh-hybrid-search'); assert.equal(deepDetails.recorded_case, null);
  assert.equal(deepDetails.settings_profile, 'deep');
  const deepSources = await assertStepSources(deepResult);
  assert(deepResult.commands.some(command => command.startsWith('induction ')));
  await screenshot('fresh-deep-proof.png', '.workspace');
  await writeJSON('deep-hybrid-ui.json', {request: deepRequest.body, job_id: deepRequest.job_id,
    configured_profile: profiles.deep, source_counts: deepSources, ui: deepDetails, job: deepJob});
  evidence.deep_job_id = deepRequest.job_id;
  checks.push('one fresh blank-script Deep Hybrid cubic proof with captured request, actual native limits, sources, and quiescent result');

  await select('search-profile', 'research'); await assertCleared();
  await select('call-budget', Math.min(...profiles.research.model_calls));
  await select('beam-width', Math.min(...profiles.research.beams));
  await fill('theorem', '0=1'); await fill('tactics', '');
  assert.equal((await apiRead('/api/status')).computation_active, false);
  await click('search');
  const researchRequest = await until(() => searchRequests()[1]?.job_id && searchRequests()[1], 20_000, 'owned Research search acknowledgement');
  assert.equal(researchRequest.body.search_profile, 'research'); assert.equal(researchRequest.body.search_mode, 'hybrid');
  assert.equal(researchRequest.body.theorem, '0=1'); assert(!Object.hasOwn(researchRequest.body, 'tactics'));
  const activeJob = await until(() => {
    const job = ownedJobs.get(researchRequest.job_id);
    return job?.state === 'running' && job.progress?.phase && !['queued', 'starting'].includes(job.progress.phase) ? job : null;
  }, 60_000, 'actual Research worker progress before cancellation');
  const startup = {state: activeJob.state, progress: {...activeJob.progress}, elapsed_seconds: activeJob.elapsed_seconds};
  assert.equal(await evaluate("['theorem','tactics','search-mode','search-profile','call-budget','beam-width'].every(id=>document.getElementById(id).disabled)"), true);
  assert.equal(await evaluate("[...document.querySelectorAll('#showcase-cases button')].every(button=>button.disabled)"), true);
  await click('cancel-search');
  await until(async () => (await text('result-badge')) === 'Search cancelled', 45_000, 'owned Research cancellation');
  const cancelled = await until(() => ownedJobs.get(researchRequest.job_id)?.state === 'cancelled' && ownedJobs.get(researchRequest.job_id), 10_000, 'cancelled Research receipt');
  assert.equal(cancelled.result, null); assert.equal(await text('run-origin'), 'NO RESULT');
  assert.equal(await evaluate("document.getElementById('download-run').disabled && document.getElementById('branch-panel').hidden"), true);
  await until(async () => (await apiRead('/api/status')).computation_active === false, 15_000, 'released computation slot');
  await fill('theorem', 'forall n m. n=m -> m=n');
  await fill('tactics', 'intro n\nintro m\nintro h\nsymm\nexact h');
  await click('check-script'); await waitResult('manual proof after owned Research cancellation');
  assert.equal(await text('run-origin'), 'MANUAL KERNEL REPLAY');
  assert.equal(await text('metric-calls'), '—'); assert.equal(await text('metric-vampire'), '—');
  assert.equal(searchRequests().length, 2, 'No automatic search retry or extra allocation is allowed.');
  assert.equal(ownedJobs.size, 2);
  await writeJSON('research-cancellation-ui.json', {request: researchRequest.body, job_id: researchRequest.job_id,
    startup, cancelled_job: cancelled, computation_slot_released: true,
    manual_replay_after_cleanup: JSON.parse(await text('run-details-content'))});
  evidence.research_job_id = researchRequest.job_id;
  checks.push('Research starts an actual worker, disables controls, cancels only its owned job, releases the slot, and permits a fresh manual proof');
  assert.deepEqual(pageErrors, [], 'No uncaught JavaScript or console.error events are allowed.');
  assert.deepEqual(captureErrors, [], 'All required network evidence must be captured.');
  assert(requests.every(item => item.http_status === undefined || item.http_status < 400), 'An API request returned an HTTP error.');
} catch (error) {
  failure = {message: error.message, stack: error.stack};
  if (socket?.readyState === WebSocket.OPEN) {
    try { evidence.failure_ui = await evaluate("({badge:document.getElementById('result-badge')?.textContent,error:document.getElementById('page-error')?.textContent,caption:document.getElementById('result-caption')?.textContent})"); }
    catch { /* Keep the original failure if the owned browser has already exited. */ }
  }
} finally {
  cleanup = await cleanupOwnedJobs();
  closing = true;
  if (socket?.readyState === WebSocket.OPEN) { try { await call('Browser.close'); } catch {} socket.close(); }
  for (const item of pending.values()) item.reject(new Error('Advanced browser check ended.'));
  pending.clear();
  if (chrome.exitCode === null && chrome.signalCode === null && chrome.pid) {
    try { process.kill(-chrome.pid, 'SIGTERM'); } catch {}
    await delay(600);
    if (chrome.exitCode === null && chrome.signalCode === null) { try { process.kill(-chrome.pid, 'SIGKILL'); } catch {} }
  }
  const browserExitDeadline = Date.now() + 3_000;
  while (chrome.exitCode === null && chrome.signalCode === null && chrome.pid && Date.now() < browserExitDeadline) await delay(50);
  cleanup.browser_exit_confirmed = !chrome.pid || chrome.exitCode !== null || chrome.signalCode !== null;
  if (cleanup.browser_exit_confirmed) await rm(profile, {recursive: true, force: true});
  else cleanup.errors.push(`The owned browser did not exit; its new temporary profile was retained at ${profile}.`);
}

if (!failure && cleanup.errors.length) failure = {message: 'Owned job cleanup did not complete.', details: cleanup.errors};
if (!failure && (pageErrors.length || captureErrors.length)) failure = {message: 'Late browser or evidence-capture errors were observed.'};
const report = {status: failure ? 'failed' : 'passed', started_at: started, finished_at: new Date().toISOString(),
  mode: 'advanced-gallery-and-profiles', url: address, isolated_browser: true, existing_browser_profile_used: false,
  checks, screenshots, evidence, page_errors: pageErrors, network_capture_errors: captureErrors, cleanup,
  observed_search_requests: searchRequests().map(item => ({request: item.body, job_id: item.job_id, http_status: item.http_status})),
  ...(failure ? {failure} : {})};
await writeJSON('browser-advanced.json', report);
console.log(JSON.stringify({status: report.status, output, checks, screenshots, cleanup, ...(failure ? {failure} : {})}));
if (failure) process.exitCode = 1;
