(function () {
  "use strict";

  const POLL_VISIBLE_MS = 5000;
  const POLL_HIDDEN_MS = 30000;
  const FETCH_TIMEOUT_MS = 15000;
  const MANUAL_REFRESH_POLL_MS = 1000;
  const MANUAL_REFRESH_WAIT_MS = 60000;
  const SVG_NS = "http://www.w3.org/2000/svg";
  const state = {
    timer: null,
    fetching: false,
    lastData: null,
    samples: [],
    sampleIndex: 0,
    targetVisible: false,
    logStream: "combined",
    logScrollPaused: false,
    refreshPending: false,
    refreshBaseline: null,
    refreshDeadline: 0,
    queuedManualRefresh: false
  };

  function element(id) { return document.getElementById(id); }
  function setText(id, value) { element(id).textContent = value === null || value === undefined || value === "" ? "—" : String(value); }
  function number(value, fallback) { return typeof value === "number" && Number.isFinite(value) ? value : fallback; }
  function object(value) { return value && typeof value === "object" && !Array.isArray(value) ? value : {}; }
  function array(value) { return Array.isArray(value) ? value : []; }
  function lines(value) {
    if (Array.isArray(value)) return value.map(String);
    if (typeof value === "string") return value.split(/\r?\n/).filter(function (line) { return line.length > 0; });
    return [];
  }
  function first() {
    for (let index = 0; index < arguments.length; index += 1) {
      const value = arguments[index];
      if (value !== undefined && value !== null && value !== "") return value;
    }
    return null;
  }

  function formatDuration(seconds) {
    const value = Math.max(0, Math.round(number(seconds, 0)));
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const remainder = value % 60;
    if (hours) return hours + "h " + String(minutes).padStart(2, "0") + "m";
    if (minutes) return minutes + "m " + String(remainder).padStart(2, "0") + "s";
    return remainder + "s";
  }

  function formatCompact(value) {
    const numeric = number(value, null);
    if (numeric === null) return "—";
    if (Math.abs(numeric) >= 1000000) return (numeric / 1000000).toFixed(2).replace(/\.00$/, "") + "M";
    if (Math.abs(numeric) >= 1000) return (numeric / 1000).toFixed(1).replace(/\.0$/, "") + "k";
    return String(numeric);
  }

  function connectionState(kind, message) {
    const dot = element("connection-dot");
    dot.className = "status-dot is-" + kind;
    setText("connection-label", message);
  }

  function hasSuccessfulSnapshot(data) {
    return number(object(object(data).connection).age_seconds, null) !== null;
  }

  function snapshotStamp(data) {
    const value = object(data);
    return first(value.fetched_at, object(value.connection).last_success_at);
  }

  function phaseOrder(phase) {
    const normalized = String(phase || "optimizer").toLowerCase();
    if (["complete", "completed"].includes(normalized)) return 5;
    if (["verification", "verifying", "finalizing", "incomplete"].includes(normalized)) return 4;
    if (["evaluation", "evaluating", "eval", "evaluating-and-admitting"].includes(normalized)) return 3;
    if (["save", "saving"].includes(normalized)) return 2;
    if (["failed", "unreachable", "unknown"].includes(normalized)) return 0;
    return 1;
  }

  function phaseTone(phase) {
    const normalized = String(phase || "").toLowerCase();
    if (["complete", "completed"].includes(normalized)) return "is-complete";
    if (["failed", "unreachable"].includes(normalized)) return "is-danger";
    if (["queued", "incomplete", "suspended"].includes(normalized)) return "is-warning";
    if (["training", "optimizer"].includes(normalized)) return "is-running";
    return "";
  }

  function isOptimizerPhase(phase) {
    return ["optimizer", "training"].includes(String(phase || "").toLowerCase());
  }

  function updatePhaseRail(phase) {
    const activeOrder = phaseOrder(phase);
    document.querySelectorAll(".phase-step").forEach(function (node, index) {
      const order = index + 1;
      node.classList.toggle("is-active", order === Math.min(activeOrder, 4));
      node.classList.toggle("is-complete", order < activeOrder || activeOrder === 5);
    });
  }

  function lossPoints(data) {
    const loss = object(data.loss);
    const raw = array(first(loss.points, data.losses, object(data.metrics).losses));
    return raw.map(function (record) {
      const value = object(record);
      return {
        step: number(first(value.step, value.global_step), null),
        loss: number(first(value.loss, value.train_loss), null),
        learningRate: number(first(value.learning_rate, value.lr), null),
        gradientNorm: number(first(value.grad_norm, value.gradient_norm), null)
      };
    }).filter(function (record) { return record.step !== null && record.loss !== null; });
  }

  function svgNode(name, attributes) {
    const node = document.createElementNS(SVG_NS, name);
    Object.keys(attributes || {}).forEach(function (key) { node.setAttribute(key, String(attributes[key])); });
    return node;
  }

  function renderLossChart(points, totalSteps) {
    const svg = element("loss-chart");
    svg.replaceChildren();
    const table = element("loss-table-body");
    table.replaceChildren();
    element("chart-empty").hidden = points.length > 0;
    if (!points.length) return;

    const width = 760;
    const height = 260;
    const pad = { left: 48, right: 20, top: 20, bottom: 34 };
    const losses = points.map(function (point) { return point.loss; });
    let minimum = Math.min.apply(null, losses);
    let maximum = Math.max.apply(null, losses);
    if (maximum === minimum) { maximum += .1; minimum -= .1; }
    const margin = (maximum - minimum) * .12;
    minimum -= margin;
    maximum += margin;
    const x = function (step) { return pad.left + (step / Math.max(1, totalSteps)) * (width - pad.left - pad.right); };
    const y = function (loss) { return pad.top + (maximum - loss) / (maximum - minimum) * (height - pad.top - pad.bottom); };

    for (let line = 0; line <= 4; line += 1) {
      const at = pad.top + line * (height - pad.top - pad.bottom) / 4;
      svg.appendChild(svgNode("line", { x1: pad.left, y1: at, x2: width - pad.right, y2: at, stroke: "rgba(125,211,252,.13)", "stroke-width": 1 }));
      const label = svgNode("text", { x: pad.left - 8, y: at + 4, fill: "#94aebd", "font-size": 10, "text-anchor": "end" });
      label.textContent = (maximum - line * (maximum - minimum) / 4).toFixed(3);
      svg.appendChild(label);
    }
    [0, .25, .5, .75, 1].forEach(function (ratio) {
      const step = Math.round(totalSteps * ratio);
      const label = svgNode("text", { x: x(step), y: height - 10, fill: "#94aebd", "font-size": 10, "text-anchor": "middle" });
      label.textContent = String(step);
      svg.appendChild(label);
    });
    svg.appendChild(svgNode("polyline", {
      points: points.map(function (point) { return x(point.step) + "," + y(point.loss); }).join(" "),
      fill: "none", stroke: "#38bdf8", "stroke-width": 3, "stroke-linejoin": "round", "stroke-linecap": "round"
    }));
    points.forEach(function (point) {
      const circle = svgNode("circle", { cx: x(point.step), cy: y(point.loss), r: 4, fill: "#07131b", stroke: "#7dd3fc", "stroke-width": 2 });
      const title = svgNode("title", {});
      title.textContent = "Step " + point.step + ": loss " + point.loss.toFixed(5);
      circle.appendChild(title);
      svg.appendChild(circle);

      const row = document.createElement("tr");
      [point.step, point.loss.toFixed(6), point.learningRate === null ? "—" : point.learningRate.toExponential(3)].forEach(function (value) {
        const cell = document.createElement("td");
        cell.textContent = String(value);
        row.appendChild(cell);
      });
      table.appendChild(row);
    });
  }

  function normalizeSamples(data) {
    return array(first(data.samples, object(data.dataset).samples, object(data.corpus).samples)).map(function (record) {
      const sample = object(record);
      return {
        id: first(sample.example_id, sample.id, "unknown"),
        theorem: first(sample.theorem, sample.name, "unnamed theorem"),
        family: first(sample.family, sample.lineage, "reported corpus"),
        formula: first(sample.formula, sample.statement, "—"),
        state: first(sample.focused_state, sample.state, sample.goal, "—"),
        library: array(first(sample.library, sample.retrieved_library, sample.allowed_theorems)).map(function (entry) {
          const record = object(entry);
          if (Object.keys(record).length) return String(first(record.name, "lemma")) + (record.statement ? " : " + record.statement : "");
          return String(entry);
        }),
        completion: first(sample.completion, sample.target, sample.next_tactic, "—")
      };
    });
  }

  function renderSample(resetTarget) {
    const count = state.samples.length;
    element("sample-previous").disabled = count < 2;
    element("sample-next").disabled = count < 2;
    setText("sample-position", count ? (state.sampleIndex + 1) + " / " + count : "0 / 0");
    if (!count) {
      state.sampleIndex = 0;
      state.targetVisible = false;
      setText("sample-theorem", "No corpus preview available");
      setText("sample-family", "—");
      setText("sample-formula", "—");
      setText("sample-state", "—");
      setText("sample-completion", "—");
      const emptyList = element("sample-library");
      emptyList.replaceChildren();
      const emptyItem = document.createElement("li");
      emptyItem.textContent = "No library preview available";
      emptyList.appendChild(emptyItem);
      element("target-answer").hidden = true;
      element("reveal-target").disabled = true;
      element("reveal-target").setAttribute("aria-expanded", "false");
      setText("reveal-target", "No supervised target available");
      return;
    }
    element("reveal-target").disabled = false;
    const sample = state.samples[state.sampleIndex];
    setText("sample-theorem", sample.theorem);
    setText("sample-family", sample.family);
    setText("sample-formula", sample.formula);
    setText("sample-state", Array.isArray(sample.state) ? sample.state.join("\n") : sample.state);
    setText("sample-completion", sample.completion);
    const list = element("sample-library");
    list.replaceChildren();
    const entries = sample.library.length ? sample.library : ["No retrieved lemma preview in this record"];
    entries.forEach(function (entry) {
      const item = document.createElement("li");
      item.textContent = entry;
      list.appendChild(item);
    });
    if (resetTarget !== false) state.targetVisible = false;
    element("target-answer").hidden = !state.targetVisible;
    element("reveal-target").setAttribute("aria-expanded", String(state.targetVisible));
    setText("reveal-target", state.targetVisible ? "Hide supervised next tactic" : "Reveal supervised next tactic");
  }

  function normalizeLogs(data) {
    const logs = object(data.logs);
    return {
      stdout: lines(first(logs.stdout, logs.events)),
      stderr: lines(first(logs.stderr, logs.progress))
    };
  }

  function renderLogs(data) {
    const logs = normalizeLogs(data);
    let lines;
    if (state.logStream === "stdout") lines = logs.stdout;
    else if (state.logStream === "stderr") lines = logs.stderr;
    else if (logs.stdout.length || logs.stderr.length) {
      lines = ["── stdout events ──"].concat(
        logs.stdout.map(function (line) { return "OUT  " + line; }),
        ["", "── stderr progress ──"],
        logs.stderr.map(function (line) { return "ERR  " + line; })
      );
    } else lines = [];
    const pre = element("live-log");
    pre.textContent = lines.length ? lines.join("\n") : "No log lines available yet.";
    if (!state.logScrollPaused) pre.scrollTop = pre.scrollHeight;
  }

  function renderSnapshots(data, currentStep) {
    const snapshotRecord = object(data.snapshots);
    const snapshots = Array.isArray(data.snapshots) ? data.snapshots : array(snapshotRecord.published);
    const published = new Set(snapshots.map(function (item) { return number(object(item).step, null); }).filter(function (value) { return value !== null; }));
    const planned = array(first(snapshotRecord.planned_steps, object(data.schedule).recovery_steps, object(data.progress).recovery_steps));
    const plannedSteps = planned.map(Number).filter(function (step) { return Number.isFinite(step); });
    const list = element("snapshot-list");
    list.replaceChildren();
    const missingSteps = plannedSteps.filter(function (step) { return !published.has(step); });
    const nextStep = missingSteps.find(function (step) { return step > currentStep; });
    plannedSteps.forEach(function (step) {
      const item = document.createElement("li");
      item.dataset.step = String(step);
      const label = document.createElement("span");
      label.textContent = String(step);
      const status = document.createElement("strong");
      if (published.has(step)) { item.className = "is-published"; status.textContent = "published ✓"; }
      else if (step === nextStep) { item.className = "is-next"; status.textContent = "next"; }
      else status.textContent = step <= currentStep ? "not observed" : "planned";
      item.append(label, status);
      list.appendChild(item);
    });
    const publishedPlanned = plannedSteps.filter(function (step) { return published.has(step); }).length;
    setText("metric-snapshots", plannedSteps.length ? publishedPlanned + " / " + plannedSteps.length : "awaiting");
    setText("metric-snapshot-detail", !plannedSteps.length ? "no recovery plan reported" : !missingSteps.length ? "all planned snapshots published" : nextStep !== undefined ? "next snapshot at step " + nextStep : missingSteps.length + " planned snapshot" + (missingSteps.length === 1 ? "" : "s") + " not observed");
  }

  function render(data) {
    state.lastData = data;
    const job = object(data.job);
    const progress = object(data.progress);
    const schedule = object(data.schedule);
    const model = object(data.model);
    const resources = object(data.resources);
    const source = object(data.source);
    const loss = object(data.loss);
    const connection = object(data.connection);
    const artifacts = object(data.artifacts);
    const reportedStep = number(first(progress.step, progress.current_step), null);
    const reportedTotal = number(first(progress.total_steps, progress.total, schedule.expected_optimizer_steps, schedule.optimizer_steps), null);
    const step = Math.max(0, reportedStep === null ? 0 : reportedStep);
    const total = reportedTotal === null ? 1 : Math.max(1, reportedTotal);
    const reportedPercent = number(progress.percent, null);
    const percent = Math.min(100, Math.max(0, reportedPercent === null ? (reportedTotal === null ? 0 : step / total * 100) : reportedPercent));
    const phase = String(first(progress.phase, progress.stage, job.state === "COMPLETED" ? "complete" : "optimizer"));

    setText("job-id", first(job.id, job.job_id, "—"));
    setText("job-node", first(job.node, job.node_list, job.node_or_reason, "—"));
    setText("job-state", first(job.state, "UNKNOWN"));
    const phaseChip = element("phase-chip");
    phaseChip.className = "phase-chip " + phaseTone(phase);
    setText("phase-chip", phase.replaceAll("-", " "));
    setText("progress-number", reportedTotal === null ? "— / —" : step + " / " + total);
    setText("progress-percent", reportedTotal === null ? "awaiting" : percent.toFixed(1) + "%");
    const configuredAccumulation = number(schedule.gradient_accumulation_steps, null);
    setText("progress-caption", isOptimizerPhase(phase) ? configuredAccumulation === null ? "Optimizer updates · accumulation awaiting schedule" : "Optimizer updates · configured accumulation " + configuredAccumulation : "Current phase: " + phase.replaceAll("-", " "));
    const progressElement = element("optimizer-progress");
    progressElement.max = total;
    progressElement.value = step;
    progressElement.textContent = reportedTotal === null ? "awaiting" : percent.toFixed(1) + "%";
    progressElement.setAttribute("aria-valuetext", reportedTotal === null ? "Optimizer schedule unavailable" : "Optimizer step " + step + " of " + total + ", " + percent.toFixed(1) + " percent");
    updatePhaseRail(phase);

    const identityPresent = artifacts.run_identity === true;
    setText("identity-eyebrow", identityPresent ? "Run identity present" : "Run evidence");
    const seal = element("seal-mark");
    seal.className = "seal-mark" + (identityPresent ? " is-present" : "");
    seal.title = identityPresent ? "A run identity record is present" : "No run identity record is available";
    setText("seal-mark", identityPresent ? "identity present" : "unavailable");
    setText("sample-eyebrow", identityPresent ? "Reported training corpus" : "Corpus evidence");

    const secondsPerStep = number(first(progress.seconds_per_step, progress.step_seconds), null);
    const etaSeconds = number(first(progress.eta_seconds, progress.optimizer_eta_seconds), null);
    setText("metric-step-time", secondsPerStep === null ? "—" : secondsPerStep.toFixed(1) + " s");
    setText("metric-eta", etaSeconds === null ? "—" : formatDuration(etaSeconds));
    setText("metric-eta-detail", isOptimizerPhase(phase) ? "then evaluation + verification" : "current phase: " + phase);

    const points = lossPoints(data);
    const latest = points.length ? points[points.length - 1] : null;
    if (latest) {
      setText("metric-loss", latest.loss.toFixed(5));
      setText("metric-loss-detail", "exact record at step " + latest.step);
      setText("metric-lr", latest.learningRate === null ? "—" : latest.learningRate.toExponential(2));
    } else {
      setText("metric-loss", "awaiting");
      const smoke = number(first(object(loss.smoke).training_loss, loss.smoke_loss, object(data.metrics).smoke_loss), null);
      const lossStatus = String(first(loss.status, "unavailable")).toLowerCase();
      const lossMessages = {
        buffered: "Production loss is buffered until exact trainer records flush",
        pending: "Waiting for the first exact production-loss record",
        unavailable: "Production-loss evidence is unavailable",
        "completed-evidence": "No plottable loss records in terminal evidence"
      };
      const lossMessage = first(lossMessages[lossStatus], "No exact production-loss record is available");
      setText("metric-loss-detail", smoke === null ? lossMessage : "admission smoke only: " + smoke.toFixed(5));
      setText("chart-empty", lossMessage + ". The chart will backfill when evidence arrives.");
      setText("metric-lr", "awaiting");
    }
    renderLossChart(points, total);
    renderSnapshots(data, step);

    setText("model-chip", first(model.display_name, model.name, model.id, "Awaiting model identity"));
    setText("fact-model", first(model.display_name, model.name, model.id, "awaiting identity"));
    const rank = first(model.lora_rank, object(model.lora).rank);
    const alpha = first(model.lora_alpha, object(model.lora).alpha);
    setText("fact-adapter", rank === null && alpha === null ? "awaiting configuration" : "LoRA r" + first(rank, "—") + " · α" + first(alpha, "—"));
    setText("fact-hardware", first(job.hardware, model.hardware, job.gpu, "awaiting allocation"));
    const gpuAverage = number(resources.gpu_utilization_percent, null);
    const gpuPeak = number(resources.max_gpu_utilization_percent, null);
    const gpuMemory = first(resources.gpu_memory, null);
    setText("fact-gpu-load", gpuAverage === null ? "awaiting telemetry" : gpuAverage + "% avg" + (gpuPeak === null ? "" : " · " + gpuPeak + "% peak") + (gpuMemory === null ? "" : " · " + gpuMemory));
    const elapsedSeconds = number(job.elapsed_seconds, null);
    setText("fact-runtime", first(job.elapsed, elapsedSeconds === null ? null : formatDuration(elapsedSeconds), "—"));
    const trainRows = first(schedule.train_rows);
    const evalRows = first(schedule.eval_rows);
    setText("fact-examples", trainRows === null && evalRows === null ? "awaiting schedule" : formatCompact(trainRows) + " train · " + formatCompact(evalRows) + " eval");
    setText("fact-tokens", formatCompact(first(schedule.train_tokens)));
    const accumulation = number(schedule.gradient_accumulation_steps, null);
    const microBatches = number(first(schedule.micro_batches_per_epoch, schedule.train_rows), null);
    const finalWindow = accumulation === null || microBatches === null ? null : (microBatches % accumulation || accumulation);
    setText("fact-accumulation", accumulation === null ? "—" : "up to " + accumulation + (finalWindow === null ? "" : " · final " + finalWindow));
    setText("sample-note", accumulation === null ? "Representative reported examples—not the exact shuffled microbatch. Accumulation details are unavailable." : "Representative reported examples—not the exact shuffled microbatch. Updates aggregate up to " + accumulation + " microbatches" + (finalWindow === null ? "." : "; the final partial window has " + finalWindow + "."));
    const preparationJob = first(source.preparation_job_id, source.prepare_job_id, object(data.preparation).job_id);
    setText("fact-preparation", preparationJob === null ? "—" : "job " + preparationJob);
    setText("fact-source", String(first(source.commit, source.source_commit, "—")).slice(0, 12));

    const samples = normalizeSamples(data);
    const previousId = state.samples[state.sampleIndex] && state.samples[state.sampleIndex].id;
    state.samples = samples;
    const sameIndex = samples.findIndex(function (sample) { return sample.id === previousId; });
    state.sampleIndex = sameIndex >= 0 ? sameIndex : Math.max(0, Math.min(state.sampleIndex, samples.length - 1));
    renderSample(sameIndex < 0);
    renderLogs(data);

    const stale = connection.stale === true || data.stale === true;
    const reportedConnectionState = String(first(connection.state, connection.status, stale ? "stale" : "live")).toLowerCase();
    const hasCachedSnapshot = stale && number(connection.age_seconds, null) !== null;
    if (["connecting", "recorded"].includes(reportedConnectionState)) connectionState("connecting", first(connection.message, "Connecting to WMI…"));
    else if (reportedConnectionState === "error" && !hasCachedSnapshot) connectionState("error", first(connection.message, "WMI collector unavailable"));
    else if (stale) connectionState("stale", hasCachedSnapshot ? "Cached · WMI link stale" : first(connection.message, "WMI snapshot unavailable"));
    else connectionState("live", "Live · WMI " + first(job.node, job.node_or_reason, "cluster"));
    const fetched = first(data.fetched_at, connection.last_success_at);
    const age = number(connection.age_seconds, null);
    const ageLabel = stale && age !== null ? " · " + formatDuration(age) + " old" : "";
    setText("freshness-label", hasCachedSnapshot && fetched ? "Snapshot " + new Date(fetched).toLocaleTimeString() + " · cached" + ageLabel : !stale && fetched ? "Snapshot " + new Date(fetched).toLocaleTimeString() + " · live" : first(connection.message, "No live snapshot received yet"));
  }

  async function fetchStatus(manual) {
    if (state.fetching) {
      if (manual) {
        state.queuedManualRefresh = true;
        connectionState("connecting", "Fresh WMI read queued…");
      }
      return;
    }
    state.fetching = true;
    if (manual) {
      state.refreshPending = true;
      state.refreshBaseline = hasSuccessfulSnapshot(state.lastData) ? snapshotStamp(state.lastData) : null;
      state.refreshDeadline = Date.now() + MANUAL_REFRESH_WAIT_MS;
      connectionState("connecting", "Requesting fresh WMI read…");
    }
    const controller = new AbortController();
    const timeout = window.setTimeout(function () { controller.abort(); }, FETCH_TIMEOUT_MS);
    try {
      const headers = { Accept: "application/json" };
      if (manual) headers["X-Peano-Refresh"] = "1";
      const response = await fetch("/api/status", { cache: "no-store", headers: headers, signal: controller.signal });
      if (!response.ok) throw new Error("status HTTP " + response.status);
      const data = await response.json();
      if (!data || data.schema !== "peano-training-dashboard-v1" || data.v !== 1) throw new Error("unexpected dashboard schema");
      render(data);
      if (state.refreshPending) {
        const stamp = snapshotStamp(data);
        const updated = hasSuccessfulSnapshot(data) && (state.refreshBaseline === null || stamp !== state.refreshBaseline);
        if (updated) {
          state.refreshPending = false;
        } else if (Date.now() >= state.refreshDeadline) {
          state.refreshPending = false;
          const usableCache = hasSuccessfulSnapshot(data);
          connectionState(usableCache ? "stale" : "error", usableCache ? "Current cache · no newer WMI snapshot" : "WMI collector unavailable");
          setText("freshness-label", usableCache ? "Refresh timed out before a newer snapshot arrived" : "No successful WMI snapshot is available");
        } else {
          connectionState("connecting", "Fresh WMI read requested…");
          setText("freshness-label", "Waiting for a newer WMI snapshot…");
        }
      }
    } catch (error) {
      const usableCache = hasSuccessfulSnapshot(state.lastData);
      if (state.refreshPending && Date.now() < state.refreshDeadline) {
        connectionState("connecting", "Fresh WMI read pending…");
      } else {
        state.refreshPending = false;
        connectionState(usableCache ? "stale" : "error", usableCache ? "Cached · refresh failed" : "WMI collector unavailable");
      }
      setText("freshness-label", (state.refreshPending ? "Retrying local status read: " : "Last refresh failed: ") + String(error && error.message ? error.message : error));
    } finally {
      window.clearTimeout(timeout);
      state.fetching = false;
      if (state.queuedManualRefresh) {
        state.queuedManualRefresh = false;
        window.setTimeout(function () { fetchStatus(true); }, 0);
      } else schedulePoll(state.refreshPending ? MANUAL_REFRESH_POLL_MS : null);
    }
  }

  function schedulePoll(delayMilliseconds) {
    if (state.timer !== null) window.clearTimeout(state.timer);
    const regularDelay = document.hidden ? POLL_HIDDEN_MS : POLL_VISIBLE_MS;
    state.timer = window.setTimeout(function () { fetchStatus(false); }, number(delayMilliseconds, regularDelay));
  }

  element("refresh-button").addEventListener("click", function () { fetchStatus(true); });
  element("sample-previous").addEventListener("click", function () {
    if (!state.samples.length) return;
    state.sampleIndex = (state.sampleIndex - 1 + state.samples.length) % state.samples.length;
    renderSample(true);
  });
  element("sample-next").addEventListener("click", function () {
    if (!state.samples.length) return;
    state.sampleIndex = (state.sampleIndex + 1) % state.samples.length;
    renderSample(true);
  });
  element("reveal-target").addEventListener("click", function () {
    state.targetVisible = !state.targetVisible;
    element("target-answer").hidden = !state.targetVisible;
    element("reveal-target").setAttribute("aria-expanded", String(state.targetVisible));
    setText("reveal-target", state.targetVisible ? "Hide supervised next tactic" : "Reveal supervised next tactic");
  });
  document.querySelectorAll("[data-log-stream]").forEach(function (button) {
    button.addEventListener("click", function () {
      state.logStream = button.dataset.logStream;
      document.querySelectorAll("[data-log-stream]").forEach(function (node) {
        const selected = node === button;
        node.classList.toggle("is-selected", selected);
        node.setAttribute("aria-pressed", String(selected));
      });
      if (state.lastData) renderLogs(state.lastData);
    });
  });
  element("pause-log").addEventListener("click", function () {
    state.logScrollPaused = !state.logScrollPaused;
    element("pause-log").setAttribute("aria-pressed", String(state.logScrollPaused));
    setText("pause-log", state.logScrollPaused ? "Resume scroll" : "Pause scroll");
  });
  element("copy-log").addEventListener("click", async function () {
    const button = element("copy-log");
    try {
      await navigator.clipboard.writeText(element("live-log").textContent);
      button.textContent = "Copied";
    } catch (_error) {
      button.textContent = "Copy failed";
    }
    window.setTimeout(function () { button.textContent = "Copy"; }, 1400);
  });
  document.addEventListener("visibilitychange", schedulePoll);

  fetchStatus(false);
}());
