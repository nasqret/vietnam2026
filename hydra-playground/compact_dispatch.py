"""Cheap, untrusted routing hints for the frozen native ``compact_arith``.

Recognize a conservative subset of its recurrence grammar, not arbitrary
polynomial identities. Every proposed command still needs ordinary native
execution and original-theorem replay. This module neither imports the compact
prover nor constructs certificates, checks proofs, or looks up theorems.

Call with the focused Goal and substitution-resolved target/context. A miss is
only a routing decision: existing simplification/ring/search must remain usable.
"""
from __future__ import annotations

from dataclasses import dataclass

from peano_lab.engine.state import Goal
from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero


DISPATCH_POLICY = "hydra-compact-recurrence-dispatch-v1"
MAX_TERM_NODES = 256
MAX_TERM_DEPTH = 48
MAX_VARIABLES = 32
MAX_CONTEXT = 64
MAX_EQUATIONS = 8
MAX_MATCH_PAIRS = 96
MAX_MATCH_DEPTH = 16
MAX_WORK = 4096
MAX_NAME_BYTES = 64

ZERO = Zero()
ONE = Succ(ZERO)
TWO = Succ(ONE)


class _Declined(ValueError):
    pass


class _UnsupportedAST(_Declined):
    pass


@dataclass(frozen=True, slots=True)
class CompactDispatchHint:
    commands: tuple[str, ...]
    reason: str
    schemas: tuple[str, ...]
    selected_assumptions: tuple[str, ...] = ()
    analysis_work: int = 0


class _Recognizer:
    def __init__(self, variables, should_stop):
        self.variables = variables
        self.should_stop = should_stop
        self.work = 0
        self.pairs = 0
        self.memo = {}
        self.tick()

    def tick(self):
        self.work += 1
        if self.work > MAX_WORK:
            raise _Declined("recognition work bound")
        if self.should_stop is not None and (self.work == 1 or self.work % 64 == 0):
            if self.should_stop():
                raise _Declined("recognition cancelled")

    def scan(self, terms):
        """Count occurrences, not identities; reject metas and cyclic/large ASTs."""
        pending = [(term, 1) for term in terms]
        nodes = 0
        while pending:
            term, depth = pending.pop()
            self.tick()
            nodes += 1
            if nodes > MAX_TERM_NODES or depth > MAX_TERM_DEPTH:
                raise _UnsupportedAST("recognition AST bound")
            if type(term) is Var:
                if type(term.index) is not int or not 0 <= term.index < self.variables:
                    raise _UnsupportedAST("out-of-scope variable")
            elif type(term) is Succ:
                pending.append((term.term, depth + 1))
            elif type(term) in (Add, Mul):
                pending.extend(((term.left, depth + 1), (term.right, depth + 1)))
            elif type(term) is not Zero:
                raise _UnsupportedAST("unsupported or unresolved term")

    @staticmethod
    def direct(left, right):
        # Empty tuples mark cheap primitive bridges usable inside a recurrence.
        # They do not, alone, justify dispatch ahead of exact/refl/simp.
        if type(left) is Add and left.right == ZERO and right == left.left:
            return ()
        if type(left) is Add and type(left.right) is Succ:
            if right == Succ(Add(left.left, left.right.term)):
                return ()
        if type(left) is Mul and left.right == ZERO and right == ZERO:
            return ()
        if type(left) is Mul and type(left.right) is Succ:
            if right == Add(Mul(left.left, left.right.term), left.left):
                return ()
        if type(right) is Succ and left == Add(right.term, ONE):
            return ()
        if type(right) is Succ and type(right.term) is Succ \
                and left == Add(right.term.term, TWO):
            return ()
        if type(left) is Mul and type(left.right) is Add \
                and left.right.right == ONE \
                and right == Add(Mul(left.left, left.right.left), left.left):
            return ("mul_add_one",)
        if type(left) is Add and type(left.left) is Succ and type(right) is Succ \
                and right.term == Add(left.left.term, left.right):
            return ("successor_left_add",)
        if type(left) is Mul and type(left.left) is Succ \
                and right == Add(Mul(left.left.term, left.right), left.right):
            return ("successor_left_mul",)
        if type(left) is Add and type(left.left) is Add and type(left.right) is Succ \
                and type(right) is Add and type(right.left) is Add and type(right.right) is Succ \
                and left.left.left == right.left.left \
                and left.left.right == right.right.term and left.right.term == right.left.right:
            return ("offset_swap",)
        if type(left) is Add and type(left.left) is Add \
                and type(left.left.left) is Mul and left.left.left.left == TWO \
                and left.left.right == left.right and type(right) is Mul and right.left == TWO \
                and type(right.right) is Add and right.right.left == left.left.left.right \
                and right.right.right == left.right:
            return ("doubling",)
        return None

    def right_zero(self, term):
        # Match the native helper exactly: it removes top-level right-zero
        # redexes, not a general simplifier or associativity normalization.
        while type(term) is Add and term.right == ZERO:
            self.tick()
            term = term.left
        return ZERO if type(term) is Mul and term.right == ZERO else term

    def match(self, left, right, depth=0):
        self.tick()
        if depth > MAX_MATCH_DEPTH:
            return None
        key = (left, right)
        if key in self.memo:
            return self.memo[key]
        self.pairs += 1
        if self.pairs > MAX_MATCH_PAIRS:
            raise _Declined("recognition pair bound")
        # Mark active pairs as misses; recursive routes may not loop.
        self.memo[key] = None
        result = self._match(left, right, depth)
        self.memo[key] = result
        return result

    def _match(self, left, right, depth):
        if left == right:
            return ()
        direct = self.direct(left, right)
        if direct is not None:
            return direct
        reverse = self.direct(right, left)
        if reverse is not None:
            return reverse
        if type(left) is Succ and type(right) is Succ:
            return self.match(left.term, right.term, depth + 1)
        if type(left) in (Add, Mul) and type(right) is type(left):
            first = self.match(left.left, right.left, depth + 1)
            if first is not None:
                second = self.match(left.right, right.right, depth + 1)
                if second is not None:
                    return tuple(dict.fromkeys(first + second))
        if self.right_zero(left) == self.right_zero(right):
            return ()
        # Native PA6 transport can finish after a supported smaller product.
        for old, new in ((left, right), (right, left)):
            if type(old) is Mul and type(old.right) is Succ \
                    and type(new) is Add and new.right == old.left:
                inner = self.match(Mul(old.left, old.right.term), new.left, depth + 1)
                if inner is not None:
                    return inner
        return None

    def replace_all(self, term, old, new):
        self.tick()
        if term == old:
            return new
        if type(term) is Succ:
            return Succ(self.replace_all(term.term, old, new))
        if type(term) in (Add, Mul):
            return type(term)(self.replace_all(term.left, old, new),
                              self.replace_all(term.right, old, new))
        return term


def _safe_name(name):
    return type(name) is str and 0 < len(name) <= MAX_NAME_BYTES \
        and (name[0].isalpha() or name[0] == "_") \
        and all(char.isalnum() or char in "_'" for char in name[1:]) \
        and len(name.encode("utf-8")) <= MAX_NAME_BYTES


def _hint(recognizer, schemas, selected=()):
    suffix = " [" + ", ".join(selected) + "]" if selected else ""
    return CompactDispatchHint(("compact_arith" + suffix,),
        "The goal matches a bounded native recurrence schema; try its compact certificate before polynomial expansion.",
        schemas, selected, recognizer.work)


def compact_arith_hint(goal, target=None, context=None, *, should_stop=None):
    """Suggest at most one ordinary tactic, or None without changing state.

    At most one explicit local equation is selected for the native doubling
    transport. No quantified theorem is specialized or invented here. Schema
    matching is not a success prediction: native certificate/resource checks
    can still reject the proposed tactic, in which case callers must fall back.
    """
    if type(goal) is not Goal:
        return None
    target = goal.target if target is None else target
    context = goal.context if context is None else context
    if type(target) is not Eq or type(context) is not tuple or len(context) > MAX_CONTEXT \
            or len(goal.variables) > MAX_VARIABLES:
        return None
    if should_stop is not None and not callable(should_stop):
        raise TypeError("should_stop must be callable")
    try:
        recognizer = _Recognizer(len(goal.variables), should_stop)
        recognizer.scan((target.left, target.right))
        schemas = recognizer.match(target.left, target.right)
        if schemas is not None:
            return _hint(recognizer, schemas) if schemas else None
        # Native selected-assumption transport has this exact right endpoint.
        # The opposite orientation is intentionally left to ordinary search.
        right = target.right
        if type(right) is not Mul or right.left != TWO or type(right.right) is not Add:
            return None
        w, value = right.right.left, right.right.right
        post = Add(Add(Mul(TWO, w), value), value)
        names = [entry[0] for entry in context if type(entry) is tuple and len(entry) == 2]
        considered = 0
        for entry in context:
            recognizer.tick()
            if type(entry) is not tuple or len(entry) != 2:
                continue
            name, formula = entry
            if type(formula) is not Eq or not _safe_name(name) or names.count(name) != 1:
                continue
            considered += 1
            if considered > MAX_EQUATIONS:
                break
            # Selected equation and target share the native aggregate AST cap.
            try:
                recognizer.scan((target.left, target.right, formula.left, formula.right))
            except _UnsupportedAST:
                # Only an unsupported assumption can be skipped. Work and
                # cancellation limits always abort the whole recognition.
                continue
            for reverse in (False, True):
                old, new = (formula.right, formula.left) if reverse else (formula.left, formula.right)
                pre = recognizer.replace_all(post, new, old)
                if pre == post:
                    continue
                recognizer.scan((target.left, pre))
                prefix = recognizer.match(target.left, pre)
                if prefix is not None:
                    schemas = tuple(dict.fromkeys(prefix + ("doubling_transport",)))
                    selected = ("<- " if reverse else "") + name
                    return _hint(recognizer, schemas, (selected,))
    except _Declined:
        return None
    return None


__all__ = ["CompactDispatchHint", "DISPATCH_POLICY", "compact_arith_hint"]
