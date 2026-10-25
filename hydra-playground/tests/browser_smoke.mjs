// UI smoke checks in a new, isolated headless Chrome profile. No user browser
// profile, cookies, credentials or existing tabs are accessed.
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,mkdir,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import assert from 'node:assert/strict';

const address=process.env.HYDRA_TEST_URL || 'http://127.0.0.1:8767/';
const live=process.env.HYDRA_TEST_LIVE==='1';
const hybrid=process.env.HYDRA_TEST_HYBRID==='1';
assert(!(live && hybrid),'Choose either HYDRA_TEST_LIVE or HYDRA_TEST_HYBRID.');
const target=new URL(address);
assert(target.protocol==='http:' && ['127.0.0.1','localhost'].includes(target.hostname),'Only the local app may be tested.');
const profile=await mkdtemp(join(tmpdir(),'hydra-browser-'));
const output=resolve(process.env.HYDRA_TEST_OUTPUT || (hybrid?'output/hydra-hybrid-playground-2026-09-01':'output/hydra-playground-2026-09-01'));
await mkdir(output,{recursive:true});
const chrome=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',[
  '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
  '--disable-background-networking','--disable-component-update','--disable-sync',
  '--disable-features=MediaRouter,OptimizationHints,Translate','--metrics-recording-only',
  '--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'
],{detached:true,stdio:['ignore','ignore','ignore']});
let socket;
const pending=new Map();let serial=0;const checks=[];
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(fn,timeout=15000,label='UI state'){
  const end=Date.now()+timeout;let last;
  while(Date.now()<end){try{last=await fn();if(last)return last;}catch(error){last=error.message;}await delay(100);}
  throw new Error(`${label} timed out: ${String(last)}`);
}
function call(method,params={}){
  const id=++serial;
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(new Error(`CDP timeout: ${method}`));},20000);
    pending.set(id,{resolve:value=>{clearTimeout(timer);resolve(value);},reject:error=>{clearTimeout(timer);reject(error);}});
    socket.send(JSON.stringify({id,method,params}));
  });
}
async function evaluate(expression){
  const result=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  if(result.exceptionDetails)throw new Error(result.exceptionDetails.text+': '+(result.exceptionDetails.exception?.description || ''));
  return result.result?.value;
}
const text=id=>evaluate(`document.getElementById(${JSON.stringify(id)}).textContent`);
const click=id=>evaluate(`document.getElementById(${JSON.stringify(id)}).click()`);
async function fill(id,value){await evaluate(`(() => {const e=document.getElementById(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('input',{bubbles:true}));})()`);}
async function select(id,value){await evaluate(`(() => {const e=document.getElementById(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);}
async function waitReady(){await until(()=>evaluate("!document.getElementById('check-script').disabled"),15000,'enabled script check');}
async function screenshot(name){const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await writeFile(join(output,name),Buffer.from(shot.data,'base64'));}
try{
  const port=await until(async()=>Number((await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]),15000,'isolated Chrome startup');
  const tabs=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const page=tabs.find(x=>x.type==='page');assert(page,'No isolated page created');
  socket=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  socket.addEventListener('message',event=>{const message=JSON.parse(String(event.data));const item=pending.get(message.id);if(item){pending.delete(message.id);if(message.error)item.reject(new Error(JSON.stringify(message.error)));else item.resolve(message.result);}});
  await call('Page.enable');await call('Runtime.enable');
  await call('Emulation.setDeviceMetricsOverride',{width:1360,height:1100,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url:address});
  await until(()=>evaluate("document.getElementById('example')?.options.length===6 && !document.getElementById('check-script').disabled"),15000,'initial app load');
  if(live){
    await select('search-mode','model');
    assert.equal(await evaluate("document.getElementById('search').disabled"),false,'Actual local model must be ready');
    await evaluate("document.getElementById('example').value='';document.getElementById('example').dispatchEvent(new Event('change',{bubbles:true}));");
    assert.equal(await evaluate("document.getElementById('theorem').value"),'');
    await fill('theorem','forall n. n = n');await fill('tactics','');
    await evaluate("document.getElementById('call-budget').value='8';document.getElementById('beam-width').value='1';");
    await click('search');
    await until(()=>evaluate("['Kernel verified','No proof found','Search stopped','Could not start'].includes(document.getElementById('result-badge').textContent)"),190000,'fresh live model search');
    assert.equal(await text('result-badge'),'Kernel verified',await text('page-error'));
    assert.equal(await text('run-origin'),'LIVE MODEL SEARCH');
    assert.equal(await text('example-kind'),'FRESH MODEL SCRIPT');
    assert(Number(await text('metric-calls'))>0,'Fresh model calls must be counted');
    assert(Number(await text('metric-steps'))>0,'Winning commands must be replayed');
    const details=JSON.parse(await text('run-details-content'));
    assert.equal(details.model.numerical_equivalence_to_training,false);
    assert.equal(details.kernel_checked,true);
    await writeFile(join(output,'live-model-ui-result.json'),JSON.stringify(details,null,2)+'\n');
    await screenshot('live-model.png');checks.push('fresh trained-model search, native proof, model provenance and visible steps');
    await fill('theorem','forall n m. n + m = m + n');await fill('tactics','');await click('search');
    await until(()=>evaluate("!document.getElementById('cancel-search').disabled && Number(document.getElementById('search-progress').value)>=1"),90000,'model search active before cancel');
    await click('cancel-search');
    await until(async()=>(await text('result-badge'))==='Search cancelled',15000,'owned model cancellation');
    assert.equal(await evaluate("document.getElementById('download-run').disabled"),true);
    assert.equal(await text('run-origin'),'NO RESULT');
    await fill('theorem','forall n m. n = m -> m = n');
    await fill('tactics','intro n\nintro m\nintro h\nsymm\nexact h');await click('check-script');
    await until(async()=>(await text('result-badge'))==='Kernel verified',15000,'manual work after model cancellation');
    assert.equal(await text('run-origin'),'MANUAL KERNEL REPLAY');
    checks.push('real model cancellation discards result and releases the computation slot');
  } else if(hybrid){
    assert.equal(await evaluate("document.getElementById('search-mode').value"),'hybrid','Hybrid must be the default method.');
    assert.equal(await evaluate("document.getElementById('search').disabled"),false,'The full hybrid runtime must be ready.');
    assert.match(await text('vampire-status'),/ready/);
    checks.push('hybrid is the default method and actual Vampire availability is visible');

    await select('search-mode','heuristic');
    assert.equal(await evaluate("document.getElementById('call-budget').disabled"),true,'Heuristic mode does not use the model budget.');
    await fill('theorem','forall a b. a=b -> (b=a /\\ a=b)');
    // Both invalid tactic text and excessive length are irrelevant to a fresh
    // search. They must still be rejected when checking the script manually.
    await fill('tactics','not_a_tactic '.repeat(50)+'\n'+Array(161).fill('refl').join('\n'));
    await click('check-script');
    assert.match(await text('page-error'),/at most 160 tactics/);
    await click('search');
    await until(()=>evaluate("['Kernel verified','No proof found','Search stopped','Could not start'].includes(document.getElementById('result-badge').textContent)"),190000,'native heuristic proof');
    assert.equal(await text('result-badge'),'Kernel verified',(await text('page-error'))+' '+(await text('result-caption')));
    assert.equal(await text('run-origin'),'HEURISTIC SEARCH');
    assert.equal(await text('example-kind'),'FRESH HEURISTIC SCRIPT');
    assert.equal(await text('metric-calls'),'0');assert.equal(await text('metric-vampire'),'0');
    assert(Number(await text('metric-states'))>0);assert(Number(await text('metric-attempts'))>0);
    const heuristicDetails=JSON.parse(await text('run-details-content'));
    assert.equal(heuristicDetails.search_mode,'heuristic');
    assert.equal(heuristicDetails.kernel_checked,true);
    assert.equal(heuristicDetails.model_used,false);assert.equal(heuristicDetails.vampire_used,false);
    assert.equal(heuristicDetails.execution.quiescent,true,'Only a finished, cleaned-up worker result may be published.');
    assert(heuristicDetails.execution.peak_sampled_rss_bytes>0);
    const sourceTags=await evaluate("[...document.querySelectorAll('#trace .step-origin')].map(node=>node.dataset.source)");
    assert.equal(sourceTags.length,Number(await text('metric-steps')));
    assert(sourceTags.length>0 && sourceTags.every(source=>source==='heuristic'));
    assert.equal(await evaluate("document.querySelectorAll('#trace .step-reason').length"),sourceTags.length);
    assert.match(await text('proof-sources'),/HEURISTIC/);
    await writeFile(join(output,'heuristic-ui-result.json'),JSON.stringify(heuristicDetails,null,2)+'\n');
    checks.push('heuristic native proof, zero advisor calls, per-step sources, and ignored oversized search script');

    const branches=heuristicDetails.search.branches.slice(0,256);
    const childIndex=branches.findIndex(row=>Number.isInteger(row.id) && row.parent_id>0 && Array.isArray(row.goals_after) && row.goals_after.length && branches.some(parent=>parent.id===row.parent_id));
    assert(childIndex>=0,'A native child and its retained parent must be available.');
    const child=branches[childIndex];
    await evaluate(`document.querySelector('#branch-list button[data-branch-index="${childIndex}"]').click()`);
    assert.equal(await text('branch-title'),`Branch #${child.id}`);
    assert.deepEqual(await evaluate("[...document.querySelectorAll('#branch-goals .branch-goal pre')].map(node=>node.textContent)"),child.goals_after,'Snapshots must display the exact supplied native goals.');
    assert.match(await text('branch-meta'),new RegExp(`Parent #${child.parent_id}`));
    await click('branch-parent');assert.equal(await text('branch-title'),`Branch #${child.parent_id}`);
    const rejectedIndex=branches.findIndex(row=>row.status==='rejected' && !Array.isArray(row.goals_after));
    assert(rejectedIndex>=0,'The recorded heuristic search must contain a rejected tactic.');
    await evaluate(`document.querySelector('#branch-list button[data-branch-index="${rejectedIndex}"]').click()`);
    assert.match(await text('branch-goals'),/No exact goal snapshot was recorded/);
    assert.equal(await evaluate("document.querySelectorAll('#branch-goals .branch-goal pre').length"),0);
    assert.equal(await text('result-badge'),'Kernel verified','Exploration snapshots do not replace the independently verified winner.');
    assert.equal(await text('goal-count'),'0 OPEN GOALS');
    checks.push('exact sibling snapshots, parent navigation, and explicit omission for rejected transitions');

    await select('search-mode','symbolic');
    assert.equal(await text('result-badge'),'Not checked');
    assert.equal(await text('run-origin'),'NO RESULT');
    assert.equal(await evaluate("document.getElementById('branch-panel').hidden"),true);
    assert.equal(await evaluate("document.getElementById('download-run').disabled"),true);
    await fill('theorem','forall a. S a = 0 -> a = 0');await fill('tactics','');
    await click('search');
    await until(()=>evaluate("['Kernel verified','No proof found','Search stopped','Could not start'].includes(document.getElementById('result-badge').textContent)"),190000,'actual Vampire advice and native proof');
    assert.equal(await text('result-badge'),'Kernel verified',(await text('page-error'))+' '+(await text('result-caption')));
    assert.equal(await text('run-origin'),'SYMBOLIC SEARCH');
    assert.equal(await text('metric-calls'),'0');assert(Number(await text('metric-vampire'))>0,'The symbolic test must actually run Vampire.');
    const symbolicDetails=JSON.parse(await text('run-details-content'));
    assert.equal(symbolicDetails.search_mode,'symbolic');assert.equal(symbolicDetails.kernel_checked,true);
    assert.equal(symbolicDetails.model_used,false);assert.equal(symbolicDetails.vampire_used,true);
    assert.equal(symbolicDetails.execution.quiescent,true);
    assert(symbolicDetails.execution.peak_sampled_rss_bytes>0);
    assert(Number.isFinite(symbolicDetails.execution.peak_sampled_solver_rss_bytes) && symbolicDetails.execution.peak_sampled_solver_rss_bytes>=0,'Sampled solver RSS may be zero for a very short process.');
    assert(symbolicDetails.search.vampire_runs.length>0);
    await writeFile(join(output,'symbolic-ui-result.json'),JSON.stringify(symbolicDetails,null,2)+'\n');
    await evaluate('window.scrollTo(0,0)');await screenshot('hybrid-symbolic.png');
    const solverBranches=symbolicDetails.search.branches.slice(0,256);
    const solverIndex=solverBranches.findIndex(row=>row.source==='vampire' && Number.isInteger(row.id));
    assert(solverIndex>=0,'At least one native transition must reconstruct actual Vampire guidance.');
    await evaluate(`document.querySelector('#branch-list button[data-branch-index="${solverIndex}"]').click()`);
    await evaluate("document.getElementById('branch-panel').scrollIntoView({block:'start'})");
    assert.match(await text('branch-meta'),/VAMPIRE/);
    await screenshot('hybrid-symbolic-branch.png');
    checks.push('mode switch clears stale proof; actual Vampire guidance is reconstructed into a native checked proof');

    await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    await evaluate('window.scrollTo(0,0)');
    assert.equal(await evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"),true,'Mobile layout must not overflow horizontally.');
    await screenshot('hybrid-mobile.png');
    await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'dark'}]});
    await call('Emulation.setDeviceMetricsOverride',{width:1360,height:1100,deviceScaleFactor:1,mobile:false});
    await evaluate('window.scrollTo(0,0)');
    assert.equal(await evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"),true,'Desktop layout must not overflow horizontally.');
    await screenshot('hybrid-desktop-dark.png');
    await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'light'}]});
    checks.push('hybrid controls and branch viewer preserve responsive mobile and dark layouts');

    await select('search-mode','hybrid');await select('call-budget','8');await select('beam-width','1');
    await fill('theorem','forall a. S a = a');await fill('tactics','');
    await click('search');
    await until(()=>evaluate("!document.getElementById('cancel-search').disabled && Number(document.getElementById('metric-calls').textContent)>=1"),130000,'actual hybrid model call before cancellation');
    assert.equal(await evaluate("document.getElementById('search-mode').disabled && document.getElementById('theorem').disabled && document.getElementById('call-budget').disabled"),true,'Search inputs must be disabled while the worker is active.');
    const callsBeforeCancel={model:Number(await text('metric-calls')),vampire:Number(await text('metric-vampire'))};
    await click('cancel-search');
    await until(async()=>(await text('result-badge'))==='Search cancelled',15000,'owned hybrid cancellation');
    assert.equal(await text('run-origin'),'NO RESULT');
    assert.equal(await evaluate("document.getElementById('download-run').disabled"),true);
    assert.equal(await evaluate("document.getElementById('branch-panel').hidden"),true);
    await until(()=>evaluate("fetch('/api/status',{cache:'no-store'}).then(response=>response.json()).then(status=>status.ok===true && status.computation_active===false)"),15000,'computation slot released after owned cleanup');
    await fill('theorem','forall n m. n=m -> m=n');
    await fill('tactics','intro n\nintro m\nintro h\nsymm\nexact h');await click('check-script');
    await until(async()=>(await text('result-badge'))==='Kernel verified',15000,'native replay after hybrid cancellation');
    assert.equal(await text('run-origin'),'MANUAL KERNEL REPLAY');
    assert.equal(await text('metric-calls'),'—');assert.equal(await text('metric-vampire'),'—');
    await writeFile(join(output,'hybrid-cancellation-ui.json'),JSON.stringify({search_mode:'hybrid',calls_observed_before_cancel:callsBeforeCancel,cancelled:true,computation_slot_released:true,manual_replay_after_cleanup:JSON.parse(await text('run-details-content'))},null,2)+'\n');
    checks.push('actual model invocation followed by hybrid cancellation, owned cleanup, and successful manual replay');
  } else {
  assert.equal(await text('result-badge'),'Not checked');checks.push('no proof claim before checking');
  await click('check-script');
  await until(async()=>(await text('result-badge'))==='Kernel verified',15000,'saved proof fresh kernel replay');
  assert.equal(await text('metric-steps'),'8');assert.equal(await text('run-origin'),'MANUAL KERNEL REPLAY');
  assert.equal(await evaluate("document.querySelectorAll('#trace .trace-step').length"),8);
  checks.push('saved model example replayed as manual, eight exact steps');
  await click('trace-start');assert.equal(await text('goal-count'),'1 OPEN GOAL');
  await evaluate("document.querySelector('#trace button[data-position=\"4\"]').click()");
  assert.equal(await text('goal-count'),'2 OPEN GOALS');
  await click('trace-end');assert.equal(await text('goal-count'),'0 OPEN GOALS');checks.push('trace shows initial, conjunction split and final goals');
  await screenshot('desktop.png');

  await fill('theorem','forall n m.\n n = m -> m = n');
  await fill('tactics','intro n\nintro m\nintro h\nsymm\nexact h');
  assert.equal(await text('result-badge'),'Not checked');assert.equal(await text('example-kind'),'CUSTOM TEST');
  await click('step-tactic');await until(async()=>(await text('metric-steps'))==='1',15000,'single-step check');
  assert.match(await text('goals'),/n/);await waitReady();await click('check-script');
  await until(async()=>(await text('result-badge'))==='Kernel verified',15000,'custom multiline theorem');checks.push('custom multiline theorem and one-step/full replay');

  await fill('theorem','0 = 1');await fill('tactics','refl');await click('check-script');
  await until(async()=>(await text('result-badge'))==='Step rejected',15000,'false statement rejection');
  assert.match(await text('goals'),/0 = 1/);assert.equal(await text('goal-count'),'1 OPEN GOAL');checks.push('false statement never receives proof label');
  await fill('theorem','forall n. n =');await click('check-script');
  await until(()=>evaluate("!document.getElementById('page-error').hidden"),15000,'syntax error');
  assert.notEqual(await text('result-badge'),'Kernel verified');checks.push('parse error clears stale proof claim');
  await fill('theorem','<img src=x onerror=alert(1)>');await click('check-script');
  await until(()=>evaluate("!document.getElementById('page-error').hidden"),15000,'injection rejection');
  assert.equal(await evaluate("document.querySelectorAll('#page-error img, #goals img, #trace img').length"),0);checks.push('untrusted input is rendered as text');

  await evaluate("document.getElementById('example').value='equality-symmetry';document.getElementById('example').dispatchEvent(new Event('change',{bubbles:true}));");
  await waitReady();await click('check-script');await until(async()=>(await text('result-badge'))==='Kernel verified',15000,'reset to useful example');
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  assert.equal(await evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"),true);await screenshot('mobile.png');
  await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'dark'}]});
  await call('Emulation.setDeviceMetricsOverride',{width:1360,height:1100,deviceScaleFactor:1,mobile:false});
  assert.equal(await evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"),true);await screenshot('desktop-dark.png');checks.push('responsive desktop/mobile and dark appearance');
  }
  const result={status:'passed',mode:live?'live-model':hybrid?'hybrid':'manual',checks,url:address,isolated_browser:true,existing_browser_profile_used:false,screenshots:live?['live-model.png']:hybrid?['hybrid-symbolic.png','hybrid-symbolic-branch.png','hybrid-mobile.png','hybrid-desktop-dark.png']:['desktop.png','mobile.png','desktop-dark.png']};
  await writeFile(join(output,live?'browser-live.json':hybrid?'browser-hybrid.json':'browser-smoke.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
} finally {
  if(socket?.readyState===WebSocket.OPEN){try{await call('Browser.close');}catch{}socket.close();}
  for(const item of pending.values())item.reject(new Error('Browser check ended'));pending.clear();
  if(chrome.exitCode===null && chrome.signalCode===null){try{process.kill(-chrome.pid,'SIGTERM');}catch{}}
  await delay(600);
  if(chrome.exitCode===null && chrome.signalCode===null){try{process.kill(-chrome.pid,'SIGKILL');}catch{}}
  await rm(profile,{recursive:true,force:true});
}
