//! A fixed, offline, untrusted semiring adviser. This program never checks a
//! native certificate, opens an input file, starts a child, or accepts a rule.
use egg::{Applier, CostFunction, EGraph, Extractor, FlatTerm, Id, Language, Pattern,
          PatternAst, RecExpr, Rewrite, Subst, Symbol, SymbolLang, TreeTerm, Var};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::{HashMap, HashSet}, io::{self, Read, Write}, rc::Rc,
          sync::{Arc, atomic::{AtomicBool, Ordering}}, time::{Duration, Instant}};

const MAX_INPUT: usize = 65_536;
const MAX_OUTPUT: usize = 262_144;
const MAX_NODES: usize = 4096;
const MAX_ITERATIONS: usize = 8;
const MAX_MATCHES: usize = 64;
const MAX_TERM: usize = 256;
const RULE_SET: &str = "peano-semiring-1";
const RULES: &[(&str, &str, &str)] = &[
    ("add-zero", "(+ ?a z)", "?a"),
    ("zero-add", "(+ z ?a)", "?a"),
    ("mul-zero", "(* ?a z)", "z"),
    ("zero-mul", "(* z ?a)", "z"),
    ("mul-one", "(* ?a (s z))", "?a"),
    ("one-mul", "(* (s z) ?a)", "?a"),
    ("add-comm", "(+ ?a ?b)", "(+ ?b ?a)"),
    ("mul-comm", "(* ?a ?b)", "(* ?b ?a)"),
    ("add-assoc", "(+ (+ ?a ?b) ?c)", "(+ ?a (+ ?b ?c))"),
    ("mul-assoc", "(* (* ?a ?b) ?c)", "(* ?a (* ?b ?c))"),
    ("distrib-left", "(* ?a (+ ?b ?c))", "(+ (* ?a ?b) (* ?a ?c))"),
    ("distrib-right", "(* (+ ?a ?b) ?c)", "(+ (* ?a ?c) (* ?b ?c))"),
    ("factor-left", "(+ (* ?a ?b) (* ?a ?c))", "(* ?a (+ ?b ?c))"),
    ("factor-right", "(+ (* ?a ?c) (* ?b ?c))", "(* (+ ?a ?b) ?c)"),
    ("succ-add-one", "(s ?a)", "(+ ?a (s z))"),
    ("add-succ", "(+ ?a (s ?b))", "(s (+ ?a ?b))"),
    ("mul-succ", "(* ?a (s ?b))", "(+ (* ?a ?b) ?a)"),
];

type Graph = EGraph<SymbolLang, ()>;

fn require(ok: bool, detail: &str) -> Result<(), String> {
    if ok { Ok(()) } else { Err(detail.into()) }
}

fn bounded_json(value: &Value) -> Result<(), String> {
    let mut stack = vec![(value, 0usize)];
    let mut work = 0usize;
    while let Some((value, depth)) = stack.pop() {
        work += 1;
        require(work <= 32768 && depth <= 128, "JSON structure bound")?;
        match value {
            Value::Null | Value::Bool(_) => (),
            Value::Number(number) => require(number.as_i64().is_some(), "Only signed integer JSON")?,
            Value::String(text) => require(text.len() <= MAX_INPUT, "JSON string bound")?,
            Value::Array(items) => stack.extend(items.iter().map(|item| (item, depth + 1))),
            Value::Object(items) => {
                require(items.len() <= 1024, "JSON map bound")?;
                stack.extend(items.values().map(|item| (item, depth + 1)));
            }
        }
    }
    Ok(())
}

// Python's common protocol uses sorted, compact, ensure_ascii JSON. serde_json
// maps are sorted in this build; encode non-ASCII codepoints identically.
fn canonical_ascii(value: &Value) -> Result<Vec<u8>, String> {
    let source = serde_json::to_string(value).map_err(|error| error.to_string())?;
    let mut result = String::with_capacity(source.len());
    for ch in source.chars() {
        if ch < '\u{7f}' { result.push(ch); }
        else {
            let mut buffer = [0u16; 2];
            for part in ch.encode_utf16(&mut buffer) { result.push_str(&format!("\\u{:04x}", part)); }
        }
    }
    require(result.len() <= MAX_OUTPUT, "Canonical JSON byte bound")?;
    Ok(result.into_bytes())
}

fn expression(text: &str, variables: usize) -> Result<RecExpr<SymbolLang>, String> {
    require(!text.is_empty() && text.len() <= 8192, "Term text bound")?;
    let mut nesting = 0i32;
    for ch in text.chars() {
        if ch == '(' { nesting += 1; }
        if ch == ')' { nesting -= 1; }
        require((0..=32).contains(&nesting), "Term nesting bound")?;
    }
    require(nesting == 0, "Unbalanced term")?;
    let expr: RecExpr<SymbolLang> = text.parse().map_err(|_| "Invalid bounded term".to_string())?;
    validate_expression(&expr, variables)?;
    Ok(expr)
}

fn validate_expression(expr: &RecExpr<SymbolLang>, variables: usize) -> Result<(), String> {
    require(!expr.as_ref().is_empty() && expr.as_ref().len() <= MAX_TERM, "Term node bound")?;
    let mut depths = Vec::new();
    let mut occurrences = Vec::new();
    for node in expr.as_ref() {
        let operator = node.op.as_str();
        let arity = match operator { "z" => 0, "s" => 1, "+" | "*" => 2,
            "v0" | "v1" | "v2" | "v3" => {
                require(usize::from(operator.as_bytes()[1] - b'0') < variables, "Unscoped term variable")?;
                0
            }, _ => return Err("Unsupported term symbol".into()) };
        require(node.children.len() == arity, "Unsupported term arity")?;
        let depth = 1 + node.children.iter().map(|child| depths[usize::from(*child)]).max().unwrap_or(0usize);
        let count = 1 + node.children.iter().map(|child| occurrences[usize::from(*child)]).sum::<usize>();
        require(depth <= 33, "Term AST depth bound")?;
        require(count <= MAX_TERM, "Term structural occurrence bound")?;
        depths.push(depth);
        occurrences.push(count);
    }
    Ok(())
}

struct BoundedApplier {
    rhs: Pattern<SymbolLang>,
    allowance: usize,
    node_limit: Arc<AtomicBool>,
}

impl Applier<SymbolLang, ()> for BoundedApplier {
    fn apply_one(&self, graph: &mut Graph, class: Id, subst: &Subst,
                 source: Option<&PatternAst<SymbolLang>>, name: Symbol) -> Vec<Id> {
        // Pattern::apply_one adds the RHS, then explanation-enabled union may
        // instantiate both sides. Count all three conservatively *before* add.
        if graph.total_size().saturating_add(self.allowance) > MAX_NODES {
            self.node_limit.store(true, Ordering::Relaxed);
            return Vec::new();
        }
        let result = self.rhs.apply_one(graph, class, subst, source, name);
        assert!(graph.total_size() <= MAX_NODES);
        result
    }
    fn get_pattern_ast(&self) -> Option<&PatternAst<SymbolLang>> { Some(&self.rhs.ast) }
    fn vars(&self) -> Vec<Var> { self.rhs.vars() }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
struct NativeCost { work: u64, nodes: usize, monomials: usize }
struct NativeEstimate;
impl CostFunction<SymbolLang> for NativeEstimate {
    type Cost = NativeCost;
    fn cost<C>(&mut self, node: &SymbolLang, mut costs: C) -> NativeCost where C: FnMut(Id) -> NativeCost {
        let children: Vec<NativeCost> = node.children.iter().map(|child| costs(*child)).collect();
        let nodes = 1usize.saturating_add(children.iter().map(|child| child.nodes).sum::<usize>()).min(1000000);
        let sum = children.iter().map(|child| child.work).sum::<u64>();
        let (work, monomials) = match node.op.as_str() {
            "z" => (1, 0),
            "s" => { let m = (children[0].monomials + 1).min(256); (sum + 2 * m as u64 + 4, m) },
            "+" => { let m = children.iter().map(|child| child.monomials).sum::<usize>().min(256); (sum + m as u64 + 4, m) },
            "*" => { let m = (children[0].monomials * children[1].monomials).min(256); (sum + 8 * m as u64 + 4, m) },
            _ => (1, 1),
        };
        NativeCost { work: work.min(1000000000), nodes, monomials }
    }
}

fn tree_stats(term: &Rc<TreeTerm<SymbolLang>>, memo: &mut HashMap<usize, (usize, usize)>,
              active: &mut HashSet<usize>, depth: usize) -> Result<(usize, usize), String> {
    let key = Rc::as_ptr(term) as usize;
    if let Some(stats) = memo.get(&key) { return Ok(*stats); }
    require(depth <= 64 && memo.len() + active.len() < 4096 && active.insert(key), "Explanation DAG bound")?;
    let mut nodes = 1usize;
    let mut steps = usize::from(term.forward_rule.is_some() || term.backward_rule.is_some());
    for proof in &term.child_proofs {
        let stats = sequence_stats(proof, memo, active, depth + 1)?;
        nodes = nodes.saturating_add(stats.0);
        steps = steps.saturating_add(stats.1);
        require(nodes <= MAX_TERM && steps <= 32, "Explanation flattening bound")?;
    }
    active.remove(&key);
    memo.insert(key, (nodes, steps));
    Ok((nodes, steps))
}

fn sequence_stats(sequence: &[Rc<TreeTerm<SymbolLang>>], memo: &mut HashMap<usize, (usize, usize)>,
                  active: &mut HashSet<usize>, depth: usize) -> Result<(usize, usize), String> {
    require(sequence.len() <= 33, "Explanation sequence bound")?;
    let mut nodes = 0usize;
    let mut steps = sequence.len().saturating_sub(1);
    for term in sequence {
        let stats = tree_stats(term, memo, active, depth)?;
        nodes = nodes.max(stats.0);
        steps = steps.saturating_add(stats.1);
        require(nodes <= MAX_TERM && steps <= 32, "Explanation expansion bound")?;
    }
    Ok((nodes, steps))
}

fn flat_data(term: &FlatTerm<SymbolLang>, path: &mut Vec<usize>, changes: &mut Vec<(String, String, Vec<usize>)>,
             nodes: &mut usize) -> Result<String, String> {
    *nodes += 1;
    require(*nodes <= MAX_TERM && path.len() <= 32, "Flat explanation term bound")?;
    require(!(term.forward_rule.is_some() && term.backward_rule.is_some()), "Ambiguous rewrite annotation")?;
    if let Some(rule) = term.forward_rule.or(term.backward_rule) {
        let name = rule.to_string();
        require(RULES.iter().any(|rule| rule.0 == name), "Unrecognized rewrite reason")?;
        changes.push((name, if term.forward_rule.is_some() { "forward" } else { "backward" }.into(), path.clone()));
        require(changes.len() <= 1, "A flat row must contain exactly one rewrite")?;
    }
    let mut children = Vec::new();
    for (index, child) in term.children.iter().enumerate() {
        path.push(index);
        children.push(flat_data(child, path, changes, nodes)?);
        path.pop();
    }
    let name = term.node.op.to_string();
    Ok(if children.is_empty() { name } else { format!("({} {})", name, children.join(" ")) })
}

fn explanation(graph: &mut Graph, from: &RecExpr<SymbolLang>, to: &RecExpr<SymbolLang>,
               variables: usize) -> Result<Vec<Value>, String> {
    let mut proof = graph.explain_equivalence(from, to);
    sequence_stats(&proof.explanation_trees, &mut HashMap::new(), &mut HashSet::new(), 0)?;
    let flat = proof.make_flat_explanation();
    require(!flat.is_empty() && flat.len() <= 17, "Sixteen-rewrite output bound")?;
    let mut previous = from.to_string();
    let mut steps = Vec::new();
    for (index, term) in flat.iter().enumerate() {
        let mut changes = Vec::new();
        let current = flat_data(term, &mut Vec::new(), &mut changes, &mut 0)?;
        expression(&current, variables)?;
        if index == 0 { require(changes.is_empty() && current == previous, "Explanation start mismatch")?; }
        else {
            require(changes.len() == 1 && current != previous, "Incomplete flat rewrite")?;
            let (rule, direction, path) = &changes[0];
            steps.push(json!({"before": previous, "after": current, "rule": rule, "direction": direction, "path": path}));
        }
        previous = current;
    }
    require(previous == to.to_string(), "Explanation end mismatch")?;
    Ok(steps)
}

fn score(steps: &[Value], variables: usize) -> Result<u64, String> {
    // Rank proof plans by expansion work and congruence/command growth, rather
    // than the character count of an extracted expression alone.
    let mut cost = 0u64;
    for step in steps {
        let expr = expression(step["after"].as_str().ok_or("Missing rewrite endpoint")?, variables)?;
        let mut values = Vec::new();
        for node in expr.as_ref() { values.push(NativeEstimate.cost(node, |id| values[usize::from(id)])); }
        let length = step["path"].as_array().ok_or("Missing congruence path")?.len() as u64;
        cost = cost.saturating_add(values.last().unwrap().work + 2 * length + 2);
    }
    Ok(cost)
}

fn solve(payload: &Value) -> Result<Value, String> {
    require(payload.as_object().map(|map| map.len()) == Some(7)
        && payload["fragment"] == "hydra-egg-semiring-v1" && payload["rule_set"] == RULE_SET
        && payload["max_nodes"] == MAX_NODES && payload["max_iterations"] == MAX_ITERATIONS, "Fixed egg payload required")?;
    let variables = payload["variables"].as_u64().ok_or("Missing variable count")? as usize;
    require(variables <= 4, "Four-variable limit")?;
    let left = expression(payload["lhs"].as_str().ok_or("Missing lhs")?, variables)?;
    let right = expression(payload["rhs"].as_str().ok_or("Missing rhs")?, variables)?;
    let started = Instant::now();
    let deadline = Duration::from_millis(700);
    let limit_hit = Arc::new(AtomicBool::new(false));
    let mut rules = Vec::new();
    for (name, lhs, rhs) in RULES {
        let lhs: Pattern<SymbolLang> = lhs.parse().map_err(|_| "Fixed rule parse")?;
        let rhs: Pattern<SymbolLang> = rhs.parse().map_err(|_| "Fixed rule parse")?;
        let allowance = lhs.ast.len() + 2 * rhs.ast.len();
        rules.push(Rewrite::new(*name, lhs, BoundedApplier { rhs, allowance, node_limit: limit_hit.clone() })
                   .map_err(|_| "Fixed rule variables")?);
    }
    let mut graph = Graph::default().with_explanations_enabled();
    let left_id = graph.add_expr(&left);
    let right_id = graph.add_expr(&right);
    graph.rebuild();
    let mut iterations = 0usize;
    let mut stopped = "iteration_limit";
    'outer: for iteration in 0..MAX_ITERATIONS {
        iterations = iteration + 1;
        let mut changed = false;
        for rule in &rules {
            if started.elapsed() >= deadline { stopped = "internal_wall_limit"; break 'outer; }
            let matches = rule.search_with_limit(&graph, MAX_MATCHES);
            changed |= !rule.apply(&mut graph, &matches).is_empty();
            graph.rebuild();
            require(graph.total_size() <= MAX_NODES && graph.total_number_of_nodes() <= MAX_NODES, "Graph node invariant")?;
            if limit_hit.load(Ordering::Relaxed) { stopped = "node_limit"; break 'outer; }
            if graph.find(left_id) == graph.find(right_id) { stopped = "equivalent"; break 'outer; }
        }
        if !changed { stopped = "saturated"; break; }
    }
    if !matches!(stopped, "equivalent" | "saturated") {
        return Ok(json!({"status": "resource_limit", "reason": stopped}));
    }
    let (_, best) = Extractor::new(&graph, NativeEstimate).find_best(left_id);
    validate_expression(&best, variables)?;
    let best_string = best.to_string();
    let same_class = graph.find(left_id) == graph.find(right_id);
    let mut choices: Vec<(u64, Vec<Value>, String)> = Vec::new();
    if same_class {
        if let Ok(steps) = explanation(&mut graph, &left, &right, variables) {
            if !steps.is_empty() { choices.push((score(&steps, variables)?, steps, right.to_string())); }
        }
    }
    if best != left && started.elapsed() < deadline {
        if let Ok(mut steps) = explanation(&mut graph, &left, &best, variables) {
            let mut endpoint = best_string.clone();
            if same_class && best != right {
                if let Ok(tail) = explanation(&mut graph, &best, &right, variables) { steps.extend(tail); endpoint = right.to_string(); }
                else { steps.clear(); }
            }
            if !steps.is_empty() && steps.len() <= 16 { choices.push((score(&steps, variables)?, steps, endpoint)); }
        }
    }
    choices.sort_by_key(|choice| choice.0);
    let Some((cost, steps, end)) = choices.into_iter().next() else {
        return Ok(json!({"status": "no_candidate", "reason": "No bounded translatable explanation"}));
    };
    Ok(json!({"status": "candidate", "evidence": {"schema": "hydra-egg-explanation-v1", "rule_set": RULE_SET,
        "steps": steps, "end": end, "graph_nodes": graph.total_size(), "iterations": iterations,
        "estimated_native_work": cost, "cost_kind": "AST expansion and native command-growth estimate",
        "stop_reason": stopped}}))
}

fn main_result() -> Result<(), String> {
    require(std::env::args_os().len() == 1, "No command-line overrides are accepted")?;
    let mut raw = Vec::new();
    io::stdin().take((MAX_INPUT + 1) as u64).read_to_end(&mut raw).map_err(|error| error.to_string())?;
    require(!raw.is_empty() && raw.len() <= MAX_INPUT, "64-KiB input limit")?;
    let request: Value = serde_json::from_slice(&raw).map_err(|error| error.to_string())?;
    bounded_json(&request)?;
    require(canonical_ascii(&request)? == raw, "Canonical common JSON required; no duplicate fields")?;
    require(request.as_object().map(|map| map.len()) == Some(6)
        && request["schema"] == "hydra-adviser-request-v1" && request["backend"] == "egg"
        && request["policy"] == "hydra-shared-advisers-deep-v1"
        && request["semantic_context"]["schema"] == "hydra-adviser-semantic-context-v1"
        && request["identity"]["backend"] == "egg" && request["identity"]["version"] == "0.11.0", "Bound common request required")?;
    let context = canonical_ascii(&request["semantic_context"])?;
    let proposal = solve(&request["payload"])?;
    let mut response = json!({"schema": "hydra-adviser-response-v1", "backend": "egg", "identity": request["identity"],
        "input_sha256": format!("{:x}", Sha256::digest(&raw)), "context_sha256": format!("{:x}", Sha256::digest(&context)),
        "kernel_checked": false});
    response.as_object_mut().unwrap().extend(proposal.as_object().ok_or("Invalid proposal")?.clone());
    let encoded = canonical_ascii(&response)?;
    require(encoded.len() <= MAX_OUTPUT, "256-KiB output limit")?;
    io::stdout().write_all(&encoded).map_err(|error| error.to_string())?;
    io::stdout().flush().map_err(|error| error.to_string())
}

fn main() {
    if let Err(error) = main_result() {
        let detail: String = error.chars().take(300).collect();
        eprintln!("hydra-egg: {}", detail);
        std::process::exit(70);
    }
}
