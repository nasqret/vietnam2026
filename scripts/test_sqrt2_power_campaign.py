"""Planning integrity tests; none of these tests proves irrationality."""
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import urlsplit, unquote
import posixpath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_sqrt2_power_campaign import (
    ROOT, OUTPUT, PINS, generated_files, parent_bytes, validate_plan, extend_atlas,
)
from constructive_proof_explorer_template import (
    ProofExplorerTemplateError, render_canonical_campaign_plan,
)
from sqrt2_power_campaign_spec import campaign_plan


@lru_cache(maxsize=1)
def files():
    return generated_files()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for name in ("href", "src"):
            if name in attrs:
                self.links.append(attrs[name])


class CampaignPlanTests(unittest.TestCase):
    def test_inventory_is_explicitly_unproved(self):
        p = campaign_plan()
        a = validate_plan(p)
        self.assertEqual(a["counts"], {"definition": 26, "lemma": 87, "engineering": 9})
        self.assertEqual(sum(n["kind"] == "lemma" and n["phase"] == 1 for n in p["nodes"]), 81)
        self.assertEqual(p["verified_new_theorem_count"], 0)
        self.assertEqual(p["active_target"], "IR072")
        self.assertEqual(p["next_target"], "TR006")

    def test_every_edge_is_typed_and_strictly_acyclic(self):
        a = validate_plan(campaign_plan())
        self.assertEqual(len(a["order"]), 122)
        for e in a["edges"]:
            self.assertLess(a["ranks"][e["source"]], a["ranks"][e["target"]])
            self.assertNotEqual(e["kind"], "proof_dependency")
        self.assertEqual({e["kind"] for e in a["edges"]}, {
            "planned_prerequisite", "engineering_prerequisite",
            "proposed_definition_dependency", "proposed_definition_use"})

    def test_twelve_fixed_pilot_children_do_not_close_parents(self):
        p = campaign_plan()
        self.assertEqual([c["id"] for c in p["pilot"]], [f"P{i:02d}" for i in range(1, 13)])
        self.assertTrue(all(c["closes_parent"] is False for c in p["pilot"]))
        self.assertEqual(p["budget"]["retry_limit_without_contract_change"], 0)
        self.assertIn("pilot.html", files())
        self.assertIn("share", files()["pilot.html"].decode())

    def test_rejects_forged_pilot_parent_closure(self):
        self.mutate(lambda p: p["pilot"][0].update(closes_parent=True))

    def test_rejects_wrong_pilot_scope(self):
        self.mutate(lambda p: p["pilot"].pop())

    def mutate(self, change):
        p = campaign_plan()
        change(p)
        with self.assertRaises(ValueError):
            validate_plan(p)

    def test_rejects_fake_theorem_count(self):
        self.mutate(lambda p: p.update(verified_new_theorem_count=1))

    def test_rejects_boolean_count(self):
        self.mutate(lambda p: p.update(verified_new_theorem_count=False))

    def test_rejects_unknown_dependency(self):
        self.mutate(lambda p: p["nodes"][0]["deps"].append("IR999"))

    def test_rejects_cycles(self):
        self.mutate(lambda p: p["nodes"][0]["deps"].append("IRD02"))

    def test_rejects_definition_assuming_theorem(self):
        self.mutate(lambda p: p["nodes"][0]["deps"].append("IR001"))

    def test_rejects_duplicate_parameter(self):
        self.mutate(lambda p: p["nodes"][0].update(parameters=["p", "p", "d"]))

    def test_rejects_forged_expansion(self):
        self.mutate(lambda p: p["nodes"][0].update(expansion_ast_sha256="0"*64))

    def test_rejects_forged_native_receipt(self):
        self.mutate(lambda p: next(n for n in p["nodes"] if n["id"] == "IR072").update(native_ha_receipt="done"))

    def test_rejects_irrationality_depending_on_transcendence(self):
        self.mutate(lambda p: next(n for n in p["nodes"] if n["id"] == "IR072")["deps"].append("TR006"))

    def test_primary_route_does_not_depend_on_compiler_or_negative_checkpoint(self):
        p = campaign_plan()
        ns = {n["id"]: n for n in p["nodes"]}
        seen = set()
        def visit(key):
            if key in seen: return
            seen.add(key)
            for d in ns[key]["deps"]: visit(d)
        visit("IR072")
        self.assertNotIn("ENG009", seen)
        self.assertNotIn("IR065", seen)
        self.assertIn("IR070", seen)
        self.assertIn("IR081", seen)
        self.assertIn("IR078", seen)

    def test_parent_hashes_remain_pinned(self):
        for name, data in parent_bytes().items():
            self.assertEqual(sha256(data).hexdigest(), PINS[name])

    def test_atlas_extension_preserves_every_old_record(self):
        parent = json.loads(parent_bytes()["campaign.json"])
        new = extend_atlas(parent, campaign_plan())
        self.assertEqual(new["nodes"][:144], parent["nodes"])
        self.assertEqual(new["families"][:12], parent["families"])
        for key in ("definitions", "ambitious_boundaries", "current_proof_family_packages"):
            self.assertEqual(new[key], parent[key])
        self.assertEqual(new["meta"]["current_alpha_checked_use_count"], 4318)
        self.assertEqual(new["meta"]["goal_count"], 122)
        self.assertEqual([n["status"] for n in new["nodes"][-2:]], ["open", "open"])

    def test_canonical_shell_and_no_fake_proof_reader(self):
        page = files()["index.html"].decode()
        for cls in ("family-page", "family-hero", "family-main", "view-grid", "view-card", "release-note", "hero-actions"):
            self.assertIn(cls, page)
        self.assertIn("Planning, not proof evidence", page)
        self.assertNotIn("Read the final theorem", page)
        self.assertNotIn("explorer/defined/tag/IR072", page)
        self.assertEqual(files()["assets/proofs.css"], (ROOT / "deploy/proofs/proofs.css").read_bytes())

    def test_planning_renderer_rejects_completed_status(self):
        p = campaign_plan()
        p["nodes"][0]["status"] = "checked"
        with self.assertRaises(ProofExplorerTemplateError):
            render_canonical_campaign_plan(p, revision="c43219950514")

    def test_all_local_planning_page_links_resolve(self):
        for name, data in files().items():
            if not name.endswith(".html"):
                continue
            parser = Links()
            parser.feed(data.decode())
            self.assertEqual(len(parser.ids), len(set(parser.ids)), name)
            for link in parser.links:
                parts = urlsplit(link)
                if parts.scheme or parts.netloc or not parts.path: continue
                path = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parts.path)))
                if path.endswith("/"): path += "index.html"
                self.assertIn(path, files(), (name, link, path))

    def test_no_network_dependency_for_planning_map(self):
        source = files()["assets/campaign-plan.js"].decode()
        self.assertNotIn("fetch(", source)
        self.assertNotIn("innerHTML", source)
        self.assertIn('e.setAttribute(key, String(value))', source)
        page = files()["map.html"].decode()
        raw = page.split('<script type="application/json" id="plan-data">', 1)[1].split("</script>", 1)[0]
        self.assertEqual(json.loads(raw)["active_target"], "IR072")

    def test_global_map_has_bidirectional_planning_navigation(self):
        page = files()["grand-campaign/index.html"].decode()
        self.assertIn('id: "D06"', page)
        self.assertIn('D06: { x: 797, y: 55 }', page)
        self.assertNotIn("120 major campaign milestones", page)
        self.assertIn("data-plan-navigation", page)
        self.assertIn("../map.html?target=IR072", page)
        raw = page.split('<script type="application/json" id="campaign-data">',1)[1].split("</script>",1)[0]
        self.assertEqual(json.loads(raw), json.loads(files()["grand-campaign/campaign.json"]))

    def test_manifest_hashes_all_outputs_except_itself(self):
        all_files = files()
        manifest = json.loads(all_files["api/manifest.json"])
        self.assertEqual(set(manifest["files"]), set(all_files)-{"api/manifest.json"})
        for name, row in manifest["files"].items():
            self.assertEqual(row, {"bytes":len(all_files[name]), "sha256":sha256(all_files[name]).hexdigest()})

    def test_regeneration_is_byte_deterministic(self):
        # The CLI builds the persisted snapshot in a separate bounded process.
        # Compare one independent regeneration against every saved byte, without
        # retaining two full generations in this process's allocator lifetime.
        regenerated = generated_files()
        persisted = {str(p.relative_to(OUTPUT)) for p in OUTPUT.rglob("*") if p.is_file()}
        self.assertEqual(set(regenerated), persisted)
        for name, data in regenerated.items():
            self.assertEqual(data, (OUTPUT / name).read_bytes(), name)

    def test_checked_arithmetic_links_go_both_to_parents_and_back(self):
        for case, parent in (("NG001", "IR003"), ("SN002", "IR032"), ("SN003", "IR031"), ("CV001", "IR079"),
                             ("RN001","IR031"),("RN002","IR031"),("SI001","IR046"),
                             ("QN001","IR046"),("QF001","IR046")):
            self.assertIn('href="../checked/'+case+'.html"', files()["lemmas/"+parent+".html"].decode())
            self.assertIn('target='+parent+'&amp;view=prerequisites', files()["checked/"+case+".html"].decode())
            self.assertIn("planning contract above remains open", files()["lemmas/"+parent+".html"].decode())
        self.assertIn('href="arithmetic-frontier.html"', files()["map.html"].decode())

    def test_current_wave_has_33_exact_statements_and_preserves_eight_failures(self):
        wave = json.loads(files()["api/wave-results.json"])
        self.assertEqual(wave["counts"]["unique_HA_statements"], 33)
        self.assertEqual(wave["counts"]["unique_Lean_checked_statements"], 33)
        self.assertEqual(wave["counts"]["failed_or_unchecked_attempts"], 8)
        self.assertEqual(len(wave["rows"]), 42)
        self.assertEqual(wave["IR_parents_closed"], 0)


if __name__ == "__main__":
    unittest.main()
