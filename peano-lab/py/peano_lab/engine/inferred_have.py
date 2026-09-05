"""Deterministic, untrusted elaboration of ``have h := lemma arguments``.

Only named hypotheses and explicit natural-number terms are accepted. No
unification, theorem search, new axiom, or kernel rule is involved. The caller
must still submit the complete certificate to the ordinary independent checker.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from ..kernel.formulas import Forall, Formula, Imp
from ..kernel.proofs import ForallElim, Hyp, ImpElim, Proof
from ..kernel.terms import parse_term_in_context
from .state import Goal, instantiate_formula, metas_in_formula, metas_in_term


MAX_APPLICATION_BYTES = 65_536
MAX_APPLICATION_ARGUMENTS = 128
MAX_APPLICATION_DEPTH = 128
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")
_RESERVED = {"S", "forall", "exists", "bot", "false"}


class InferredHaveError(ValueError):
    """The application is not uniquely determined by explicit checked inputs."""


@dataclass(frozen=True, slots=True)
class ApplicationSyntax:
    name: str
    reference: str
    arguments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InferredHave:
    syntax: ApplicationSyntax
    proposition: Formula
    proof: Proof
    argument_kinds: tuple[str, ...]


def parse_inferred_have(args: str) -> ApplicationSyntax:
    if type(args) is not str or len(args.encode("utf-8")) > MAX_APPLICATION_BYTES:
        raise InferredHaveError("inferred application exceeds its source bound")
    name, separator, source = args.partition(":=")
    name = name.strip()
    if not separator or not _NAME.fullmatch(name) or name in _RESERVED:
        raise InferredHaveError("syntax: have <fresh-name> := <hypothesis> [arguments]")
    tokens: list[str] = []
    start = None
    depth = 0
    for index, character in enumerate(source):
        if character.isspace() and not depth:
            if start is not None:
                tokens.append(source[start:index])
                start = None
            continue
        if start is None:
            start = index
        if character == "(":
            depth += 1
            if depth > MAX_APPLICATION_DEPTH:
                raise InferredHaveError("application term nesting exceeds its bound")
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise InferredHaveError("unbalanced application parentheses")
        if len(tokens) > MAX_APPLICATION_ARGUMENTS:
            raise InferredHaveError("too many application arguments")
    if depth:
        raise InferredHaveError("unbalanced application parentheses")
    if start is not None:
        tokens.append(source[start:])
    if not tokens or not _NAME.fullmatch(tokens[0]):
        raise InferredHaveError("application requires a named hypothesis")
    if len(tokens) - 1 > MAX_APPLICATION_ARGUMENTS:
        raise InferredHaveError("too many application arguments")
    return ApplicationSyntax(name, tokens[0], tuple(tokens[1:]))


def resolve_inferred_have(goal: Goal, args: str) -> InferredHave:
    syntax = parse_inferred_have(args)
    context = {name: (index, formula) for index, (name, formula) in enumerate(goal.context)}
    if len(context) != len(goal.context):
        raise InferredHaveError("ambiguous hypothesis names")
    if syntax.name in context or syntax.name in goal.variables:
        raise InferredHaveError("the local name is already in use")
    if syntax.reference not in context:
        raise InferredHaveError("application reference is not in the current proof context")
    index, proposition = context[syntax.reference]
    if metas_in_formula(proposition):
        raise InferredHaveError("application needs a fully determined hypothesis")
    proof: Proof = Hyp(index)
    kinds: list[str] = []
    for argument in syntax.arguments:
        if type(proposition) is Forall:
            try:
                term = parse_term_in_context(argument, list(goal.variables))
            except (ValueError, RecursionError) as error:
                raise InferredHaveError("invalid explicit natural-number argument") from error
            if metas_in_term(term):
                raise InferredHaveError("application arguments must not contain metavariables")
            proof = ForallElim(proof, term)
            proposition = instantiate_formula(proposition.body, term)
            kinds.append("term")
        elif type(proposition) is Imp:
            if not _NAME.fullmatch(argument) or argument not in context:
                raise InferredHaveError("an implication premise requires a named proof hypothesis")
            premise_index, premise = context[argument]
            if metas_in_formula(premise) or premise != proposition.left:
                raise InferredHaveError("argument does not prove the exact required premise")
            proof = ImpElim(proof, Hyp(premise_index))
            proposition = proposition.right
            kinds.append("proof")
        else:
            raise InferredHaveError("too many arguments for this hypothesis")
    return InferredHave(syntax, proposition, proof, tuple(kinds))
