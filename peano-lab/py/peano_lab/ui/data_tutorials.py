"""Frozen, deterministic teaching scripts for Peano Lab.

Tutorial commands are data rather than code so the browser runner can show the
exact command before executing it.  A ``command`` step is not a transcript:
``tutorial.py`` sends it through the real proof-session implementation, and a
chapter marked ``requires_qed`` cannot complete until that implementation has
performed its independent kernel check.
"""

from __future__ import annotations


CHAPTERS = (
    {
        "order": 1,
        "slug": "add_comm",
        "title": "Prove add_comm by hand",
        "summary": (
            "Derive premise-free addition commutativity from PA3, PA4, and "
            "nested induction.  There is no auto call and no imported lemma: "
            "every simplification becomes a proof-term fragment."
        ),
        "requires_qed": True,
        "steps": (
            {
                "kind": "narrative",
                "title": "Why the proof needs nested induction",
                "body": (
                    "Addition recurses on its right argument, so PA3 and PA4 "
                    "simplify x + 0 and x + S y but not their mirror images.  "
                    "The inner inductions prove those mirror-image facts at "
                    "the exact moments the outer commutativity induction needs them."
                ),
            },
            {
                "kind": "command",
                "title": "State premise-free add_comm",
                "command": "pa prove forall n m. n + m = m + n",
                "note": "This is the actual theorem, from a fresh empty context.",
            },
            {
                "kind": "command",
                "title": "Fix the first addend",
                "command": "intro a",
                "note": "The remaining quantified variable is the recursive argument.",
            },
            {
                "kind": "command",
                "title": "Induct on the second addend",
                "command": "induction b",
                "note": "The base and step expose the asymmetric PA equations.",
            },
            {
                "kind": "command",
                "title": "Simplify the outer base",
                "command": "simp",
                "note": "PA3 removes a right zero, revealing the mirror-zero lemma.",
            },
            {
                "kind": "command",
                "title": "Prove the mirror-zero lemma in place",
                "command": "induction a",
                "note": "This nested induction uses no previously named theorem.",
            },
            {
                "kind": "command",
                "title": "Close the nested base",
                "command": "simp",
                "note": "Ordered PA simplification produces a checked reflexive leaf.",
            },
            {
                "kind": "command",
                "title": "Close the nested step",
                "command": "simp",
                "note": "The nested induction certificate now fills the outer base hole.",
            },
            {
                "kind": "command",
                "title": "Use the outer induction hypothesis",
                "command": "simp [IH]",
                "note": "Only the explicitly named local IH joins PA3 and PA4.",
            },
            {
                "kind": "command",
                "title": "Prove the successor mirror in place",
                "command": "induction a",
                "note": "A second nested induction establishes the remaining orientation.",
            },
            {
                "kind": "command",
                "title": "Close its base",
                "command": "simp",
                "note": "The kernel-visible PA equations discharge the base case.",
            },
            {
                "kind": "command",
                "title": "Close its step",
                "command": "simp",
                "note": "All engine goals are now filled by a concrete certificate.",
            },
            {
                "kind": "command",
                "title": "Ask the independent kernel",
                "command": "qed",
                "note": "The chapter completes only if this exact command checks.",
            },
        ),
    },
    {
        "order": 2,
        "slug": "symm_all",
        "title": "Build a toy symm_all tactical",
        "summary": (
            "Walk one small feature from semantic composition to surface "
            "grammar and tests.  The executable specimen uses the existing "
            "spelling `all_goals symm`, which is precisely the proposed alias."
        ),
        "requires_qed": True,
        "steps": (
            {
                "kind": "narrative",
                "title": "Keep the trusted kernel unchanged",
                "body": (
                    "symm_all is syntax sugar in the untrusted tactic layer.  "
                    "It composes all_goals with symm and therefore creates only "
                    "the same EqSym proof nodes that the kernel already knows."
                ),
            },
            {
                "kind": "source",
                "title": "Add the semantic helper",
                "path": "peano_lab/ui/prove.py",
                "source": (
                    "def _symm_all(classical: bool) -> Tactic:\n"
                    "    return all_goals(_primitive(\"symm\", \"\", classical))"
                ),
                "note": "Composition reuses the transactional all_goals contract.",
            },
            {
                "kind": "source",
                "title": "Add one grammar branch",
                "path": "peano_lab/ui/prove.py",
                "source": (
                    "if source == \"symm_all\":\n"
                    "    return _symm_all(classical), True"
                ),
                "note": "The branch belongs before primitive-name dispatch.",
            },
            {
                "kind": "source",
                "title": "Pin the contracts with tests",
                "path": "tests/test_ui.py",
                "source": (
                    "before = state\n"
                    "tactic, _ = _compile(\"symm_all\", False)\n"
                    "after = tactic(before, \"\")\n"
                    "assert undo(after) is before\n"
                    "closed = _compile(\"all_goals refl\", False)[0](after, \"\")\n"
                    "checked_final(closed, target)"
                ),
                "note": (
                    "Test both one-command undo and final kernel checking; also "
                    "test that failure publishes no partial state."
                ),
            },
            {
                "kind": "command",
                "title": "Open a two-goal specimen",
                "command": "pa prove (0 = 0) /\\ (S 0 = S 0)",
                "note": "A conjunction makes all_goals observable.",
            },
            {
                "kind": "command",
                "title": "Create both equality goals",
                "command": "split",
                "note": "There are now two certificate holes in a fixed order.",
            },
            {
                "kind": "command",
                "title": "Run the alias semantics",
                "command": "all_goals symm",
                "note": "This is the behavior the proposed symm_all spelling aliases.",
            },
            {
                "kind": "command",
                "title": "Close every reversed equality",
                "command": "all_goals refl",
                "note": "The compound action remains one transaction.",
            },
            {
                "kind": "command",
                "title": "Kernel-check the generated certificate",
                "command": "qed",
                "note": "A UI feature earns QED only through the ordinary checker.",
            },
        ),
    },
)


__all__ = ["CHAPTERS"]
