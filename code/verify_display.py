"""Offline integrity check for the seven-file display-aggregate layout.

This checks frozen values and file structure. It cannot recover inputs or
recompute estimates, establish disclosure safety, or grant publication rights.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

COUNTS = {"V1": 36, "V2": 96, "V4": 66, "rq1_screens": 72,
          "measurement": 12, "measurement_classes": 10,
          "supp_sprint_rank": 16, "supp_two_part": 12}
FILES = {"data/display_cells.json", "data/field_schema.json", "PAPER_OBJECT_MAP.json",
         "code/verify_display.py", "README.md", "PROVENANCE.md"}
LICENSE_FILES = {"LICENSES/DATA-CC-BY-4.0.md", "LICENSES/CODE-MIT.txt"}
FORBIDDEN = {"N", "reference_support_n", "excluded_n"}
FORBIDDEN_KEYS = {"screen_id", "project_id", "issue_id", "comment_id", "sprint_id"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def summary(payload: dict) -> list[dict]:
    return [{"id": obj["id"], "paper_label": obj["paper_label"],
             "scalar_cells": len(obj["cells"]),
             "context_field_shapes": [list(shape) for shape in sorted(
                 {tuple(sorted(cell["context"])) for cell in obj["cells"]})],
             "arms": sorted({cell["arm"] for cell in obj["cells"]}),
             "quantities": sorted({cell["quantity"] for cell in obj["cells"]})}
            for obj in payload["objects"]]


def verify(folder: Path) -> dict:
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("invalid_package_directory")
    manifest = read(folder / "MANIFEST.json")
    version = manifest["schema_version"]
    expected = FILES if version == 1 else FILES | LICENSE_FILES if version == 2 else set()
    if not expected:
        raise ValueError("manifest_schema_mismatch")
    members = {p.relative_to(folder).as_posix(): p for p in folder.rglob("*")
               if p.is_file() or p.is_symlink()}
    if set(members) != expected | {"MANIFEST.json"} or any(p.is_symlink() for p in members.values()):
        raise ValueError("file_inventory_mismatch")
    entries = manifest["files"]
    if ({item["path"] for item in entries} != expected or len(entries) != len(expected) or
            any(sha(folder / item["path"]) != item["sha256"] for item in entries)):
        raise ValueError("manifest_file_hash_mismatch")
    if (manifest["capability"] != "selected_frozen_display_values_only" or
            manifest["scalar_cells"] != 320 or manifest["object_ids"] != list(COUNTS)):
        raise ValueError("manifest_contract_mismatch")
    if version == 2:
        scopes = manifest.get("license_scopes")
        if scopes != {"CC-BY-4.0": sorted((expected - {"code/verify_display.py", "LICENSES/CODE-MIT.txt"}) | {"MANIFEST.json"}),
                      "MIT": ["code/verify_display.py"]}:
            raise ValueError("license_scope_mismatch")
        data_notice = (folder / "LICENSES/DATA-CC-BY-4.0.md").read_text(encoding="utf-8")
        code_notice = (folder / "LICENSES/CODE-MIT.txt").read_text(encoding="utf-8")
        if ("Chien-Wei Hu" not in data_notice or "Hewijin Christine Jiau" not in data_notice or
                "creativecommons.org/licenses/by/4.0/legalcode" not in data_notice or
                "Copyright (c) 2026 Chien-Wei Hu and Hewijin Christine Jiau" not in code_notice or
                "Permission is hereby granted" not in code_notice or
                "THE SOFTWARE IS PROVIDED \"AS IS\"" not in code_notice):
            raise ValueError("license_notice_mismatch")
    payload = read(folder / "data/display_cells.json")
    if (set(payload) != {"schema_version", "capability", "objects"} or
            payload["schema_version"] != 1 or payload["capability"] != manifest["capability"] or
            [obj["id"] for obj in payload["objects"]] != list(COUNTS)):
        raise ValueError("payload_contract_mismatch")
    for obj in payload["objects"]:
        if set(obj) != {"id", "paper_label", "cells"} or len(obj["cells"]) != COUNTS[obj["id"]]:
            raise ValueError("object_shape_mismatch")
        slots = set()
        for cell in obj["cells"]:
            if set(cell) != {"slot", "context", "arm", "quantity", "value"}:
                raise ValueError("cell_shape_mismatch")
            if cell["slot"] in slots or cell["quantity"] in FORBIDDEN:
                raise ValueError("duplicate_slot_or_count")
            slots.add(cell["slot"])
            if (not isinstance(cell["context"], dict) or
                    FORBIDDEN_KEYS.intersection(cell["context"])):
                raise ValueError("forbidden_context_key")
            value = cell["value"]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("invalid_numeric_value")
    schema = read(folder / "data/field_schema.json")
    if (schema["schema_version"] != 1 or schema["payload_top_level_fields"] != sorted(payload) or
            schema["cell_fields"] != ["arm", "context", "quantity", "slot", "value"] or
            schema["objects"] != summary(payload)):
        raise ValueError("field_schema_mismatch")
    paper_map = read(folder / "PAPER_OBJECT_MAP.json")
    if (paper_map["schema_version"] != 1 or
            [{"id": obj["id"], "paper_label": obj["paper_label"],
              "scalar_cells": obj["scalar_cells"]} for obj in paper_map["objects"]] !=
            [{"id": obj["id"], "paper_label": obj["paper_label"],
              "scalar_cells": len(obj["cells"])} for obj in payload["objects"]]):
        raise ValueError("paper_map_mismatch")
    return {"files_plus_manifest": len(expected) + 1, "objects": len(COUNTS),
            "scalar_cells": sum(COUNTS.values()), "file_hashes_verified": True,
            "frozen_display_structure_verified": True,
            "real_input_to_estimate_reproduction": False,
            "disclosure_safety_established": False,
            "publication_approval": False}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 -I code/verify_display.py PACKAGE_ROOT")
    print(json.dumps(verify(Path(sys.argv[1])), indent=2))
