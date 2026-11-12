#!/usr/bin/env python3
"""LAB-006: structural checks and deterministic editorial selection; no network/API."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import urlparse

VERSION = "1.0"
TABLES = ("sources", "findings", "elements", "ratings", "merge_map", "relations", "decisions")
DIMS = ("value", "burden", "long_term", "adaptability", "agency", "composability")
WEIGHTS = dict(zip(DIMS, (.30, .15, .20, .10, .15, .10)))
PROFILES = {
    "equal": dict.fromkeys(DIMS, 1 / 6),
    "long_use": dict(zip(DIMS, (.25, .15, .30, .10, .15, .05))),
    "low_effort": dict(zip(DIMS, (.25, .30, .15, .10, .15, .05))),
}
KINDS = {"mechanism", "technique", "interaction_pattern", "quality_capability", "method_system", "product", "example"}
RANKABLE = {"mechanism", "technique", "interaction_pattern", "quality_capability"}


def fail(message):
    raise ValueError(message)


def parse_json(text):
    return json.loads(text, parse_constant=lambda x: fail("Non-finite JSON: " + x))


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(root):
    data = {}
    for table in TABLES:
        path = Path(root) / (table + ".jsonl")
        rows = []
        if path.exists():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.strip():
                    try:
                        row = parse_json(line)
                    except (ValueError, TypeError) as exc:
                        fail(f"{path.name}:{n}: {exc}")
                    if not isinstance(row, dict):
                        fail(f"{path.name}:{n}: expected object")
                    rows.append(row)
        data[table] = rows
    return data


def write_data(root, data):
    Path(root).mkdir(parents=True, exist_ok=True)
    for table in TABLES:
        rows = sorted(data[table], key=lambda r: r.get("id", r.get("raw_id", "")))
        (Path(root) / (table + ".jsonl")).write_text(
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n" for r in rows), encoding="utf-8")


def taxonomy(path):
    obj = parse_json(Path(path).read_text(encoding="utf-8"))
    if obj.get("version") != VERSION:
        fail("Unsupported taxonomy version")
    cats = [r["id"] for r in obj["categories"]]
    jobs = [r["id"] for r in obj["jobs"]]
    if len(cats) != len(set(cats)) or len(jobs) != len(set(jobs)):
        fail("Duplicate taxonomy ID")
    return set(cats), set(jobs)


def validate(data, cats, jobs, complete=False):
    errors = []
    indexes = {}
    def error(where, msg):
        errors.append(f"{where}: {msg}")
    def string(row, key, where):
        if not isinstance(row.get(key), str) or not row[key].strip():
            error(where, "nonempty string required: " + key)
    def strings(row, key, where, nonempty=False):
        value = row.get(key)
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            error(where, "string list required: " + key)
        elif len(value) != len(set(value)):
            error(where, "duplicate list values: " + key)
        elif nonempty and not value:
            error(where, "nonempty list required: " + key)
    def enum(row, key, allowed, where):
        value = row.get(key)
        if not isinstance(value, str) or value not in allowed:
            error(where, "invalid " + key)
    all_ids = set()
    for table in TABLES:
        idx = {}
        for n, row in enumerate(data[table], 1):
            key = "raw_id" if table == "merge_map" else "id"
            where = f"{table}:{n}"
            string(row, key, where)
            identity = row.get(key)
            if isinstance(identity, str):
                if identity in idx or (table != "merge_map" and identity in all_ids):
                    error(where, "duplicate ID: " + identity)
                idx[identity] = row
                if table != "merge_map":
                    all_ids.add(identity)
        indexes[table] = idx
    for s in data["sources"]:
        w = s.get("id", "source")
        for key in ("url", "title", "owner", "origin_group", "language"):
            string(s, key, w)
        enum(s, "source_type", {"official_documentation", "source_code", "research", "practice_manual", "first_person_report", "review", "other"}, w)
        if type(s.get("accessed")) is not bool:
            error(w, "accessed must be boolean")
        if "retrieved_at" not in s:
            error(w, "retrieved_at field required, null if unviewed")
        if not isinstance(s.get("url"), str) or urlparse(s["url"]).scheme not in {"http", "https"} or not urlparse(s["url"]).netloc:
            error(w, "HTTP(S) URL required")
        when = s.get("retrieved_at")
        if when is not None:
            try:
                if not isinstance(when, str) or datetime.fromisoformat(when.replace("Z", "+00:00")).tzinfo is None:
                    raise ValueError("timezone missing")
            except ValueError:
                error(w, "invalid retrieved_at")
        elif s.get("accessed") is True:
            error(w, "accessed source requires retrieved_at")
    for f in data["findings"]:
        w = f.get("id", "finding")
        for key in ("task_id", "name", "description"):
            string(f, key, w)
        enum(f, "kind", KINDS, w)
        enum(f, "verification", {"verified", "lead", "inaccessible"}, w)
        strings(f, "category_ids", w, True)
        strings(f, "source_ids", w)
        if not isinstance(f.get("claims"), list):
            error(w, "claims must be list")
        else:
            for claim in f["claims"]:
                if not isinstance(claim, dict):
                    error(w, "claim must be object")
                    continue
                for key in ("source_id", "locator", "text"):
                    string(claim, key, w)
                enum(claim, "type", {"existence", "benefit", "risk", "failure", "origin"}, w)
                enum(claim, "basis", {"quote", "paraphrase", "direct_observation"}, w)
    for e in data["elements"]:
        w = e.get("id", "element")
        for key in ("name", "description", "primary_category", "family_id", "mechanism", "benefit", "evidence_summary"):
            string(e, key, w)
        for key in ("category_ids", "jobs"):
            strings(e, key, w, True)
        for key in ("raw_ids", "source_ids", "contexts", "conditions", "costs", "risks", "alternatives", "questions"):
            strings(e, key, w)
        enum(e, "kind", KINDS, w)
        enum(e, "existence", {"verified", "unverified", "disputed"}, w)
        enum(e, "evidence_effect", {"unknown", "mixed", "supports", "no_effect", "adverse"}, w)
        enum(e, "review_status", {"pending", "accepted", "quarantined"}, w)
        enum(e, "risk_status", {"unassessed", "reviewed", "unresolved_high"}, w)
        enum(e, "selection_track", {"main", "reference", "hypothesis"}, w)
    for r in data["ratings"]:
        w = r.get("id", "rating")
        for key in ("element_id", "reviewer_id", "context_id", "rubric_version"):
            string(r, key, w)
        if r.get("rubric_version") != VERSION:
            error(w, "rubric_version mismatch")
        if type(r.get("blind")) is not bool:
            error(w, "blind must be boolean")
        for field in ("scores", "rationales"):
            if not isinstance(r.get(field), dict) or set(r[field]) != set(DIMS):
                error(w, field + " must contain exactly six criteria")
        if isinstance(r.get("scores"), dict):
            for val in r["scores"].values():
                if val is not None and (type(val) is not int or not 0 <= val <= 4):
                    error(w, "score must be integer 0..4 or null")
        if isinstance(r.get("rationales"), dict):
            for val in r["rationales"].values():
                if not isinstance(val, str) or not val.strip():
                    error(w, "rationale required, including unknown")
        if "source_ids" in r:
            strings(r, "source_ids", w)
    for m in data["merge_map"]:
        w = m.get("raw_id", "mapping")
        strings(m, "element_ids", w)
        string(m, "reason", w)
        enum(m, "decision", {"canonical", "merged_variant", "composite", "split", "quarantined", "out_of_scope"}, w)
        if isinstance(m.get("element_ids"), list):
            count = len(m["element_ids"])
            if m.get("decision") in {"canonical", "merged_variant", "composite"} and count != 1:
                error(w, "mapping requires one target")
            if m.get("decision") == "split" and count < 2:
                error(w, "split requires multiple targets")
    for r in data["relations"]:
        w = r.get("id", "relation")
        for key in ("from_id", "to_id", "rationale"):
            string(r, key, w)
        enum(r, "type", {"complements", "alternative", "conflicts_with", "depends_on", "contains", "variant_of"}, w)
        enum(r, "status", {"documented", "hypothesis"}, w)
    for d in data["decisions"]:
        w = d.get("id", "decision")
        for key in ("type", "reason"):
            string(d, key, w)
        for key in ("reviewer_ids", "source_ids"):
            strings(d, key, w)
        if d.get("type") == "rating_resolution":
            string(d, "element_id", w)
            if d.get("resolved") is not True or len(d.get("reviewer_ids", [])) < 2:
                error(w, "rating resolution needs resolved=true and two reviewers")
    if errors:
        return errors
    def refs(values, table, where):
        for value in values:
            if value not in indexes[table]:
                error(where, "unknown " + table + " ID: " + value)
    for f in data["findings"]:
        w = f["id"]
        refs(f["source_ids"], "sources", w)
        for cat in f["category_ids"]:
            if cat not in cats:
                error(w, "unknown category " + cat)
        existence = False
        for c in f["claims"]:
            if c["source_id"] not in f["source_ids"]:
                error(w, "claim source missing from source_ids")
            s = indexes["sources"].get(c["source_id"], {})
            existence |= c["type"] == "existence" and s.get("accessed") is True
        if f["verification"] == "verified" and not existence:
            error(w, "verified finding lacks accessed existence claim")
    for e in data["elements"]:
        w = e["id"]
        refs(e["raw_ids"], "findings", w)
        refs(e["source_ids"], "sources", w)
        if e["primary_category"] not in e["category_ids"]:
            error(w, "primary_category not in category_ids")
        if set(e["category_ids"]) - cats or set(e["jobs"]) - jobs:
            error(w, "unknown category/job")
        if e["existence"] == "verified":
            linked = False
            for raw_id in e["raw_ids"]:
                f = indexes["findings"].get(raw_id, {})
                for c in f.get("claims", []):
                    s = indexes["sources"].get(c["source_id"], {})
                    linked |= f.get("verification") == "verified" and c["type"] == "existence" and c["source_id"] in e["source_ids"] and s.get("accessed") is True
            if not linked:
                error(w, "verified element lacks linked verified existence")
    seen_reviewers, seen_contexts = set(), set()
    for r in data["ratings"]:
        w = r["id"]
        refs([r["element_id"]], "elements", w)
        refs(r.get("source_ids", []), "sources", w)
        for seen, key in ((seen_reviewers, "reviewer_id"), (seen_contexts, "context_id")):
            pair = (r["element_id"], r[key])
            if pair in seen:
                error(w, "repeated evaluator/context for element: " + r[key])
            seen.add(pair)
    for m in data["merge_map"]:
        refs([m["raw_id"]], "findings", m["raw_id"])
        refs(m["element_ids"], "elements", m["raw_id"])
        for eid in m["element_ids"]:
            if m["raw_id"] not in indexes["elements"].get(eid, {}).get("raw_ids", []):
                error(m["raw_id"], "mapping missing reciprocal element.raw_ids")
    for e in data["elements"]:
        for raw_id in e["raw_ids"]:
            m = indexes["merge_map"].get(raw_id)
            if (complete or m is not None) and e["id"] not in (m or {}).get("element_ids", []):
                error(e["id"], "missing reciprocal merge_map for " + raw_id)
    if complete:
        for raw_id in indexes["findings"]:
            if raw_id not in indexes["merge_map"]:
                error(raw_id, "finding has no disposition")
    for r in data["relations"]:
        refs([r["from_id"], r["to_id"]], "elements", r["id"])
        if r["from_id"] == r["to_id"]:
            error(r["id"], "self relation")
    reviewers_by_element = {}
    for r in data["ratings"]:
        reviewers_by_element.setdefault(r["element_id"], set()).add(r["reviewer_id"])
    for d in data["decisions"]:
        refs(d["source_ids"], "sources", d["id"])
        if d.get("element_id"):
            refs([d["element_id"]], "elements", d["id"])
        if d["type"] == "rating_resolution" and set(d["reviewer_ids"]) - reviewers_by_element.get(d["element_id"], set()):
            error(d["id"], "resolution names unknown reviewers")
    return errors


def configuration(path=None):
    config = {"target": 200, "core": 100, "quality_floor": 60, "weights": WEIGHTS, "mode": "research"}
    if path:
        obj = parse_json(Path(path).read_text(encoding="utf-8"))
        if obj.get("rubric_version") != VERSION or obj.get("taxonomy_version") != VERSION:
            fail("RUN versions mismatch")
        config.update(obj.get("selection", {}))
    if config.get("mode") not in {"research", "synthetic_demo"}:
        fail("mode must be research or synthetic_demo")
    if type(config["target"]) is not int or not 100 <= config["target"] <= 300:
        fail("target must be integer 100..300")
    if type(config["core"]) is not int or not 1 <= config["core"] <= min(100, config["target"]):
        fail("core must be integer 1..100, no larger than target")
    if type(config["quality_floor"]) not in {int, float} or not math.isfinite(config["quality_floor"]) or not 0 <= config["quality_floor"] <= 100:
        fail("quality_floor must be 0..100")
    w = config["weights"]
    if not isinstance(w, dict) or set(w) != set(DIMS) or any(type(v) not in {int, float} or not math.isfinite(v) or v < 0 for v in w.values()) or abs(sum(w.values()) - 1) > 1e-9:
        fail("weights must match six criteria and sum to one")
    return config


def score(values, weights):
    return 25 * sum(weights[d] * values[d] for d in DIMS)


def calculate(data, cats, jobs, config):
    synthetic = any(row.get("synthetic") is True for rows in data.values() for row in rows)
    if synthetic and config.get("mode") != "synthetic_demo":
        fail("Synthetic examples cannot enter a research release; use a separate demo RUN")
    by_element = {}
    for r in data["ratings"]:
        if r["blind"] and all(r["scores"][d] is not None for d in DIMS):
            by_element.setdefault(r["element_id"], []).append(r)
    resolved = {d["element_id"] for d in data["decisions"] if d["type"] == "rating_resolution" and d.get("resolved") is True}
    eligible, excluded = [], []
    for e in sorted(data["elements"], key=lambda x: x["id"]):
        reasons = []
        for condition, reason in ((e["kind"] not in RANKABLE, "unit_not_rankable"), (e["existence"] != "verified", "existence_not_verified"), (e["review_status"] != "accepted", "review_not_accepted"), (e["risk_status"] != "reviewed", "risks_not_reviewed"), (e["selection_track"] != "main", "not_main_track")):
            if condition:
                reasons.append(reason)
        rs = by_element.get(e["id"], [])
        if len(rs) < 2:
            reasons.append("fewer_than_two_complete_blind_reviews")
        if len(rs) >= 2:
            low = {d: min(r["scores"][d] for r in rs) for d in DIMS}
            high = {d: max(r["scores"][d] for r in rs) for d in DIMS}
            median = {d: statistics.median(r["scores"][d] for r in rs) for d in DIMS}
            if any(high[d] - low[d] >= 2 for d in DIMS) and e["id"] not in resolved:
                reasons.append("unresolved_rating_disagreement")
        if reasons:
            excluded.append({"id": e["id"], "reasons": reasons})
        else:
            eligible.append({"id": e["id"], "element": e, "median": median, "low": low, "high": high, "reviewers": len(rs), "Q": score(median, config["weights"]), "Q_min": score(low, config["weights"]), "Q_max": score(high, config["weights"])})
    eligible.sort(key=lambda x: (-x["Q"], x["id"]))
    pool = [r for r in eligible if r["Q"] >= config["quality_floor"]]
    selected, seen_jobs, seen_cats, seen_families = [], set(), set(), set()
    def add(row, tier, gain=None, utility=None, reason=None):
        e = row["element"]
        selected.append({"id": row["id"], "tier": tier, "Q": row["Q"], "G": gain, "U": utility, "reason": reason or ("quality_order" if tier == "core" else "quality_and_marginal_coverage")})
        seen_jobs.update(e["jobs"])
        seen_cats.update(e["category_ids"])
        seen_families.add(e["family_id"])
    for row in pool[:config["core"]]:
        add(row, "core")
    remaining = {r["id"]: r for r in pool[config["core"]:]}
    while remaining and len(selected) < config["target"]:
        best = None
        for row in remaining.values():
            e = row["element"]
            new_jobs, new_cats = set(e["jobs"]) - seen_jobs, set(e["category_ids"]) - seen_cats
            gap = bool(new_jobs or new_cats)
            gain = .50 * len(new_jobs) / len(e["jobs"]) + .30 * len(new_cats) / len(e["category_ids"]) + .20 * (e["family_id"] not in seen_families)
            utility = .70 * row["Q"] + 30 * gain
            key = (-int(gap), -utility, -row["Q"], row["id"])
            if best is None or key < best[0]:
                best = (key, row, gain, utility, gap)
        _, row, gain, utility, gap = best
        add(row, "extension", gain, utility, "coverage_gap_first" if gap else "quality_and_marginal_coverage")
        del remaining[row["id"]]
    base_core = {s["id"] for s in selected if s["tier"] == "core"}
    scenarios = {"baseline": (config["weights"], "median"), **{k: (v, "median") for k, v in PROFILES.items()}, "opinions_low": (config["weights"], "low"), "opinions_high": (config["weights"], "high")}
    sensitivity = {}
    occurrences = dict.fromkeys((r["id"] for r in eligible), 0)
    for name, (weights, field) in scenarios.items():
        ordered = sorted(eligible, key=lambda r: (-score(r[field], weights), r["id"]))
        ids = [r["id"] for r in ordered if score(r[field], weights) >= config["quality_floor"]][:config["core"]]
        current = set(ids)
        union = base_core | current
        sensitivity[name] = {"core_ids": ids, "jaccard_with_baseline": len(base_core & current) / len(union) if union else None}
        for eid in ids:
            occurrences[eid] += 1
    boundary = pool[min(config["core"], len(pool)) - 1]["Q"] if pool else None
    audit = {"tool_version": VERSION, "config": config, "counts": {k: len(v) for k, v in data.items()}, "eligible": len(eligible), "above_floor": len(pool), "selected": len(selected), "target_reached": len(selected) >= config["target"], "missing_categories": sorted(cats - seen_cats), "missing_jobs": sorted(jobs - seen_jobs), "excluded": excluded, "below_quality_floor": [r["id"] for r in eligible if r["Q"] < config["quality_floor"]], "core_boundary_ties": [r["id"] for r in pool if r["Q"] == boundary], "sensitivity": sensitivity, "core_occurrences_in_declared_scenarios": occurrences, "status": "draft_requires_content_and_source_audit", "not_checked": ["URL contents and truth", "semantic deduplication", "reviewer independence", "efficacy", "completeness of internet coverage"]}
    audit["synthetic_input"] = synthetic
    audit["partial_or_unblinded_ratings"] = [r["id"] for r in data["ratings"] if not r["blind"] or any(r["scores"][d] is None for d in DIMS)]
    if synthetic or config.get("mode") == "synthetic_demo":
        audit["status"] = "synthetic_demo_not_research"
    return eligible, selected, audit


def snapshot_hashes(root):
    return {p.name: sha(p) for p in sorted(Path(root).glob("*.jsonl"))}


def rank(root, out, cats, jobs, config, taxonomy_path):
    data = load(root)
    errors = validate(data, cats, jobs, complete=True)
    if errors:
        fail("\n".join(errors[:50]))
    eligible, selected, audit = calculate(data, cats, jobs, config)
    output = Path(out)
    if output.exists():
        fail("Output directory already exists; choose a new release path")
    output.mkdir(parents=True)
    with (output / "quality-ranked.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["order", "score_rank", "id", "name", "Q", "Q_min", "Q_max", *DIMS, "category_ids", "jobs", "source_ids"])
        score_rank, prior_score = 0, None
        for n, r in enumerate(eligible, 1):
            e = r["element"]
            if r["Q"] != prior_score:
                score_rank, prior_score = n, r["Q"]
            writer.writerow([n, score_rank, r["id"], e["name"], round(r["Q"], 4), round(r["Q_min"], 4), round(r["Q_max"], 4), *(r["median"][d] for d in DIMS), "|".join(e["category_ids"]), "|".join(e["jobs"]), "|".join(e["source_ids"])])
    audit["input_sha256"] = snapshot_hashes(root)
    audit["taxonomy_sha256"] = sha(taxonomy_path)
    audit["tool_sha256"] = sha(__file__)
    audit["generated_at"] = datetime.now(timezone.utc).isoformat()
    dump(output / "audit.json", audit)
    dump(output / "atlas-selection.json", {"status": audit["status"], "config": config, "selected": selected})
    lines = ["# Черновик атласа — требуется содержательный аудит", "", "Это вывод по переданным оценкам. Источники и эффективность программой не проверены.", ""]
    if audit["status"] == "synthetic_demo_not_research":
        lines.extend(["ТЕХНИЧЕСКИЙ ПРИМЕР: данные вымышлены, это не результаты исследования.", ""])
    elements = {e["id"]: e for e in data["elements"]}
    sources = {s["id"]: s for s in data["sources"]}
    for s in selected:
        e = elements[s["id"]]
        lines.extend([f"## {e['id']} — {e['name']}", "", e["description"], "", "Механизм: " + e["mechanism"], "", "Возможная польза (суждение): " + e["benefit"], "", "Условия: " + "; ".join(e["conditions"]), "", "Риски: " + "; ".join(e["risks"]), "", "Свидетельства эффекта: " + e["evidence_effect"] + ". " + e["evidence_summary"], "", f"Отбор: {s['tier']}; Q={s['Q']:.2f}. ID оценок сохранены во входном снимке.", ""])
        for sid in e["source_ids"]:
            lines.append(f"- {sid}: {sources[sid]['url']}")
        lines.append("")
    (output / "ATLAS-DRAFT.md").write_text("\n".join(lines), encoding="utf-8")
    return {"eligible": len(eligible), "selected": len(selected), "target_reached": audit["target_reached"], "status": audit["status"]}


def merge(inputs, output, cats, jobs):
    dest = Path(output)
    if dest.exists():
        fail("Merge output already exists")
    merged = {k: {} for k in TABLES}
    receipts = []
    for root in inputs:
        data = load(root)
        receipts.append({"input": str(root), "sha256": snapshot_hashes(root)})
        for table in TABLES:
            key = "raw_id" if table == "merge_map" else "id"
            for row in data[table]:
                identity = row.get(key)
                if not isinstance(identity, str) or not identity.strip():
                    fail("Missing ID in merge input: " + table)
                old = merged[table].get(identity)
                if old is not None and old != row:
                    fail("Conflicting ID, explicit revision required: " + identity)
                merged[table][identity] = row
    data = {k: list(v.values()) for k, v in merged.items()}
    errors = validate(data, cats, jobs)
    if errors:
        fail("\n".join(errors[:50]))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="atlas-merge-", dir=dest.parent) as temporary:
        staged = Path(temporary) / "snapshot"
        write_data(staged, data)
        dump(staged / "MERGE.json", {"inputs": receipts, "semantic_deduplication": "not_performed"})
        if dest.exists():
            fail("Output appeared during merge")
        os.rename(staged, dest)
    return {k: len(v) for k, v in data.items()}


def manifest(root, name, checking=False):
    root = Path(root).resolve()
    if Path(name).name != name:
        fail("Manifest must be a filename")
    target = root / name
    if checking:
        obj = parse_json(target.read_text(encoding="utf-8"))
        seen = set()
        for record in obj["files"]:
            rel = Path(record["path"])
            path = root / rel
            if rel.is_absolute() or ".." in rel.parts or path.is_symlink() or not path.resolve().is_relative_to(root) or str(rel) in seen:
                fail("Unsafe/duplicate manifest path")
            seen.add(str(rel))
            if not path.is_file() or path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
                fail("Integrity mismatch: " + str(rel))
        return {"verified_files": len(seen), "meaning": "byte integrity, not authenticity or research quality"}
    if target.exists():
        fail("Manifest already exists")
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            fail("Symlinks are not allowed in bundle")
        if path.is_file():
            files.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    dump(target, {"schema_version": VERSION, "files": files})
    return {"files": len(files), "manifest": name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taxonomy", default=str(Path(__file__).resolve().parent.parent / "taxonomy.json"))
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate")
    p.add_argument("directory")
    p.add_argument("--complete", action="store_true")
    p = sub.add_parser("merge")
    p.add_argument("--out", required=True)
    p.add_argument("inputs", nargs="+")
    p = sub.add_parser("rank")
    p.add_argument("directory")
    p.add_argument("--out", required=True)
    p.add_argument("--config")
    for command in ("seal", "verify"):
        p = sub.add_parser(command)
        p.add_argument("directory")
        p.add_argument("--manifest", default="BUNDLE_MANIFEST.json")
    args = parser.parse_args()
    try:
        if args.command in {"seal", "verify"}:
            result = manifest(args.directory, args.manifest, args.command == "verify")
        else:
            cats, jobs = taxonomy(args.taxonomy)
            if args.command == "validate":
                data = load(args.directory)
                errors = validate(data, cats, jobs, args.complete)
                result = {"valid_structure": not errors, "complete_normalization_required": args.complete, "counts": {k: len(v) for k, v in data.items()}, "errors": errors, "source_truth_checked": False}
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 1 if errors else 0
            elif args.command == "merge":
                result = merge(args.inputs, args.out, cats, jobs)
            else:
                result = rank(args.directory, args.out, cats, jobs, configuration(args.config), args.taxonomy)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
