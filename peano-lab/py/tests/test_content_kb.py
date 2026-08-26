from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from peano_lab.ui.data_kb import (
    CARDS,
    KBCard,
    get_card,
    list_cards,
    render_card,
    render_index,
    search_cards,
)


EXPECTED_SLUGS = (
    "pa1",
    "pa2",
    "pa3",
    "pa4",
    "pa5",
    "pa6",
    "induction-schema",
    "de-bruijn-indices",
    "lcf-vs-proof-terms",
    "de-bruijn-criterion",
    "simp-termination",
    "godel-limits",
    "heyting-vs-classical-pa",
)


def test_cards_have_a_stable_complete_order_and_schema() -> None:
    assert tuple(card.slug for card in CARDS) == EXPECTED_SLUGS
    assert list_cards() is CARDS
    assert len({card.slug for card in CARDS}) == len(CARDS)
    for card in CARDS:
        assert type(card) is KBCard
        assert card.title.strip()
        assert card.summary.strip()
        assert card.body.strip()
        assert card.related_commands


def test_the_six_rule_constants_are_stated_exactly() -> None:
    statements = {
        "pa1": "∀x. ¬(S x = 0)",
        "pa2": "∀x y. S x = S y → x = y",
        "pa3": "∀x. x + 0 = x",
        "pa4": "∀x y. x + S y = S (x + y)",
        "pa5": "∀x. x · 0 = 0",
        "pa6": "∀x y. x · S y = x · y + x",
    }
    for slug, statement in statements.items():
        card = get_card(slug)
        assert card is not None
        assert statement in card.body


def test_required_concept_cards_name_their_limits_and_soundness_boundaries() -> None:
    induction = get_card("induction-schema")
    indices = get_card("de-bruijn-indices")
    architecture = get_card("lcf-vs-proof-terms")
    criterion = get_card("de-bruijn-criterion")
    simp = get_card("simp-termination")
    limits = get_card("godel-limits")
    logic = get_card("heyting-vs-classical-pa")
    assert all(
        card is not None
        for card in (induction, indices, architecture, criterion, simp, limits, logic)
    )
    assert "infinite, effective schema" in induction.body
    assert "silently capture" in indices.body
    assert "original goal" in architecture.body
    assert "imports nothing" in criterion.body
    assert "well-founded orders—not the browser step cap" in simp.body
    assert "rigid de Bruijn variables" in simp.body
    assert "not an unprovability result" in limits.body
    assert "classical on" in logic.body and "not the meanings" in logic.body


def test_lookup_is_convenient_but_unknown_slugs_remain_explicit() -> None:
    assert get_card(" PA1 ") is CARDS[0]
    assert get_card("de_bruijn_criterion").slug == "de-bruijn-criterion"
    assert get_card("not-a-card") is None
    with pytest.raises(TypeError, match="slug must be text"):
        get_card(1)  # type: ignore[arg-type]


def test_search_is_deterministic_and_accent_insensitive() -> None:
    assert search_cards("") is CARDS
    assert search_cards("Gödel") == (get_card("godel-limits"),)
    assert search_cards("godel consistency") == (get_card("godel-limits"),)
    assert search_cards("de bruijn") == (
        get_card("de-bruijn-indices"),
        get_card("de-bruijn-criterion"),
        get_card("simp-termination"),
    )
    assert search_cards("recursive equation") == (
        get_card("pa3"),
        get_card("pa4"),
        get_card("pa5"),
        get_card("pa6"),
    )
    assert search_cards("no such topic") == ()
    with pytest.raises(TypeError, match="query must be text"):
        search_cards(None)  # type: ignore[arg-type]


def test_rendering_is_plain_deterministic_text() -> None:
    expected = (
        "PA1 — zero is not a successor\n"
        "No successor is equal to zero.\n\n"
        "Formal rule constant: ∀x. ¬(S x = 0), where ¬A abbreviates "
        "A → ⊥. PA1 separates zero from every number visibly built with S. "
        "It does not by itself prove that every nonzero number is a successor; "
        "that is a different statement requiring a derivation.\n\n"
        "Related commands:\n"
        "  pa axioms\n"
        "  pa prove forall x. ~(S x = 0)"
    )
    assert render_card("pa1") == expected
    assert render_card(CARDS[0]) == expected
    with pytest.raises(KeyError):
        render_card("missing")
    with pytest.raises(TypeError, match="KBCard or slug"):
        render_card(None)  # type: ignore[arg-type]


def test_rendered_index_preserves_source_order_and_handles_no_results() -> None:
    index = render_index()
    assert index.startswith("Peano Lab knowledge base\n  pa1")
    assert index.index("pa6") < index.index("induction-schema")
    assert render_index(()) == "Peano Lab knowledge base\n  No cards matched."
    with pytest.raises(TypeError, match="tuple of KBCard"):
        render_index(list(CARDS))  # type: ignore[arg-type]


def test_card_values_are_immutable_and_validate_new_content() -> None:
    with pytest.raises(FrozenInstanceError):
        CARDS[0].title = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="slug"):
        KBCard("Bad slug", "Title", "Summary", "Body", ("pa axioms",))
    with pytest.raises(ValueError, match="related commands"):
        KBCard("valid", "Title", "Summary", "Body", ())
