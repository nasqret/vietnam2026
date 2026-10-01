import PeanoLab.Codec

/-!
# Independently sound, self-contained topological proof bundles

Each local node stores an ordinary Peano certificate for its dependency-curried
formula.  The existing proof-producing intuitionistic checker validates that
certificate exactly once.  Previously verified local conclusions are
discharged by the already sound implication-elimination rule; the composition
witness lives in `Prop` and is therefore erased from the executable checker.

No theorem name, digest, Python object identity, external registry, or prior
process receipt has logical authority.
-/

namespace PeanoLab

open Lean

/-- One topologically prior-dependency proof and its explicit checker fuel. -/
structure BundleNode where
  fuel : Nat
  target : Formula
  dependencies : List Nat
  body : Proof
  deriving Repr, DecidableEq

/-- Dense local indices are the list positions; `root` is not a global name. -/
structure ProofBundle where
  nodes : List BundleNode
  root : Nat
  deriving Repr, DecidableEq

/-- A previously established closed conclusion with its erased proof witness. -/
structure EstablishedBundleNode where
  target : Formula
  derivation : ∃ proof, Derives false [] proof target

/-- Preserve the author's exact ordered list of implication assumptions. -/
def curryBundleTargets : List EstablishedBundleNode → Formula → Formula
  | [], target => target
  | entry :: rest, target => .imp entry.target (curryBundleTargets rest target)

/-- Constructive repeated modus ponens; no new inference rule or axiom. -/
theorem dischargeBundleDependencies
    (dependencies : List EstablishedBundleNode) (target : Formula)
    (body : Proof)
    (hbody : Derives false [] body (curryBundleTargets dependencies target)) :
    ∃ proof, Derives false [] proof target := by
  induction dependencies generalizing body with
  | nil => exact ⟨body, hbody⟩
  | cons dependency rest ih =>
      rcases dependency.derivation with ⟨argument, hargument⟩
      exact ih (.impElim body argument) (.impElim hbody hargument)

/-- Resolve only dense local IDs already established in this same invocation. -/
def gatherBundleDependencies
    (established : Array EstablishedBundleNode) :
    List Nat → Option (List EstablishedBundleNode)
  | [] => some []
  | index :: remaining => do
      let dependency ← established[index]?
      let rest ← gatherBundleDependencies established remaining
      return dependency :: rest

/-- A node is accepted only after its own unchanged empty-context proof check. -/
def checkBundleNode
    (established : Array EstablishedBundleNode) (node : BundleNode) :
    Option (Array EstablishedBundleNode) := do
  if !node.target.wellScoped 0 || node.fuel == 0 then
    none
  else if node.dependencies.eraseDups.length != node.dependencies.length then
    none
  else
    let dependencies ← gatherBundleDependencies established node.dependencies
    let checked ←
      checkVerified node.fuel false [] node.body
        (curryBundleTargets dependencies node.target)
    let derivation :=
      dischargeBundleDependencies dependencies node.target node.body
        checked.derivation
    return established.push ⟨node.target, derivation⟩

/-- Process the node list exactly once in canonical topological order. -/
def checkBundleNodes :
    List BundleNode → Array EstablishedBundleNode →
      Option (Array EstablishedBundleNode)
  | [], established => some established
  | node :: remaining, established => do
      let next ← checkBundleNode established node
      checkBundleNodes remaining next

/-- Bounded root reachability rejects irrelevant appended certificate data. -/
def collectBundleReachable
    (nodes : Array BundleNode) :
    Nat → List Nat → List Nat → Option (List Nat)
  | _, [], seen => some seen
  | 0, _ :: _, _ => none
  | fuel + 1, index :: pending, seen =>
      if index ∈ seen then
        collectBundleReachable nodes fuel pending seen
      else
        match nodes[index]? with
        | none => none
        | some node =>
            collectBundleReachable nodes fuel
              (node.dependencies ++ pending) (index :: seen)

def bundleReachabilityFuel (nodes : List BundleNode) : Nat :=
  nodes.length + (nodes.map (fun node => node.dependencies.length)).sum + 1

/-- Successful bundle checking retains an erased actual derivation witness. -/
structure VerifiedBundle (target : Formula) where
  root : Nat
  derivation : ∃ proof, Derives false [] proof target

/-- Exact target matching, strict local scope, and duplicate-free topology. -/
def checkBundleVerified
    (bundle : ProofBundle) (target : Formula) :
    Option (VerifiedBundle target) := do
  if bundle.nodes.isEmpty || bundle.root + 1 != bundle.nodes.length then
    none
  else
    let established ← checkBundleNodes bundle.nodes #[]
    let entry ← established[bundle.root]?
    let reachable ←
      collectBundleReachable bundle.nodes.toArray
        (bundleReachabilityFuel bundle.nodes) [bundle.root] []
    if reachable.length != bundle.nodes.length then
      none
    else if htarget : entry.target = target then
      some ⟨bundle.root, htarget ▸ entry.derivation⟩
    else
      none

/-- Executable Boolean acceptance; every local body was checked exactly once. -/
def checkBundle (bundle : ProofBundle) (target : Formula) : Bool :=
  (checkBundleVerified bundle target).isSome

/-- A successful shared bundle still denotes an ordinary constructive derivation. -/
theorem checkBundle_derives {bundle : ProofBundle} {target : Formula}
    (h : checkBundle bundle target = true) :
    ∃ proof, Derives false [] proof target := by
  unfold checkBundle at h
  cases hverified : checkBundleVerified bundle target with
  | none => simp [hverified] at h
  | some verified => exact verified.derivation

/-- The unchanged semantic theorem proves the caller's exact target true. -/
theorem checkBundle_sound {bundle : ProofBundle} {target : Formula}
    (h : checkBundle bundle target = true) :
    ∀ valuation, target.Holds valuation := by
  rcases checkBundle_derives h with ⟨proof, hproof⟩
  intro valuation
  exact hproof.sound valuation trivial

/-- Canonical inert payload plus an independently supplied exact target. -/
structure BundleArtifact where
  bundle : ProofBundle
  target : Formula
  deriving Repr, DecidableEq

private def bundleEncodeArray (items : List String) : String :=
  "[" ++ String.intercalate "," items ++ "]"

def encodeBundleNode (node : BundleNode) : String :=
  bundleEncodeArray
    [toString node.fuel,
      encodeFormula node.target,
      bundleEncodeArray (node.dependencies.map toString),
      encodeProof node.body]

/-- Exact canonical JSON arrays; proof constructors retain v2 spellings. -/
def encodeBundleArtifact (artifact : BundleArtifact) : String :=
  bundleEncodeArray
    ["\"peano-lab-bundle-v1\"",
      toString artifact.bundle.root,
      encodeFormula artifact.target,
      bundleEncodeArray (artifact.bundle.nodes.map encodeBundleNode)] ++ "\n"

private def decodeBundleNat (json : Json) : Except String Nat :=
  fromJson? json

def decodeBundleNode (bound : Nat) : Json → Except String BundleNode
  | .arr fields =>
      match fields.toList with
      | [fuel, target, .arr dependencies, body] => do
          let decodedDependencies ←
            dependencies.toList.mapM decodeBundleNat
          return {
            fuel := ← decodeBundleNat fuel
            target := ← decodeFormula bound target
            dependencies := decodedDependencies
            body := ← decodeProof bound body
          }
      | _ => throw "bundle node must have exactly four fields"
  | _ => throw "bundle node must be an exact JSON array"

def decodeBundleArtifactJson (bound : Nat) :
    Json → Except String BundleArtifact
  | .arr fields =>
      match fields.toList with
      | [.str "peano-lab-bundle-v1", root, target, .arr nodes] => do
          let decodedNodes ← nodes.toList.mapM (decodeBundleNode bound)
          return {
            bundle := {
              nodes := decodedNodes
              root := ← decodeBundleNat root
            }
            target := ← decodeFormula bound target
          }
      | _ => throw "bundle artifact must have exact tag and arity"
  | _ => throw "bundle artifact must be an exact tagged array"

/-- Reject alternate whitespace, duplicate/extra fields, and trailing data. -/
def decodeBundleArtifactCanonical (input : String) :
    Except String BundleArtifact := do
  let json ← Json.parse input
  let artifact ← decodeBundleArtifactJson (input.length + 1) json
  if encodeBundleArtifact artifact = input then
    return artifact
  else
    throw "bundle artifact bytes are not canonical"

def BundleArtifact.check (artifact : BundleArtifact) : Bool :=
  checkBundle artifact.bundle artifact.target

theorem BundleArtifact.check_sound {artifact : BundleArtifact}
    (h : artifact.check = true) :
    ∀ valuation, artifact.target.Holds valuation :=
  checkBundle_sound h

/-- A shared local proof is applied twice while its body is checked once. -/
def sharedReflexivityBundle : BundleArtifact :=
  let proposition := Formula.eq .zero .zero
  {
    target := .conj proposition proposition
    bundle := {
      root := 1
      nodes := [
        {
          fuel := 24
          target := proposition
          dependencies := []
          body := .eqRefl .zero
        },
        {
          fuel := 48
          target := .conj proposition proposition
          dependencies := [0]
          body := .impIntro (.andIntro (.hyp 0) (.hyp 0))
        }
      ]
    }
  }

example : sharedReflexivityBundle.check = true := by native_decide

def sharedBundleCodecRoundTrip : Bool :=
  match decodeBundleArtifactCanonical
      (encodeBundleArtifact sharedReflexivityBundle) with
  | .ok artifact => artifact == sharedReflexivityBundle
  | .error _ => false

example : sharedBundleCodecRoundTrip = true := by native_decide

end PeanoLab
