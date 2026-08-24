"""Shared data formats and path helpers for the evaluation scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


SAFE_NAME_RE = re.compile(r"[^a-z0-9]+")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {path}:{exc.lineno}:{exc.colno}") from exc


def safe_name(value: object, fallback: str) -> str:
    normalized = SAFE_NAME_RE.sub("-", str(value).strip().lower()).strip("-")
    return normalized[:80] or fallback


def validate_eval_set(
    path: Path,
    expected_skill_name: str | None = None,
    allow_empty: bool = False,
) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError("evals file top level must be an object")
    skill_name = data.get("skill_name")
    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("evals.skill_name must be a non-empty string")
    if expected_skill_name and skill_name != expected_skill_name:
        raise ValueError(
            f"evals.skill_name is {skill_name!r}, which does not match the target Skill {expected_skill_name!r}"
        )
    evals = data.get("evals")
    if not isinstance(evals, list):
        raise ValueError("evals.evals must be an array")
    if not evals and not allow_empty:
        raise ValueError("evals.evals must include at least one test")

    ids: set[str] = set()
    names: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(evals, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"evals[{index}] must be an object")
        allowed_keys = {
            "id",
            "name",
            "prompt",
            "expected_output",
            "files",
            "expectations",
        }
        unexpected = sorted(set(item) - allowed_keys)
        if unexpected:
            raise ValueError(
                f"evals[{index}] contains unsupported fields: {', '.join(unexpected)}"
            )
        eval_id = str(item.get("id", "")).strip()
        if not eval_id or eval_id in ids:
            raise ValueError(f"evals[{index}].id is missing or duplicated")
        ids.add(eval_id)
        raw_name = item.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError(f"evals[{index}].name must be a descriptive string")
        name = safe_name(raw_name, f"eval-{eval_id}")
        if name in names:
            raise ValueError(f"evals[{index}].name collides after normalization: {name}")
        names.add(name)
        prompt = item.get("prompt")
        expected = item.get("expected_output")
        files = item.get("files", [])
        expectations = item.get("expectations", [])
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"evals[{index}].prompt must be a non-empty string")
        if not isinstance(expected, str) or not expected.strip():
            raise ValueError(f"evals[{index}].expected_output must be a non-empty string")
        if not isinstance(files, list) or not all(isinstance(value, str) for value in files):
            raise ValueError(f"evals[{index}].files must be an array of strings")
        if not isinstance(expectations, list) or not all(
            isinstance(value, str) and value.strip() for value in expectations
        ):
            raise ValueError(f"evals[{index}].expectations must be a non-empty array of strings")
        normalized.append(
            {
                "id": eval_id,
                "name": name,
                "prompt": prompt.strip(),
                "expected_output": expected.strip(),
                "files": files,
                "expectations": [value.strip() for value in expectations],
            }
        )
    return {"skill_name": skill_name, "evals": normalized}


def summarize(values: list[float | int]) -> dict[str, float | int | None]:
    if not values:
        return {"mean": None, "stddev": None, "count": 0}
    numeric = [float(value) for value in values]
    return {
        "mean": round(mean(numeric), 4),
        "stddev": round(pstdev(numeric), 4) if len(numeric) > 1 else 0.0,
        "count": len(numeric),
    }
