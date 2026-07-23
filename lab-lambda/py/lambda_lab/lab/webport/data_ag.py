"""Frozen AlphaGeometry DD+AR demo proofs for the browser build.

Frozen from the desktop YAML files in ``lambda_lab/proofs/alphageometry/``
(``angle_bisector.yaml``, ``imo_p4.yaml``, ``isogonal.yaml`` — all three fit
well under the size cap). The desktop data is Polish-only; since the browser
build ships English UI text, the prose was translated to English while the
mathematical content, step structure, and ASCII diagrams are kept verbatim.
"""

from __future__ import annotations

PROOFS = {
    "angle_bisector": {
        "title": "Proof: in an isosceles triangle the angle bisector coincides with the altitude",
        "problem": (
            "In triangle ABC let AB = AC. Let D be the point on BC such\n"
            "that AD is the bisector of angle BAC. Show that AD ⟂ BC."
        ),
        "diagram": (
            "      A\n"
            "     /|\\\n"
            "    / | \\\n"
            "   /  |  \\\n"
            "  /   |   \\\n"
            "  B---D----C"
        ),
        "aux": [
            "Choosing AD as the bisector of ∠BAC — AD is the common side of triangles ABD and ACD.",
        ],
        "steps": [
            {
                "premises": [
                    "AB = AC (assumption)",
                    "AD = AD (common side)",
                    "∠BAD = ∠CAD (AD is the bisector)",
                ],
                "rule": "SAS (side-angle-side)",
                "conclusion": "△ABD ≅ △ACD",
                "why": "Triangle congruence rules — side-angle-side.",
            },
            {
                "premises": ["△ABD ≅ △ACD"],
                "rule": "property of congruent triangles",
                "conclusion": "∠ADB = ∠ADC",
                "why": "Corresponding angles of congruent triangles are equal.",
            },
            {
                "premises": [
                    "∠ADB + ∠ADC = 180°",
                    "∠ADB = ∠ADC",
                ],
                "rule": "algebra (linear arithmetic)",
                "conclusion": "∠ADB = 90°",
                "why": "Half of 180° is 90° — this is where AlphaGeometry's AR module works.",
            },
        ],
        "conclusion": "AD ⟂ BC. ◻",
    },
    "imo_p4": {
        "title": "IMO 2015/P4 (simplified DD+AR sketch, illustrative)",
        "problem": (
            "Let triangle ABC have circumcircle Ω. Points D and E lie on\n"
            "sides AB and AC respectively so that DE ∥ BC. Show that the\n"
            "circumcircle of △ADE is tangent to Ω at A."
        ),
        "diagram": (
            "          Ω\n"
            "        __.__\n"
            "      /    A    \\\n"
            "     |   /  \\    |\n"
            "     |  D----E   |\n"
            "      \\ /    \\ /\n"
            "       B------C"
        ),
        "aux": [
            "The LM proposed an auxiliary: consider the tangent to Ω at A.",
            "Let ℓ be that tangent.",
        ],
        "steps": [
            {
                "premises": ["DE ∥ BC (assumption)"],
                "rule": "DD — Thales' theorem",
                "conclusion": "AD / AB = AE / AC",
            },
            {
                "premises": [
                    "∠(ℓ, AB) = ∠ACB (tangent–chord angle)",
                    "DE ∥ BC  ⇒  ∠ADE = ∠ABC",
                ],
                "rule": "AR — angle chasing + equalities",
                "conclusion": "∠(ℓ, AD) = ∠ADE",
                "why": "We compute the angle difference: ℓ sees A at an angle equal to ∠ADE.",
            },
            {
                "premises": ["∠(ℓ, AD) = ∠ADE"],
                "rule": "DD — tangency criterion for a circle",
                "conclusion": "ℓ is tangent to the circumcircle of △ADE at the point A.",
            },
            {
                "premises": [
                    "ℓ is tangent to Ω at A",
                    "ℓ is tangent to the circle of △ADE at A",
                ],
                "rule": "DD — two tangents at the same point",
                "conclusion": "The circles are tangent (internally/externally) at A.",
            },
        ],
        "conclusion": "The circumcircle of △ADE is tangent to Ω at A. ◻",
    },
    "isogonal": {
        "title": "Lemma: isogonal conjugation with respect to a triangle",
        "problem": (
            "Let P be any point inside △ABC. Let P' be the isogonal\n"
            "conjugate of P with respect to △ABC. Show that the reflections\n"
            "of P in the sides of the triangle lie on one circle centred at P'."
        ),
        "diagram": "(omitted — too intricate for ASCII; see slide 38)",
        "aux": [
            "Let Pa, Pb, Pc denote the reflections of P in the sides BC, CA, AB.",
            "The LM proposed: consider the circumcircle of △Pa Pb Pc and its centre O.",
        ],
        "steps": [
            {
                "premises": [
                    "|P Pa| = 2 · dist(P, BC) (definition of reflection)",
                    "|P Pb| = 2 · dist(P, CA)",
                    "|P Pc| = 2 · dist(P, AB)",
                ],
                "rule": "AR — distance algebra",
                "conclusion": "O = P' (equal distances)",
                "why": "The algebraic module: P' is the point at which the distances to Pa, Pb, Pc are equal.",
            },
            {
                "premises": ["O = P'"],
                "rule": "DD — geometric deduction",
                "conclusion": "Pa, Pb, Pc lie on a circle centred at P'.",
                "why": "By the definition of a circle: all points equidistant from O are concyclic.",
            },
        ],
        "conclusion": "The reflections of P in the sides of △ABC lie on a circle around P'. ◻",
    },
}
