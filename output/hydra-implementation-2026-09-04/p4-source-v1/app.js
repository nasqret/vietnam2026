(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const ui = Object.fromEntries(["example","theorem","tactics","search","inspect-goal","step-tactic","check-script","new-test","search-mode","search-mode-description","call-budget","beam-width","beam-label","page-error","model-unavailable","model-name","model-detail","vampire-status","vampire-detail","connection-dot","connection-label","result-badge","result-caption","progress-area","progress-message","progress-detail","search-progress","cancel-search","metric-calls","metric-vampire","metric-states","metric-attempts","metric-steps","metric-nodes","proof-sources","goals","goal-title","goal-count","trace","trace-position","trace-start","trace-prev","trace-play","trace-next","trace-end","download-run","run-origin","run-details","run-details-content","example-kind","example-description","theorem-length","script-count","branch-panel","branch-list","branch-summary","branch-title","branch-meta","branch-reason","branch-parent","branch-goals"].map((id) => [id,$(id)]));
  const state = {status:null, token:"", examples:[], example:null, busy:false, job:null, result:null, snapshot:null, records:[], position:0, branches:[], branchPosition:-1, manualCount:0, playTimer:null, pollTimer:null, started:0, generation:0, progressCounts:{}};
  for(const id of ["search-profile","profile-description","showcase","showcase-title","showcase-count","showcase-cases","showcase-note","experimental-engine","experimental-lemmas","experimental-planner","experimental-description","certificate-cost","lemma-summary","planner-summary"])ui[id]=$(id);
  state.showcase=[];
  const modes = {
    hybrid:{name:"Hybrid",origin:"HYBRID SEARCH",script:"FRESH HYBRID SCRIPT",model:true,description:"Heuristics handle routine steps. Vampire suggests first-order moves; the model ranks unresolved choices. The winning script must pass independent native replay."},
    symbolic:{name:"Symbolic",origin:"SYMBOLIC SEARCH",script:"FRESH SYMBOLIC SCRIPT",model:false,description:"Native heuristics and Vampire explore proof branches. No model is loaded. Vampire guidance must be reconstructed as native tactics before it can prove anything."},
    heuristic:{name:"Heuristic",origin:"HEURISTIC SEARCH",script:"FRESH HEURISTIC SCRIPT",model:false,description:"Native tactic search, induction, and certified arithmetic only. Neither the model nor Vampire is called."},
    model:{name:"Model",origin:"LIVE MODEL SEARCH",script:"FRESH MODEL SCRIPT",model:true,description:"The trained model proposes each next tactic using the original bounded search. No extra heuristic or Vampire guidance is added."}
  };
  const sourceLabels={heuristic:"HEURISTIC",model:"MODEL",vampire:"VAMPIRE",manual:"MANUAL",unknown:"SOURCE NOT RECORDED"};
  const metricIds=["metric-calls","metric-vampire","metric-states","metric-attempts","metric-steps","metric-nodes"];
  const element = (tag, className, text) => {const node=document.createElement(tag); if(className)node.className=className; if(text!==undefined)node.textContent=String(text); return node;};
  const tactics = () => ui.tactics.value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  const errorText = error => typeof error === "string" ? error : error?.message || "The request could not be completed.";
  const showError = message => {ui["page-error"].textContent=message;ui["page-error"].hidden=!message;};
  const badge = (label, kind="neutral") => {ui["result-badge"].textContent=label;ui["result-badge"].className="badge "+kind;};
  const selectedMode=()=>Object.hasOwn(modes,ui["search-mode"].value)?ui["search-mode"].value:"hybrid";
  const countValue=value=>Number.isInteger(value) && value>=0?String(value):"—";
  const modeAvailable=mode=>ui["experimental-engine"].checked && ["model","hybrid"].includes(mode)?false:state.status?.search_modes?state.status.search_modes[mode]?.available===true:mode==="model" && state.status?.model?.available===true;
  const experimentalSelection=()=>ui["experimental-engine"].checked?{engine:"sharing-v1",lemmas:ui["experimental-lemmas"].checked,...(ui["experimental-planner"].value!=="off"?{planner:ui["experimental-planner"].value}:{})}:null;
  const sourceName=value=>Object.hasOwn(sourceLabels,value)?value:"unknown";
  const sourceBadge=(source,text)=>element("span","source-badge source-"+sourceName(source),text || sourceLabels[sourceName(source)]);

  function repeatedWorkNote(search) {
    const notes=[];
    const model=search?.model_repeated_prompts_skipped;
    const vampire=search?.vampire_advice_cache?.cache_hits;
    const algebra=search?.polynomial_decomposition?.repeated_decompositions_skipped;
    if(Number.isSafeInteger(model) && model>0)notes.push(`Skipped ${model} repeated model prompt${model===1?"":"s"} before decoding.`);
    if(Number.isSafeInteger(vampire) && vampire>0)notes.push(`Skipped ${vampire} repeated Vampire launch${vampire===1?"":"es"} after earlier unsuccessful attempts.`);
    if(Number.isSafeInteger(algebra) && algebra>0)notes.push(`Skipped ${algebra} repeated algebra plan${algebra===1?"":"s"} at equal or greater proof depth.`);
    return notes.join(" ");
  }

  function renderProfile() {
    const original=selectedMode()==="model";
    if(original)ui["search-profile"].value="standard";
    if(ui["experimental-engine"].checked && ui["search-profile"].value==="research")ui["search-profile"].value="deep";
    for(const option of ui["search-profile"].options)option.disabled=(original && option.value!=="standard") || (ui["experimental-engine"].checked && option.value==="research");
    const profile=state.status?.limits?.profiles?.[ui["search-profile"].value];
    ui["search-profile"].disabled=state.busy || !state.status?.limits?.profiles;
    if(!profile)return;
    function choices(control,values,preferred,label) {
      const previous=Number(control.value);
      if([...control.options].map(option=>Number(option.value)).join(",")!==values.join(",")){
        control.replaceChildren(...values.map(value=>new Option(label(value),String(value))));
        control.value=String(values.includes(previous)?previous:preferred);
      }
    }
    choices(ui["call-budget"],profile.model_calls,profile.default_model_calls,value=>`${value} calls`);
    choices(ui["beam-width"],profile.beams,profile.default_beam,value=>`${value} · ${value===1?"focused":value===8?"broad":"wider"}`);
    const parts=[`${profile.worker.wall_seconds/60} min worker ceiling`,`${profile.search.max_states.toLocaleString()} states`,`${profile.search.max_tactic_attempts.toLocaleString()} tactic checks`];
    if(["hybrid","symbolic"].includes(selectedMode()))parts.push(`${profile.search.max_vampire_calls} Vampire attempts, ${profile.vampire?.solver_seconds || 1}s each`);
    ui["profile-description"].textContent=original?"The original model-only algorithm keeps its standard budgets; Deep and Research apply to the branch-based search.":parts.join(" · ")+".";
  }

  function renderMode() {
    const mode=selectedMode();const config=modes[mode];
    ui["search-mode-description"].textContent=config.description;
    ui["beam-label"].textContent=mode==="model"?"Search beam":"Branch budget";
    for(const option of ui["search-mode"].options)option.disabled=Boolean(state.status) && !modeAvailable(option.value);
    const unavailable=Boolean(state.status) && !modeAvailable(mode);
    ui["model-unavailable"].hidden=!unavailable;
    ui["model-unavailable"].textContent=unavailable?`${config.name} search is unavailable with the current server components. Choose an available method, or check a proof script manually.`:"";
  }

  function stepOrigin(record,index) {
    const supplied=record.origin || state.result?.search?.provenance?.[index];
    if(supplied && typeof supplied==="object" && (!supplied.command || supplied.command===record.tactic))return {...supplied,source:sourceName(supplied.source),reason:typeof supplied.reason==="string"?supplied.reason:""};
    if(state.snapshot?.kind==="manual")return {source:"manual",reason:"Checked from the submitted script."};
    if(state.snapshot?.kind==="model")return {source:"model",reason:"Proposed by the trained model."};
    return {source:"unknown",reason:"This result did not include tactic provenance."};
  }

  async function api(path, body) {
    const headers={Accept:"application/json"};
    const options={method:body===undefined?"GET":"POST",headers,cache:"no-store",credentials:"same-origin"};
    if(body!==undefined){headers["Content-Type"]="application/json";headers["X-CSRF-Token"]=state.token;options.body=JSON.stringify(body);}
    let response;
    try {response=await fetch(path,options);} catch (_) {throw new Error("The local server is not reachable. Restart the playground server, then refresh this page.");}
    let data;
    try {data=await response.json();} catch (_) {throw new Error("The server returned an unreadable response. No proof result was accepted.");}
    if(!response.ok || data.ok===false)throw new Error(errorText(data.error) || `Request failed (${response.status}).`);
    return data;
  }

  function updateControls() {
    renderProfile();
    const experimentalReady=state.status?.experimental?.available===true;
    ui["experimental-engine"].disabled=state.busy || !experimentalReady;
    ui["experimental-lemmas"].disabled=state.busy || !experimentalReady || !ui["experimental-engine"].checked;
    ui["experimental-planner"].disabled=state.busy || !experimentalReady || !ui["experimental-engine"].checked || !state.status?.experimental?.planners?.includes("deterministic");
    ui["experimental-description"].textContent=experimentalReady?"Uses an isolated compiler and the unchanged kernel. Lemmas are checked again on every import, including replay. This first version supports Heuristics and Symbolic; the saved model keeps its original engine.":state.status?.experimental?.detail || "The experimental runtime is unavailable on this server.";
    const ready=Boolean(state.status?.ok && state.token);
    const hasTheorem=Boolean(ui.theorem.value.trim());
    const commands=tactics();
    for(const name of ["theorem","tactics","example","new-test","search-mode","beam-width"])ui[name].disabled=state.busy;
    ui["call-budget"].disabled=state.busy || !modes[selectedMode()].model;
    ui.search.disabled=state.busy || !ready || !hasTheorem || !modeAvailable(selectedMode());
    ui["inspect-goal"].disabled=state.busy || !ready || !hasTheorem;
    ui["check-script"].disabled=state.busy || !ready || !hasTheorem || !commands.length;
    ui["step-tactic"].disabled=state.busy || !ready || !hasTheorem || !commands.length || state.manualCount>=commands.length;
    ui["download-run"].disabled=!state.result || state.busy;
    const count=state.records.length;
    ui["trace-start"].disabled=state.busy || !count || state.position===0;
    ui["trace-prev"].disabled=state.busy || !count || state.position===0;
    ui["trace-next"].disabled=state.busy || !count || state.position>=count;
    ui["trace-end"].disabled=state.busy || !count || state.position>=count;
    ui["trace-play"].disabled=state.busy || !count;
    for(const button of ui.trace.querySelectorAll("button"))button.disabled=state.busy;
    for(const button of ui["branch-list"].querySelectorAll("button"))button.disabled=state.busy;
    for(const button of ui["showcase-cases"].querySelectorAll("button"))button.disabled=state.busy;
    const branch=state.branches[state.branchPosition];
    ui["branch-parent"].disabled=state.busy || !branch || !Number.isInteger(branch.parent_id) || !state.branches.some(item=>Number.isInteger(item.id) && item.id===branch.parent_id);
    ui["cancel-search"].disabled=!state.job;
    ui["theorem-length"].textContent=`${new TextEncoder().encode(ui.theorem.value).length} / 4096 bytes`;
    ui["script-count"].textContent=`${commands.length} TACTIC${commands.length===1?"":"S"}`;
    renderMode();
  }

  function stopPlayback(){if(state.playTimer)clearInterval(state.playTimer);state.playTimer=null;ui["trace-play"].textContent="Play steps";}
  function emptyGoals(title="A proof starts with a goal.",message="Enter a theorem, then inspect it, check a script, or ask Hydra to search.") {
    const box=element("div","empty-state");box.append(element("div","empty-symbol","⊢"),element("strong","",title),element("p","",message));ui.goals.replaceChildren(box);
  }
  function clearResult(message) {
    stopPlayback();state.result=null;state.snapshot=null;state.records=[];state.position=0;state.branches=[];state.branchPosition=-1;state.manualCount=0;state.progressCounts={};
    badge("Not checked");ui["result-caption"].textContent=message || "The inputs changed. Run a fresh check to see the new proof state.";
    for(const id of metricIds)ui[id].textContent="—";
    ui["proof-sources"].replaceChildren();ui["proof-sources"].hidden=true;
    for(const id of ["certificate-cost","lemma-summary","planner-summary"]){ui[id].hidden=true;ui[id].textContent="";}
    ui["branch-panel"].hidden=true;ui["branch-list"].replaceChildren();ui["branch-goals"].replaceChildren();
    ui["branch-title"].textContent="Select a branch";ui["branch-meta"].replaceChildren();ui["branch-reason"].textContent="";
    ui["goal-title"].textContent="Current goals";ui["goal-count"].textContent="NO CHECK YET";ui["trace-position"].textContent="—";
    ui.trace.replaceChildren(element("li","trace-empty","Checked tactics will appear here. Select a step to see its exact remaining goals."));
    ui["run-origin"].textContent="NO RESULT";ui["run-details"].hidden=true;showError("");emptyGoals();updateControls();
  }
  function markCustom(){state.example=null;ui.example.value="";ui["example-kind"].textContent="CUSTOM TEST";ui["example-description"].textContent="Your own exploratory test. It is not added to any training or evaluation dataset.";}
  function newTest(){ui.theorem.value="";ui.tactics.value="";markCustom();clearResult("Enter your own closed theorem over the natural numbers.");ui.theorem.focus();}
  function loadExample(id) {
    const item=state.examples.find(x=>x.id===id);if(!item)return;
    state.example=item;ui.theorem.value=item.theorem;ui.tactics.value=item.tactics.join("\n");
    ui["example-kind"].textContent=item.provenance==="saved-model"?"RECORDED MODEL PROOF":item.provenance==="negative"?"NEGATIVE EXAMPLE":"HAND-WRITTEN SCRIPT";
    ui["example-description"].textContent=item.description;
    clearResult(item.provenance==="saved-model"?"This script came from the trained model’s verified run. Step through it or run a fresh kernel check below.":"This example is loaded, but it has not been checked in this session.");
  }

  function validateInputs(includeTactics=true) {
    const theorem=ui.theorem.value.trim();
    if(!theorem)throw new Error("Enter a theorem first.");
    if(new TextEncoder().encode(theorem).length>4096)throw new Error("The statement is longer than the 4096-byte limit.");
    const commands=includeTactics?tactics():[];
    const maximum=state.status?.limits?.tactics || 160;
    if(commands.length>maximum)throw new Error(`A script may contain at most ${maximum} tactics.`);
    if(commands.some(x=>new TextEncoder().encode(x).length>512))throw new Error("Each tactic must be at most 512 bytes.");
    return {theorem,tactics:commands};
  }
  function busy(on, message) {
    state.busy=on;ui["progress-area"].hidden=!on;
    if(on){stopPlayback();showError("");ui["progress-message"].textContent=message || "Working…";ui["search-progress"].removeAttribute("value");ui["progress-detail"].textContent="The request is bounded; no automatic retry will be started.";badge("Checking…");}
    updateControls();
  }

  function renderGoals() {
    const count=state.records.length;
    const current=state.position===0?null:state.records[state.position-1];
    let goals=current?.goals_after;
    if(!Array.isArray(goals))goals=state.records[0]?.goals_before || state.result?.initial_goals || state.result?.goals || [];
    ui["goal-title"].textContent=state.position===0?"Initial goal":`After ${current?.tactic || "check"}`;
    ui["goal-count"].textContent=`${goals.length} OPEN GOAL${goals.length===1?"":"S"}`;
    ui.goals.replaceChildren();
    if(goals.length===0){
      const complete=state.result?.kernel_checked===true && state.position===count;
      const box=element("div","empty-state"+(complete?" qed-state":""));
      box.append(element("div","empty-symbol",complete?"✓":"⊢"),element("strong","",complete?"Proof verified by the kernel":"No open goals shown"),element("p","",complete?"The complete certificate was checked against the original theorem.":"A verified label requires the final kernel check, not just an empty goal list."));ui.goals.append(box);
    } else for(const [index,raw] of goals.entries()) {
      const text=typeof raw==="string"?raw:JSON.stringify(raw);
      const card=element("div","goal-card");card.append(element("div","goal-label",`GOAL ${index+1}`));
      const cut=text.indexOf("⊢");const context=cut>=0?text.slice(0,cut).trim():"";const target=cut>=0?text.slice(cut+1).trim():text;
      if(context)card.append(element("div","goal-context",context));
      const line=element("div","goal-target");line.append(element("span","turnstile","⊢"),element("span","",target));card.append(line);ui.goals.append(card);
    }
    ui["trace-position"].textContent=count?`${state.position} / ${count} STEPS`:"INITIAL STATE";
    for(const button of ui.trace.querySelectorAll("button[data-position]")){
      if(Number(button.dataset.position)===state.position)button.setAttribute("aria-current","step");else button.removeAttribute("aria-current");
    }
    updateControls();
  }
  function selectPosition(position){state.position=Math.max(0,Math.min(position,state.records.length));renderGoals();}
  function renderTrace() {
    ui.trace.replaceChildren();
    if(!state.records.length){ui.trace.append(element("li","trace-empty","No tactics have been checked yet. Try one in the proof script."));return;}
    state.records.forEach((record,index)=>{
      const rejected=Boolean(record.error) || ["error","failed","rejected"].includes(record.status);
      const row=element("li","trace-step"+(rejected?" failed":""));const button=element("button","trace-button");button.type="button";button.dataset.position=String(index+1);
      const origin=stepOrigin(record,index);
      button.setAttribute("aria-label",`Step ${index+1}: ${record.tactic}, ${sourceLabels[origin.source]}${rejected?", rejected":""}`);
      const n=Array.isArray(record.goals_after)?record.goals_after.length:null;
      button.append(element("span","step-index",index+1),element("code","",record.tactic),element("span","step-outcome",rejected?"rejected":n===0?"closed":n===null?"checked":`${n} goal${n===1?"":"s"}`));
      button.addEventListener("click",()=>{stopPlayback();selectPosition(index+1);});row.append(button);
      const detail=element("div","step-origin");detail.dataset.source=origin.source;detail.append(sourceBadge(origin.source));
      if(origin.reason){const reason=element("span","step-reason",origin.reason);reason.id=`step-reason-${index+1}`;button.setAttribute("aria-describedby",reason.id);detail.append(reason);}
      row.append(detail);
      if(rejected && record.error)row.append(element("p","step-error",errorText(record.error)));ui.trace.append(row);
    });
  }

  function branchStatus(value) {
    const labels={open:"Open at this step",rejected:"Tactic rejected",duplicate:"Duplicate state",no_progress:"No progress",proved:"Winning endpoint",kernel_rejected:"Kernel rejected",closed_pending_verification:"Closed, pending check",verified_after_search_deadline:"Closed after deadline"};
    return Object.hasOwn(labels,value)?labels[value]:(typeof value==="string"?value.replaceAll("_"," "):"Status not recorded");
  }

  function selectBranch(index,rendering=false) {
    if((state.busy && !rendering) || !Number.isInteger(index) || index<0 || index>=state.branches.length)return;
    state.branchPosition=index;const record=state.branches[index];
    const hasId=typeof record.id==="number" && Number.isInteger(record.id);
    const hasParent=typeof record.parent_id==="number" && Number.isInteger(record.parent_id);
    ui["branch-title"].textContent=hasId?`Branch #${record.id}`:`Tactic attempt ${index+1}`;
    ui["branch-meta"].replaceChildren(sourceBadge(record.source),element("span","branch-status",branchStatus(record.status)));
    const details=[];
    if(hasParent)details.push(`Parent #${record.parent_id}`);
    if(Number.isInteger(record.macro_id))details.push(`Macro #${record.macro_id}${Number.isInteger(record.macro_step)?`, step ${record.macro_step}`:""}`);
    if(details.length)ui["branch-meta"].append(element("span","branch-path",details.join(" · ")));
    if(typeof record.command==="string")ui["branch-meta"].append(element("code","branch-command",record.command));
    ui["branch-reason"].textContent=typeof record.reason==="string"?record.reason:"No explanation was recorded for this transition.";
    const parentExists=hasParent && state.branches.some(item=>item.id!==null && item.id===record.parent_id);
    ui["branch-parent"].textContent=parentExists?`View parent #${record.parent_id}`:record.parent_id===0?"Parent is the initial theorem":hasParent?`Parent #${record.parent_id} is not in this preview`:"No parent snapshot recorded";
    ui["branch-parent"].disabled=!parentExists;
    ui["branch-goals"].replaceChildren();
    if(Array.isArray(record.goals_after)){
      ui["branch-goals"].append(element("p","small-label",`${record.goals_after.length} OPEN GOAL${record.goals_after.length===1?"":"S"} IN THIS SNAPSHOT`));
      if(!record.goals_after.length)ui["branch-goals"].append(element("p","branch-snapshot-note","The recorded snapshot has no open goals. See the final proof trace for the independent verification result."));
      for(const [position,goal] of record.goals_after.entries()){
        const box=element("div","branch-goal");box.append(element("span","small-label",`GOAL ${position+1}`),element("pre","",typeof goal==="string"?goal:JSON.stringify(goal)));ui["branch-goals"].append(box);
      }
    }else{
      ui["branch-goals"].append(element("p","branch-snapshot-note",typeof record.goals_omitted==="string"?record.goals_omitted:"No exact goal snapshot was recorded for this transition. No remaining goals are inferred from its status."));
    }
    for(const button of ui["branch-list"].querySelectorAll("button[data-branch-index]")){
      if(Number(button.dataset.branchIndex)===index)button.setAttribute("aria-current","true");else button.removeAttribute("aria-current");
    }
  }

  function renderBranches() {
    const records=Array.isArray(state.result?.search?.branches)?state.result.search.branches.filter(record=>record && typeof record==="object"):[];
    state.branches=records.slice(0,256);state.branchPosition=-1;ui["branch-list"].replaceChildren();
    const omitted=state.result?.search?.branches_omitted;
    ui["branch-panel"].hidden=!state.branches.length && !(typeof omitted==="number" && omitted>0);
    if(ui["branch-panel"].hidden)return;
    if(!state.branches.length){ui["branch-title"].textContent="No snapshots retained";ui["branch-meta"].replaceChildren();ui["branch-reason"].textContent="The search did not retain a branch snapshot within its log limit.";ui["branch-goals"].replaceChildren(element("p","branch-snapshot-note","No remaining goals are inferred."));}
    const summary=[`${state.branches.length} recorded transition${state.branches.length===1?"":"s"} shown`];
    if(typeof omitted==="number" && omitted>0)summary.push(`${omitted} omitted by the search log byte limit`);
    if(records.length>state.branches.length)summary.push(`${records.length-state.branches.length} more available in the downloaded run`);
    ui["branch-summary"].textContent=summary.join(" · ")+".";
    state.branches.forEach((record,index)=>{
      const row=element("li","branch-row");const button=element("button","branch-button");button.type="button";button.dataset.branchIndex=String(index);
      const identity=Number.isInteger(record.id)?`#${record.id}`:"Attempt";
      const parent=Number.isInteger(record.parent_id)?` ← #${record.parent_id}`:"";
      const heading=element("span","branch-row-heading");heading.append(element("span","branch-identity",identity+parent),sourceBadge(record.source));
      button.append(heading,element("code","",typeof record.command==="string"?record.command:"No tactic recorded"),element("span","branch-status",branchStatus(record.status)));
      button.setAttribute("aria-label",`${identity}${parent}: ${record.command || "transition"}; ${branchStatus(record.status)}`);
      button.addEventListener("click",()=>selectBranch(index));row.append(button);ui["branch-list"].append(row);
    });
    if(state.branches.length)selectBranch(0,true);
  }

  function renderProofSources() {
    ui["proof-sources"].replaceChildren();
    ui["proof-sources"].hidden=state.result?.kernel_checked!==true || state.snapshot?.kind==="manual";
    if(ui["proof-sources"].hidden)return;
    const sources={};state.records.forEach((record,index)=>{const source=stepOrigin(record,index).source;sources[source]=(sources[source] || 0)+1;});
    ui["proof-sources"].append(element("span","small-label","WINNING STEPS"));
    for(const [source,count] of Object.entries(sources))ui["proof-sources"].append(sourceBadge(source,`${sourceLabels[source]} · ${count}`));
  }
  function acceptResult(result,snapshot,kind) {
    if(!result || typeof result!=="object")throw new Error("Missing proof result. No verification claim was accepted.");
    snapshot=snapshot || {};kind=kind==="manual"?"manual":Object.hasOwn(modes,kind)?kind:"model";
    const searched=kind!=="manual";
    const recorded=snapshot.recorded===true;
    state.result=result;state.snapshot={...snapshot,kind,created_at:new Date().toISOString()};
    state.records=(Array.isArray(result.trace)?result.trace:[]).filter(x=>x && typeof x.tactic==="string" && (Array.isArray(x.goals_before)||Array.isArray(x.goals_after)));
    state.position=state.records.length;
    const checked=state.records.filter(x=>!x.error && !["error","failed","rejected"].includes(x.status)).length;
    state.manualCount=searched?0:checked;
    const verified=result.kernel_checked===true;
    const rejected=state.records.some(x=>x.error) || Boolean(result.error);
    const initial=kind==="manual" && !snapshot.tactics?.length && !rejected && !verified;
    badge(verified?"Kernel verified":rejected?"Step rejected":initial?"Goal parsed":searched?"No proof found":"Proof incomplete",verified?"success":rejected?"error":initial?"neutral":"warning");
    let caption;
    if(verified){
      if(!searched)caption="Fresh kernel replay accepted this script. This check did not run the model or Vampire.";
      else if(kind==="model")caption="Fresh model search found a proof, and the native kernel accepted the complete certificate.";
      else {
        const onlyHeuristics=state.records.length>0 && state.records.every((record,index)=>stepOrigin(record,index).source==="heuristic");
        caption=onlyHeuristics?`${modes[kind].name} search found a proof using only native heuristic steps. `:`${modes[kind].name} search found a proof; each winning step’s source is shown below. `;
        caption+="The original kernel independently replayed the complete script.";
        if(result.model_used===false && result.vampire_used===false)caption+=" Neither the model nor Vampire was called.";
      }
    }else caption=initial?"The theorem is well formed. Add tactics to work toward a checked proof.":searched?"The bounded search ended without a verified proof. This is not a disproof of the statement.":rejected?"A tactic was rejected. The successful prefix is retained below; no proof has been accepted.":"The script is valid so far, but open goals remain.";
    if(recorded)caption="Recorded, independently checked proof. The counters and step sources below belong to that saved run; loading it did not start a model or solver. Use Check entire script for a fresh kernel replay.";
    const repeated=searched?repeatedWorkNote(result.search):"";
    if(repeated)caption+=" "+repeated;
    ui["result-caption"].textContent=caption;
    const calls=result.search?.model_calls ?? result.search?.model_generate_calls ?? result.model_generate_calls ?? result.model_calls;
    ui["metric-calls"].textContent=searched?countValue(calls):"—";
    ui["metric-vampire"].textContent=searched?countValue(result.search?.vampire_calls ?? (kind==="model"?0:undefined)):"—";
    ui["metric-states"].textContent=searched?countValue(result.search?.states_expanded):"—";
    ui["metric-attempts"].textContent=searched?countValue(result.search?.tactic_attempts ?? result.search?.candidates_executed):countValue(state.records.length);
    ui["metric-steps"].textContent=String(state.records.length);ui["metric-nodes"].textContent=verified?(result.proof_nodes ?? "—"):"—";
    const cost=result.search?.proof_cost?.final || result.search?.proof_cost?.best_partial;
    ui["certificate-cost"].hidden=!cost;
    ui["certificate-cost"].textContent=cost?`${cost.stage==="final"?"Final certificate":"Retained partial certificate (not a proof)"}: ${countValue(cost.distinct_objects)} distinct proof objects · ${countValue(cost.structural_occurrences)} occurrences · depth ${countValue(cost.depth)}. These counts exclude formula payloads and are not memory estimates.`:"";
    const library=result.search?.lemma_library;
    const imports=library?.imports || result.experimental?.imports;
    const usedLemmas=[...new Set((result.search?.provenance || []).filter(row=>row.command?.startsWith("use ")).map(row=>row.evidence?.lemma || row.command.split(/\s+/)[1]).filter(Boolean))];
    ui["lemma-summary"].hidden=!imports;
    ui["lemma-summary"].textContent=imports?`Checked imports: ${countValue(imports.attempts)} native attempts (${countValue(imports.phases?.independent_replay)} during independent replay).${usedLemmas.length?" Winning lemmas: "+usedLemmas.join(", ")+".":""}`:"";
    const planning=result.search?.structured_planning;
    const plannedSteps=(result.search?.provenance || []).filter(row=>row.evidence?.strategy==="structured_plan").length;
    ui["planner-summary"].hidden=!planning?.enabled;
    ui["planner-summary"].textContent=planning?.enabled?`Structured planning: ${countValue(planning.requests)} requests, ${countValue(planning.plans_generated)} proposals, ${countValue(planning.native_steps_accepted)} accepted native steps across search. ${verified?`${plannedSteps} planned steps in the independently replayed proof.`:"No independently replayed proof was found."} Generated auxiliary statements must also be proved.`:"";
    ui["run-origin"].textContent=recorded?`RECORDED ${modes[kind].name.toUpperCase()} PROOF`:searched?modes[kind].origin:"MANUAL KERNEL REPLAY";
    ui["run-details-content"].textContent=JSON.stringify({origin:recorded?`recorded-${kind}-search`:searched?`fresh-${kind}-search`:"manual-script-replay",recorded_case:snapshot.recorded_case || null,recorded_at:snapshot.recorded_at || null,artifact_sha256:snapshot.artifact_sha256 || null,search_mode:searched?kind:null,settings_profile:result.settings_profile || snapshot.search_profile || null,theorem:result.theorem || snapshot.theorem,model:result.model || null,model_used:result.model_used ?? null,vampire_used:result.vampire_used ?? null,proof_sources:result.proof_sources || null,search:result.search || null,kernel_checked:verified,proof_nodes:result.proof_nodes ?? null,status:result.status,resources:result.resources || null,execution:result.execution || null},null,2);
    ui["run-details"].hidden=false;
    if(searched && Array.isArray(result.commands) && result.commands.length){
      ui.tactics.value=result.commands.join("\n");state.manualCount=0;state.example=null;ui.example.value="";
      ui["example-kind"].textContent=recorded?`RECORDED ${modes[kind].name.toUpperCase()} PROOF`:modes[kind].script;
      ui["example-description"].textContent=recorded?"A saved successful search, with its original component counts. Edit the statement to try a variant, or run a fresh search that ignores this saved script.":kind==="model"?"These commands came from this local search. A later manual replay checks the script without making another model call.":"These commands came from the selected search method; each winning step’s source is recorded in the trace. A manual replay runs neither the model nor Vampire.";
    }
    renderTrace();renderProofSources();renderBranches();renderGoals();
  }

  async function replay(mode) {
    if(state.busy)return;
    let input;
    try{input=validateInputs();}catch(error){showError(errorText(error));return;}
    const limit=mode==="initial"?0:mode==="step"?Math.min(state.manualCount+1,input.tactics.length):input.tactics.length;
    const request={theorem:input.theorem,tactics:input.tactics.slice(0,limit)};
    const experimental=experimentalSelection();if(experimental)request.experimental=experimental;
    busy(true,mode==="initial"?"Parsing the initial goal…":"Checking the proof script…");
    try{const response=await api("/api/replay",request);acceptResult(response.result,request,"manual");}
    catch(error){clearResult("This request did not produce an accepted result.");showError(errorText(error));badge("Check failed","error");}
    finally{busy(false);}
  }

  async function pollJob(generation) {
    if(!state.job || generation!==state.generation)return;
    try {
      const response=await api(`/api/jobs/${encodeURIComponent(state.job)}`);const job=response.job;
      if(!job || generation!==state.generation)return;
      const progress=job.progress || {};const calls=progress.model_calls ?? progress.model_generate_calls;
      ui["progress-message"].textContent=progress.message || (progress.phase==="loading_model"?"Loading the local model…":"Searching for a proof…");
      const elapsed=job.elapsed_seconds ?? ((Date.now()-state.started)/1000);
      for(const [key,value,id] of [["model",calls,"metric-calls"],["vampire",progress.vampire_calls,"metric-vampire"],["states",progress.states_expanded,"metric-states"],["attempts",progress.tactic_attempts,"metric-attempts"]]){
        if(countValue(value)!=="—"){state.progressCounts[key]=value;ui[id].textContent=countValue(value);}
      }
      const parts=[`${Math.round(elapsed)} seconds elapsed`];
      for(const [key,label] of [["model","model calls"],["vampire","Vampire runs"],["states","states explored"]])if(Object.hasOwn(state.progressCounts,key))parts.push(`${state.progressCounts[key]} ${label}`);
      const repeated=repeatedWorkNote(progress);
      if(repeated)parts.push(repeated);
      ui["progress-detail"].textContent=parts.join(" · ");
      const mode=state.snapshot?.search_mode || "model";
      if(mode==="model" && typeof calls==="number"){ui["search-progress"].max=Number(ui["call-budget"].value);ui["search-progress"].value=calls;}
      else ui["search-progress"].removeAttribute("value");
      if(["completed","failed","cancelled"].includes(job.state)) {
        if(job.state==="completed" && job.result)acceptResult(job.result,state.snapshot,job.result.search_mode || job.result.kind || mode);
        else {badge(job.state==="cancelled"?"Search cancelled":"Search stopped","warning");ui["result-caption"].textContent=job.state==="cancelled"?"The search was cancelled. No proof result was accepted.":"The search request ended without an accepted result. You can still inspect and check proof scripts.";if(job.error)showError(errorText(job.error));}
        state.job=null;busy(false);return;
      }
      state.pollTimer=setTimeout(()=>pollJob(generation),750);
    } catch(error) {showError(errorText(error));badge("Connection lost","error");ui["result-caption"].textContent="The search status is unknown. The server’s time limit still applies. No proof has been accepted.";busy(false);}
  }
  async function search() {
    const mode=selectedMode();if(state.busy || !modeAvailable(mode))return;
    let input;try{input=validateInputs(false);}catch(error){showError(errorText(error));return;}
    clearResult(`A fresh ${modes[mode].name.toLowerCase()} search will start from your theorem; any loaded example script is ignored.`);
    const request={theorem:input.theorem,max_model_calls:Number(ui["call-budget"].value),beam_width:Number(ui["beam-width"].value)};
    if(state.status?.limits?.profiles)request.search_profile=ui["search-profile"].value;
    if(state.status?.search_modes || mode!=="model")request.search_mode=mode;
    const experimental=experimentalSelection();if(experimental)request.experimental=experimental;
    state.snapshot=request;state.started=Date.now();state.generation++;busy(true,mode==="model"?"Starting the local model…":`Starting ${modes[mode].name.toLowerCase()} proof search…`);
    ui["search-progress"].setAttribute("aria-label",mode==="model"?"Model calls used from the selected budget":"Bounded proof search in progress");
    try{const response=await api("/api/search",request);if(typeof response.job_id!=="string")throw new Error("No search job was created.");state.job=response.job_id;updateControls();await pollJob(state.generation);}
    catch(error){state.job=null;showError(errorText(error));badge("Could not start","error");busy(false);}
  }
  async function cancel() {
    if(!state.job)return;ui["cancel-search"].disabled=true;
    try{await api(`/api/jobs/${encodeURIComponent(state.job)}/cancel`,{});ui["progress-message"].textContent="Stopping the owned search process…";}
    catch(error){showError(errorText(error));ui["cancel-search"].disabled=false;}
  }

  async function refreshStatus() {
    try {
      const data=await api("/api/status");state.status=data;state.token=data.csrf_token || "";
      const model=data.model || {};ui["model-name"].textContent=model.name || "Mixed retention adapter";ui["model-detail"].textContent=model.detail || (model.available?"Local weights available; loaded when you start a search.":"The live model is not configured.");
      const vampire=data.vampire || {};
      ui["vampire-status"].textContent=`${vampire.name || "Vampire"} · ${vampire.available===true?"ready":data.vampire?"unavailable":"not reported"}`;
      ui["vampire-status"].className=vampire.available===true?"component-ready":"component-unavailable";
      ui["vampire-detail"].textContent=vampire.detail || "This server did not report a local Vampire runtime. Select another available method or check a script manually.";
      const components=["Kernel"];if(model.available===true)components.push("model");if(vampire.available===true)components.push("Vampire");
      ui["connection-label"].textContent=components.join(" + ")+" ready";ui["connection-dot"].className="connection-dot ready";updateControls();
    }catch(error){state.status=null;ui["connection-label"].textContent="Server unavailable";ui["connection-dot"].className="connection-dot failed";showError(errorText(error));updateControls();}
  }
  function downloadRun() {
    if(!state.result || state.busy)return;
    const raw=JSON.stringify({schema:"hydra-playground-run-v1",input:state.snapshot,result:state.result,claim:"Exploratory local run; not training data or a benchmark score."},null,2);
    const url=URL.createObjectURL(new Blob([raw],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download="hydra-proof-run.json";document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  async function loadShowcase(item,withProof) {
    if(state.busy)return;
    busy(true,"Loading the recorded theorem…");
    try{
      const response=await api(`/api/showcase/${encodeURIComponent(item.id)}`);
      const record=response.record;
      if(!record || record.case_id!==item.id || record.theorem!==item.theorem || record.result?.kernel_checked!==true)throw new Error("The saved proof does not match this gallery entry.");
      ui.theorem.value=record.theorem;ui.tactics.value=withProof?record.result.commands.join("\n"):"";
      markCustom();
      ui["search-mode"].value=record.request.search_mode;
      ui["experimental-engine"].checked=Boolean(record.request.experimental);
      ui["experimental-lemmas"].checked=record.request.experimental?.lemmas!==false;
      ui["experimental-planner"].value=record.request.experimental?.planner || "off";
      ui["search-profile"].value=record.request.search_profile || "standard";
      renderProfile();
      ui["call-budget"].value=String(record.request.max_model_calls);
      ui["beam-width"].value=String(record.request.beam_width);
      if(withProof)acceptResult(record.result,{...record.request,recorded:true,recorded_case:item.id,recorded_at:record.recorded_at_utc,artifact_sha256:item.artifact_sha256},record.request.search_mode);
      else clearResult("The theorem and its recorded settings are loaded. Find a proof starts a new search with no supplied script.");
      document.querySelector(".workspace").scrollIntoView({block:"start",behavior:"smooth"});
    }catch(error){showError(errorText(error));}
    finally{busy(false);}
  }

  async function loadShowcaseCatalog() {
    try{
      const catalog=await api("/api/showcase");
      if(catalog.schema!=="hydra-verified-showcase-v1" || !Array.isArray(catalog.cases))throw new Error("The verified example catalogue is invalid.");
      state.showcase=catalog.cases.filter(item=>item.kernel_verified===true && item.independent_replay===true);
      ui["showcase-cases"].replaceChildren();
      for(const item of state.showcase){
        const card=element("article","showcase-card");card.dataset.caseId=item.id;
        const tags=element("div","showcase-tags");
        tags.append(element("span","source-badge source-heuristic","KERNEL VERIFIED"));
        for(const tag of item.tags || [])tags.append(element("span","source-badge",tag));
        card.append(tags,element("h3","",item.title),element("p","showcase-math",item.display),element("p","showcase-summary",item.description));
        const sources=Object.keys(item.proof_sources || {});
        const contribution=sources.length===1 && sources[0]==="heuristic"?"Native tactic proof":sources.map(source=>sourceLabels[source] || source).join(" + ")+" steps";
        card.append(element("div","showcase-stats",`${item.proof_steps} steps · ${Number(item.proof_nodes).toLocaleString()} proof nodes · ${Number(item.elapsed_seconds).toFixed(1)}s\n${contribution} · model ${countValue(item.model_calls)} / Vampire ${countValue(item.vampire_calls)}`));
        const actions=element("div","showcase-actions");const inspect=element("button","button secondary","Inspect proof →");inspect.type="button";inspect.dataset.showcaseAction="proof";inspect.addEventListener("click",()=>loadShowcase(item,true));
        const load=element("button","text-button","Load theorem");load.type="button";load.dataset.showcaseAction="theorem";load.addEventListener("click",()=>loadShowcase(item,false));actions.append(inspect,load);card.append(actions);ui["showcase-cases"].append(card);
      }
      ui["showcase-count"].textContent=`${state.showcase.length} VERIFIED`;
      ui["showcase"].hidden=!state.showcase.length;
      if(catalog.note)ui["showcase-note"].textContent=catalog.note;
    }catch(error){ui["showcase"].hidden=false;ui["showcase-count"].textContent="UNAVAILABLE";ui["showcase-count"].className="badge warning";ui["showcase-note"].textContent="Verified examples could not be loaded: "+errorText(error);}
    updateControls();
  }

  ui.example.addEventListener("change",()=>ui.example.value?loadExample(ui.example.value):newTest());
  ui.theorem.addEventListener("input",()=>{markCustom();clearResult();});
  ui.tactics.addEventListener("input",()=>{markCustom();clearResult("The script changed. Check it again to see the current proof state.");});
  ui["search-mode"].addEventListener("change",()=>clearResult("The search method changed. Start a new search or check the current script manually."));
  for(const id of ["experimental-engine","experimental-lemmas","experimental-planner"])ui[id].addEventListener("change",()=>{
    if(ui["experimental-engine"].checked && ["model","hybrid"].includes(selectedMode()))ui["search-mode"].value=state.status?.search_modes?.symbolic?.available?"symbolic":"heuristic";
    clearResult("The experimental engine selection changed. Start a fresh search or replay; the saved model remains on its original engine.");
  });
  ui["search-profile"].addEventListener("change",()=>{renderProfile();clearResult("The experiment profile changed. A fresh search will use its displayed bounds.");});
  for(const id of ["call-budget","beam-width"])ui[id].addEventListener("change",()=>clearResult("The search budget changed. Start a fresh search with the new settings."));
  ui["new-test"].addEventListener("click",newTest);
  ui["inspect-goal"].addEventListener("click",()=>replay("initial"));ui["step-tactic"].addEventListener("click",()=>replay("step"));ui["check-script"].addEventListener("click",()=>replay("all"));
  ui.search.addEventListener("click",search);ui["cancel-search"].addEventListener("click",cancel);ui["download-run"].addEventListener("click",downloadRun);
  ui["branch-parent"].addEventListener("click",()=>{const record=state.branches[state.branchPosition];if(record)selectBranch(state.branches.findIndex(item=>item.id!==null && item.id===record.parent_id));});
  ui["trace-start"].addEventListener("click",()=>{stopPlayback();selectPosition(0);});ui["trace-prev"].addEventListener("click",()=>{stopPlayback();selectPosition(state.position-1);});ui["trace-next"].addEventListener("click",()=>{stopPlayback();selectPosition(state.position+1);});ui["trace-end"].addEventListener("click",()=>{stopPlayback();selectPosition(state.records.length);});
  ui["trace-play"].addEventListener("click",()=>{if(state.playTimer){stopPlayback();return;}if(state.position>=state.records.length)selectPosition(0);ui["trace-play"].textContent="Pause steps";state.playTimer=setInterval(()=>{selectPosition(state.position+1);if(state.position>=state.records.length)stopPlayback();},1100);});
  ui.theorem.addEventListener("keydown",event=>{if((event.ctrlKey||event.metaKey)&&event.key==="Enter"){event.preventDefault();search();}});
  ui.tactics.addEventListener("keydown",event=>{if((event.ctrlKey||event.metaKey)&&event.key==="Enter"){event.preventDefault();replay("all");}});
  window.addEventListener("beforeunload",()=>{stopPlayback();if(state.pollTimer)clearTimeout(state.pollTimer);});

  async function init() {
    updateControls();
    const statusTask=refreshStatus();
    const showcaseTask=loadShowcaseCatalog();
    try{const data=await api("/api/examples");state.examples=Array.isArray(data.examples)?data.examples:[];ui.example.replaceChildren(new Option("Your own theorem", ""));for(const item of state.examples)ui.example.add(new Option(item.title,item.id));if(state.examples.length){ui.example.value=state.examples[0].id;loadExample(state.examples[0].id);}}
    catch(error){ui.example.replaceChildren(new Option("Your own theorem",""));showError(errorText(error));}
    await Promise.all([statusTask,showcaseTask]);updateControls();setInterval(()=>{if(!state.busy)refreshStatus();},15000);
  }
  init();
})();
