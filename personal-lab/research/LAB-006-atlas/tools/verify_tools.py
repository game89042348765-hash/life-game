#!/usr/bin/env python3
"""Technical checks with invented data only. This is not an atlas research run."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("atlas", HERE / "atlas.py")
atlas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atlas)


def fixture(n):
    data = {k: [] for k in atlas.TABLES}
    for i in range(n):
        suffix = f"DEMO-{i:05d}"
        sid, fid, eid = "S-" + suffix, "F-" + suffix, "E-" + suffix
        cat, job = f"C{i % 32 + 1:02d}", f"J{i % 12 + 1:02d}"
        data["sources"].append({"id": sid, "url": "https://example.invalid/" + suffix, "title": "Вымышленный источник для проверки программы", "owner": "synthetic_fixture", "origin_group": "SYNTHETIC-" + suffix, "source_type": "other", "language": "ru", "retrieved_at": "2026-11-12T00:00:00+00:00", "accessed": True, "synthetic": True})
        data["findings"].append({"id": fid, "task_id": "SYNTHETIC-DEMO", "name": "Вымышленная находка " + suffix, "description": "Технические данные, не результат поиска.", "kind": "mechanism", "category_ids": [cat], "source_ids": [sid], "verification": "verified", "claims": [{"type": "existence", "source_id": sid, "locator": "synthetic fixture", "text": "Этот факт вымышлен и используется только в тесте.", "basis": "paraphrase"}], "synthetic": True})
        data["elements"].append({"id": eid, "name": "Вымышленный механизм " + suffix, "description": "Пример структуры, не существующая рекомендация.", "kind": "mechanism", "primary_category": cat, "category_ids": [cat], "jobs": [job], "family_id": f"FAM-DEMO-{i // 2:05d}", "raw_ids": [fid], "source_ids": [sid], "mechanism": "Условное правило технического примера.", "benefit": "Не проверялась; вымышленное аналитическое поле.", "evidence_effect": "unknown", "evidence_summary": "Реальные источники не изучались.", "contexts": ["synthetic"], "conditions": ["Только проверка формата"], "costs": [], "risks": ["Нельзя выдавать за исследование"], "alternatives": [], "questions": [], "existence": "verified", "review_status": "accepted", "risk_status": "reviewed", "selection_track": "main", "synthetic": True})
        data["merge_map"].append({"raw_id": fid, "element_ids": [eid], "decision": "canonical", "reason": "Соответствие один к одному только для технического теста."})
        for reviewer in ("A", "B"):
            scores = dict.fromkeys(atlas.DIMS, 3)
            scores["value"] = i % 4 + 1
            data["ratings"].append({"id": "R-" + reviewer + "-" + suffix, "element_id": eid, "reviewer_id": "synthetic-" + reviewer, "context_id": "synthetic-context-" + reviewer, "rubric_version": "1.0", "blind": True, "scores": scores, "rationales": dict.fromkeys(atlas.DIMS, "Заданное тестовое значение, не экспертная оценка."), "source_ids": [sid], "synthetic": True})
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report")
    args = p.parse_args()
    cats, jobs = atlas.taxonomy(HERE.parent / "taxonomy.json")
    config = atlas.configuration()
    config.update({"mode": "synthetic_demo", "core": 3, "target": 100})
    results = []
    def check(name, action):
        start = time.perf_counter()
        details = action()
        results.append({"check": name, "passed": True, "seconds": round(time.perf_counter() - start, 4), "details": details})
    def raises(action, text):
        try:
            action()
        except ValueError as exc:
            assert text in str(exc), str(exc)
        else:
            raise AssertionError("Expected failure: " + text)
    data = fixture(12)
    with tempfile.TemporaryDirectory(prefix="lab006-technical-") as temporary:
        root = Path(temporary)
        source = root / "dataset"
        atlas.write_data(source, data)
        def valid():
            assert atlas.validate(data, cats, jobs, True) == []
            return {"elements": 12, "ratings": 24}
        check("complete_schema_and_provenance_links", valid)
        def cli():
            run = root / "RUN.demo.json"
            atlas.dump(run, {"rubric_version": "1.0", "taxonomy_version": "1.0", "selection": config})
            before = atlas.snapshot_hashes(source)
            process = subprocess.run([sys.executable, str(HERE / "atlas.py"), "rank", str(source), "--config", str(run), "--out", str(root / "release")], capture_output=True, text=True, timeout=60)
            assert process.returncode == 0, process.stderr
            result = json.loads(process.stdout)
            assert result["status"] == "synthetic_demo_not_research"
            assert result["selected"] == 12 and result["target_reached"] is False
            audit = json.loads((root / "release/audit.json").read_text())
            assert len(audit["sensitivity"]) == 6
            assert atlas.snapshot_hashes(source) == before
            assert "ТЕХНИЧЕСКИЙ ПРИМЕР" in (root / "release/ATLAS-DRAFT.md").read_text()
            return result
        check("real_cli_outputs_hashes_and_incomplete_target", cli)
        def unknown():
            changed = copy.deepcopy(data)
            changed["ratings"][0]["scores"]["value"] = None
            assert not atlas.validate(changed, cats, jobs, True)
            ranked, selected, audit = atlas.calculate(changed, cats, jobs, config)
            eid = changed["elements"][0]["id"]
            assert eid not in {r["id"] for r in ranked}
            assert any(r["id"] == eid and "fewer_than_two_complete_blind_reviews" in r["reasons"] for r in audit["excluded"])
            return "null stays unknown; candidate not promoted"
        check("unknown_not_zero_or_imputed", unknown)
        def invalid():
            cases = []
            changed = copy.deepcopy(data)
            changed["elements"][0]["source_ids"] = ["MISSING"]
            cases.append(changed)
            changed = copy.deepcopy(data)
            changed["merge_map"].pop()
            cases.append(changed)
            changed = copy.deepcopy(data)
            changed["sources"][0]["accessed"] = False
            cases.append(changed)
            changed = copy.deepcopy(data)
            changed["ratings"][0]["scores"]["value"] = True
            cases.append(changed)
            for changed in cases:
                assert atlas.validate(changed, cats, jobs, True)
            return "missing source, lost disposition, unviewed existence, boolean score rejected"
        check("critical_invalid_inputs_rejected", invalid)
        def independence():
            for key in ("reviewer_id", "context_id"):
                changed = copy.deepcopy(data)
                changed["ratings"][1][key] = changed["ratings"][0][key]
                assert atlas.validate(changed, cats, jobs, True)
            changed = copy.deepcopy(data)
            changed["ratings"][0]["rubric_version"] = "9.0"
            assert atlas.validate(changed, cats, jobs, True)
            return "duplicate reviewer/context and wrong rubric rejected"
        check("review_identity_and_version", independence)
        def gates():
            changed = copy.deepcopy(data)
            changed["elements"][0]["kind"] = "method_system"
            changed["elements"][1]["selection_track"] = "reference"
            changed["elements"][2]["risk_status"] = "unresolved_high"
            changed["elements"][3]["existence"] = "disputed"
            for r in changed["ratings"]:
                if r["element_id"] == changed["elements"][4]["id"]:
                    r["scores"] = dict.fromkeys(atlas.DIMS, 0)
            assert not atlas.validate(changed, cats, jobs, True)
            ranked, selected, audit = atlas.calculate(changed, cats, jobs, config)
            excluded = {r["id"] for r in audit["excluded"]}
            assert {e["id"] for e in changed["elements"][:4]} <= excluded
            assert changed["elements"][4]["id"] in audit["below_quality_floor"]
            assert changed["elements"][4]["id"] not in {s["id"] for s in selected}
            return "composites, reference, unresolved risks and disputed existence blocked; low quality not used as filler"
        check("eligibility_and_quality_floor", gates)
        def disagreement():
            changed = copy.deepcopy(data)
            changed["ratings"][0]["scores"]["value"] = 1
            changed["ratings"][1]["scores"]["value"] = 4
            eid = changed["elements"][0]["id"]
            _, _, audit = atlas.calculate(changed, cats, jobs, config)
            assert any(e["id"] == eid and "unresolved_rating_disagreement" in e["reasons"] for e in audit["excluded"])
            changed["decisions"].append({"id": "D-SYNTHETIC", "element_id": eid, "type": "rating_resolution", "resolved": True, "reason": "Технический пример фиксации разрешённого расхождения.", "reviewer_ids": ["synthetic-A", "synthetic-B"], "source_ids": []})
            assert not atlas.validate(changed, cats, jobs, True)
            ranked, _, _ = atlas.calculate(changed, cats, jobs, config)
            row = next(r for r in ranked if r["id"] == eid)
            assert row["Q_min"] < row["Q_max"]
            return "resolution required; original range retained"
        check("disagreement_gate_and_auditable_resolution", disagreement)
        def stable():
            baseline = atlas.calculate(data, cats, jobs, config)
            changed = copy.deepcopy(data)
            rng = random.Random(20261112)
            for rows in changed.values():
                rng.shuffle(rows)
            result = atlas.calculate(changed, cats, jobs, config)
            assert baseline[1] == result[1]
            assert [r["id"] for r in baseline[0]] == [r["id"] for r in result[0]]
            assert baseline[2]["sensitivity"] == result[2]["sensitivity"]
            return "rank, selection and sensitivity independent of input row order"
        check("deterministic_with_shuffled_input", stable)
        def merging():
            merged = root / "merged"
            result = atlas.merge([source, source], merged, cats, jobs)
            assert result["elements"] == 12
            changed = copy.deepcopy(data)
            changed["elements"][0]["description"] = "CONFLICT"
            other = root / "conflict"
            atlas.write_data(other, changed)
            refused = root / "refused"
            raises(lambda: atlas.merge([source, other], refused, cats, jobs), "Conflicting ID")
            assert not refused.exists()
            return "exact IDs coalesced; conflicting revision stops without output"
        check("merge_no_silent_overwrite", merging)
        def integrity():
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "a.txt").write_text("original", encoding="utf-8")
            atlas.manifest(bundle, "FILES.json")
            assert atlas.manifest(bundle, "FILES.json", True)["verified_files"] == 1
            (bundle / "a.txt").write_text("changed", encoding="utf-8")
            raises(lambda: atlas.manifest(bundle, "FILES.json", True), "Integrity mismatch")
            raises(lambda: atlas.calculate(data, cats, jobs, atlas.configuration()), "Synthetic examples")
            return "byte change caught; synthetic fixtures blocked from research mode"
        check("integrity_and_demo_separation", integrity)
        def scale():
            large = fixture(10000)
            assert atlas.validate(large, cats, jobs, True) == []
            cfg = atlas.configuration()
            cfg["mode"] = "synthetic_demo"
            ranked, selected, audit = atlas.calculate(large, cats, jobs, cfg)
            assert len(ranked) == 10000 and len(selected) == 200
            assert len({s["id"] for s in selected}) == 200
            assert not audit["missing_categories"] and not audit["missing_jobs"]
            return {"synthetic_elements": 10000, "synthetic_ratings": 20000, "selected": 200, "real_web_sources": 0}
        check("ten_thousand_synthetic_elements", scale)
    report = {"status": "technical_checks_only_not_research", "checks_passed": len(results), "checks": results, "tool_sha256": atlas.sha(HERE / "atlas.py"), "verifier_sha256": atlas.sha(__file__), "python": sys.version.split()[0], "network_requests": 0}
    if args.report:
        path = Path(args.report)
        if path.exists():
            raise ValueError("Report exists; preserve previous verification")
        atlas.dump(path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
