import Lean.Data.Json
import PeanoLab.Soundness

/-!
# Canonical inert artifact codec

Artifacts use exact-arity tagged JSON arrays.  The public decoder parses the
bytes, reconstructs inert Lean syntax, and then requires byte-for-byte equality
with the canonical encoder.  This rejects alternate whitespace, number
spellings, unknown fields, duplicate fields, and trailing data without relying
on object-key semantics.
-/

namespace PeanoLab

open Lean

structure Artifact where
  fuel : Nat
  target : Formula
  proof : Proof
  deriving Repr, DecidableEq

private def encodeArray (items : List String) : String :=
  "[" ++ String.intercalate "," items ++ "]"

private def encodeTag (tag : String) (args : List String := []) : String :=
  encodeArray (("\"" ++ tag ++ "\"") :: args)

def encodeTerm : Term -> String
  | .var i => encodeTag "var" [toString i]
  | .zero => encodeTag "zero"
  | .succ t => encodeTag "succ" [encodeTerm t]
  | .add s t => encodeTag "add" [encodeTerm s, encodeTerm t]
  | .mul s t => encodeTag "mul" [encodeTerm s, encodeTerm t]

def encodeFormula : Formula -> String
  | .eq s t => encodeTag "eq" [encodeTerm s, encodeTerm t]
  | .bot => encodeTag "bot"
  | .imp a b => encodeTag "imp" [encodeFormula a, encodeFormula b]
  | .conj a b => encodeTag "and" [encodeFormula a, encodeFormula b]
  | .disj a b => encodeTag "or" [encodeFormula a, encodeFormula b]
  | .forallE a => encodeTag "forall" [encodeFormula a]
  | .existsE a => encodeTag "exists" [encodeFormula a]

private def encodeAxiomName : AxiomName -> String
  | .pa1 => "\"PA1\""
  | .pa2 => "\"PA2\""
  | .pa3 => "\"PA3\""
  | .pa4 => "\"PA4\""
  | .pa5 => "\"PA5\""
  | .pa6 => "\"PA6\""

def encodeProof : Proof -> String
  | .hyp i => encodeTag "hyp" [toString i]
  | .impIntro p => encodeTag "imp_intro" [encodeProof p]
  | .impElim f a => encodeTag "imp_elim" [encodeProof f, encodeProof a]
  | .cut proposition conclusion lemma body =>
      encodeTag "cut"
        [encodeFormula proposition, encodeFormula conclusion,
          encodeProof lemma, encodeProof body]
  | .andIntro p q => encodeTag "and_intro" [encodeProof p, encodeProof q]
  | .andElimL p => encodeTag "and_elim_l" [encodeProof p]
  | .andElimR p => encodeTag "and_elim_r" [encodeProof p]
  | .orIntroL p => encodeTag "or_intro_l" [encodeProof p]
  | .orIntroR p => encodeTag "or_intro_r" [encodeProof p]
  | .orElim p l r =>
      encodeTag "or_elim" [encodeProof p, encodeProof l, encodeProof r]
  | .botElim p => encodeTag "bot_elim" [encodeProof p]
  | .forallIntro p => encodeTag "forall_intro" [encodeProof p]
  | .forallElim p t => encodeTag "forall_elim" [encodeProof p, encodeTerm t]
  | .existsIntro t p => encodeTag "exists_intro" [encodeTerm t, encodeProof p]
  | .existsElim p body => encodeTag "exists_elim" [encodeProof p, encodeProof body]
  | .eqRefl t => encodeTag "eq_refl" [encodeTerm t]
  | .eqSym p => encodeTag "eq_sym" [encodeProof p]
  | .eqTrans p q => encodeTag "eq_trans" [encodeProof p, encodeProof q]
  | .congS p => encodeTag "cong_s" [encodeProof p]
  | .congAdd p q => encodeTag "cong_add" [encodeProof p, encodeProof q]
  | .congMul p q => encodeTag "cong_mul" [encodeProof p, encodeProof q]
  | .eqSubst motive equation body =>
      encodeTag "eq_subst" [encodeFormula motive, encodeProof equation, encodeProof body]
  | .dne a => encodeTag "dne" [encodeFormula a]
  | .axiom name => encodeTag "axiom" [encodeAxiomName name]
  | .ind motive base step =>
      encodeTag "ind" [encodeFormula motive, encodeProof base, encodeProof step]

/-- Canonical artifacts always end in exactly one LF byte. -/
def encodeArtifact (artifact : Artifact) : String :=
  encodeTag "peano-lab-v2"
    [toString artifact.fuel, encodeFormula artifact.target, encodeProof artifact.proof] ++
    "\n"

private def decodeNat (json : Json) : Except String Nat :=
  fromJson? json

def decodeTerm : Nat -> Json -> Except String Term
  | 0, _ => throw "term nesting exceeds input bound"
  | fuel + 1, .arr items =>
      match items.toList with
      | [.str "var", index] => return .var (← decodeNat index)
      | [.str "zero"] => return .zero
      | [.str "succ", term] => return .succ (← decodeTerm fuel term)
      | [.str "add", left, right] =>
          return .add (← decodeTerm fuel left) (← decodeTerm fuel right)
      | [.str "mul", left, right] =>
          return .mul (← decodeTerm fuel left) (← decodeTerm fuel right)
      | _ => throw "invalid term tag or arity"
  | _, _ => throw "term must be a tagged array"

def decodeFormula : Nat -> Json -> Except String Formula
  | 0, _ => throw "formula nesting exceeds input bound"
  | fuel + 1, .arr items =>
      match items.toList with
      | [.str "eq", left, right] =>
          return .eq (← decodeTerm fuel left) (← decodeTerm fuel right)
      | [.str "bot"] => return .bot
      | [.str "imp", left, right] =>
          return .imp (← decodeFormula fuel left) (← decodeFormula fuel right)
      | [.str "and", left, right] =>
          return .conj (← decodeFormula fuel left) (← decodeFormula fuel right)
      | [.str "or", left, right] =>
          return .disj (← decodeFormula fuel left) (← decodeFormula fuel right)
      | [.str "forall", body] => return .forallE (← decodeFormula fuel body)
      | [.str "exists", body] => return .existsE (← decodeFormula fuel body)
      | _ => throw "invalid formula tag or arity"
  | _, _ => throw "formula must be a tagged array"

private def decodeAxiomName : Json -> Except String AxiomName
  | .str "PA1" => return .pa1
  | .str "PA2" => return .pa2
  | .str "PA3" => return .pa3
  | .str "PA4" => return .pa4
  | .str "PA5" => return .pa5
  | .str "PA6" => return .pa6
  | _ => throw "axiom name must be exactly PA1 through PA6"

def decodeProof : Nat -> Json -> Except String Proof
  | 0, _ => throw "proof nesting exceeds input bound"
  | fuel + 1, .arr items =>
      match items.toList with
      | [.str "hyp", index] => return .hyp (← decodeNat index)
      | [.str "imp_intro", body] => return .impIntro (← decodeProof fuel body)
      | [.str "imp_elim", function, argument] =>
          return .impElim (← decodeProof fuel function) (← decodeProof fuel argument)
      | [.str "cut", proposition, conclusion, lemma, body] =>
          return .cut (← decodeFormula fuel proposition)
            (← decodeFormula fuel conclusion)
            (← decodeProof fuel lemma) (← decodeProof fuel body)
      | [.str "and_intro", left, right] =>
          return .andIntro (← decodeProof fuel left) (← decodeProof fuel right)
      | [.str "and_elim_l", pair] => return .andElimL (← decodeProof fuel pair)
      | [.str "and_elim_r", pair] => return .andElimR (← decodeProof fuel pair)
      | [.str "or_intro_l", proof] => return .orIntroL (← decodeProof fuel proof)
      | [.str "or_intro_r", proof] => return .orIntroR (← decodeProof fuel proof)
      | [.str "or_elim", disjunction, leftCase, rightCase] =>
          return .orElim (← decodeProof fuel disjunction)
            (← decodeProof fuel leftCase) (← decodeProof fuel rightCase)
      | [.str "bot_elim", absurdity] => return .botElim (← decodeProof fuel absurdity)
      | [.str "forall_intro", body] => return .forallIntro (← decodeProof fuel body)
      | [.str "forall_elim", universal, term] =>
          return .forallElim (← decodeProof fuel universal) (← decodeTerm fuel term)
      | [.str "exists_intro", term, proof] =>
          return .existsIntro (← decodeTerm fuel term) (← decodeProof fuel proof)
      | [.str "exists_elim", existential, body] =>
          return .existsElim (← decodeProof fuel existential) (← decodeProof fuel body)
      | [.str "eq_refl", term] => return .eqRefl (← decodeTerm fuel term)
      | [.str "eq_sym", proof] => return .eqSym (← decodeProof fuel proof)
      | [.str "eq_trans", first, second] =>
          return .eqTrans (← decodeProof fuel first) (← decodeProof fuel second)
      | [.str "cong_s", proof] => return .congS (← decodeProof fuel proof)
      | [.str "cong_add", left, right] =>
          return .congAdd (← decodeProof fuel left) (← decodeProof fuel right)
      | [.str "cong_mul", left, right] =>
          return .congMul (← decodeProof fuel left) (← decodeProof fuel right)
      | [.str "eq_subst", motive, equation, body] =>
          return .eqSubst (← decodeFormula fuel motive)
            (← decodeProof fuel equation) (← decodeProof fuel body)
      | [.str "dne", proposition] => return .dne (← decodeFormula fuel proposition)
      | [.str "axiom", name] => return .axiom (← decodeAxiomName name)
      | [.str "ind", motive, base, step] =>
          return .ind (← decodeFormula fuel motive)
            (← decodeProof fuel base) (← decodeProof fuel step)
      | _ => throw "invalid proof tag or arity"
  | _, _ => throw "proof must be a tagged array"

def decodeArtifactJson (bound : Nat) : Json -> Except String Artifact
  | .arr items =>
      match items.toList with
      | [.str "peano-lab-v2", fuel, target, proof] =>
          return {
            fuel := ← decodeNat fuel
            target := ← decodeFormula bound target
            proof := ← decodeProof bound proof
          }
      | _ => throw "artifact must use the peano-lab-v2 tag and exact arity"
  | _ => throw "artifact must be a tagged array"

/-- Parse and require the one canonical byte representation of the artifact. -/
def decodeArtifactCanonical (input : String) : Except String Artifact := do
  let json ← Json.parse input
  let artifact ← decodeArtifactJson (input.length + 1) json
  if encodeArtifact artifact = input then
    return artifact
  else
    throw "artifact bytes are valid JSON but not canonical peano-lab-v2 encoding"

/-- The production artifact gate uses the fuel carried in canonical bytes. -/
def Artifact.check (artifact : Artifact) : Bool :=
  artifact.target.wellScoped 0 &&
    checkIntuitionisticWithFuel artifact.fuel [] artifact.proof artifact.target

theorem Artifact.check_derives {artifact : Artifact}
    (h : artifact.check = true) :
    Derives false [] artifact.proof artifact.target := by
  have hparts :
      artifact.target.wellScoped 0 = true ∧
        checkIntuitionisticWithFuel artifact.fuel [] artifact.proof artifact.target = true := by
    simpa [Artifact.check] using h
  apply PeanoLab.check_derives
  simpa [checkIntuitionisticWithFuel] using hparts.2

theorem Artifact.check_sound {artifact : Artifact}
    (h : artifact.check = true) :
    ∀ valuation, artifact.target.Holds valuation := by
  exact closed_derivation_sound (Artifact.check_derives h)

end PeanoLab
