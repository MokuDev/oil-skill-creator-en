#!/usr/bin/env python3
"""Generate a cross-platform local review page that hides candidate identity by default."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .evaluation_common import load_json
except ImportError:
    from evaluation_common import load_json


TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".html", ".css", ".py"}
IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}
MAX_PREVIEW_CHARS = 12000
MAX_EMBED_BYTES = 8 * 1024 * 1024


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{color-scheme:light dark;font-family:ui-sans-serif,system-ui,sans-serif}body{max-width:1120px;margin:0 auto;padding:32px 20px;line-height:1.55}h1,h2,h3{line-height:1.2}.muted{opacity:.68}.eval{border-top:1px solid #8886;padding-top:24px;margin-top:32px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}.card{border:1px solid #8886;border-radius:12px;padding:16px}.badge{display:block;font-weight:700;margin-top:12px}img{display:block;max-width:100%;height:auto;border-radius:8px}pre{white-space:pre-wrap;overflow:auto;background:#8881;padding:12px;border-radius:8px}textarea{width:100%;min-height:100px;box-sizing:border-box}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #8885;padding:8px;text-align:left}button{padding:10px 16px;border-radius:8px;border:1px solid #8888;cursor:pointer}.pass{color:#198754}.fail{color:#c43d3d}</style>
</head>
<body>
<h1 id="title"></h1>
<p class="muted">Candidate identities are hidden by default. Review the outputs and leave feedback before looking at the aggregate; do not judge quality from version names.</p>
<div id="content"></div>
<h2>Comparison results</h2>
<div id="benchmark"></div>
<p><button id="export" type="button">Export feedback.json</button> <span id="status" class="muted" aria-live="polite"></span></p>
<script id="review-data" type="application/json">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('review-data').textContent);
document.getElementById('title').textContent=data.title;
const storageKey='oil-skill-review:'+data.title;
let drafts={};let storageAvailable=true;try{drafts=JSON.parse(localStorage.getItem(storageKey)||'{}')}catch(_error){drafts={};storageAvailable=false}
const content=document.getElementById('content');
for(const item of data.evals){
  const section=document.createElement('section'); section.className='eval';
  const h=document.createElement('h2'); h.textContent=item.name; section.appendChild(h);
  const prompt=document.createElement('pre'); prompt.textContent=item.prompt; section.appendChild(prompt);
  const grid=document.createElement('div'); grid.className='grid';
  for(const run of item.runs){
    const card=document.createElement('article'); card.className='card';
    const title=document.createElement('h3'); title.textContent=run.candidate+' · run '+run.repetition; card.appendChild(title);
    if(run.files.length===0){const p=document.createElement('p');p.className='muted';p.textContent='No output files';card.appendChild(p)}
    for(const file of run.files){
      const label=document.createElement('p'); label.className='badge'; label.textContent=file.name+' · '+file.size+' bytes'; card.appendChild(label);
      if(file.data_url!==null){const img=document.createElement('img');img.src=file.data_url;img.alt=file.name;card.appendChild(img)}
      if(file.preview!==null){const pre=document.createElement('pre');pre.textContent=file.preview;card.appendChild(pre)}
    }
    if(run.grading.length){
      const ul=document.createElement('ul');
      for(const grade of run.grading){const li=document.createElement('li');li.className=grade.passed?'pass':'fail';li.textContent=(grade.passed?'pass: ':'fail: ')+grade.text+' — '+grade.evidence;ul.appendChild(li)}
      card.appendChild(ul);
    }
    const label=document.createElement('label'); label.className='badge'; label.htmlFor=run.candidate_id; label.textContent='Feedback'; card.appendChild(label);
    const area=document.createElement('textarea'); area.id=run.candidate_id; area.dataset.candidateId=run.candidate_id; area.placeholder='Record reusable feedback; leave empty if there are no issues'; area.value=drafts[run.candidate_id]||'';
    area.addEventListener('input',()=>{drafts[run.candidate_id]=area.value;try{localStorage.setItem(storageKey,JSON.stringify(drafts))}catch(_error){storageAvailable=false}}); card.appendChild(area);
    grid.appendChild(card);
  }
  section.appendChild(grid); content.appendChild(section);
}
const bench=document.getElementById('benchmark');
if(data.benchmark.length){
  const table=document.createElement('table');
  table.innerHTML='<thead><tr><th>Candidate</th><th>Runs</th><th>Pass rate</th><th>Seconds</th><th>Tokens</th></tr></thead>';
  const body=document.createElement('tbody');
  for(const row of data.benchmark){const tr=document.createElement('tr');for(const value of [row.candidate,row.runs,row.pass_rate,row.duration,row.tokens]){const td=document.createElement('td');td.textContent=value;tr.appendChild(td)}body.appendChild(tr)}
  table.appendChild(body);bench.appendChild(table);
}else{bench.textContent='No comparison report generated yet';bench.className='muted'}
document.getElementById('export').addEventListener('click',()=>{
  const reviews=[...document.querySelectorAll('textarea')].map(area=>({candidate_id:area.dataset.candidateId,feedback:area.value,timestamp:new Date().toISOString()}));
  const blob=new Blob([JSON.stringify({status:'complete',reviews},null,2)+'\\n'],{type:'application/json'});
  const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='feedback.json';link.click();URL.revokeObjectURL(link.href);
  document.getElementById('status').textContent=storageAvailable?'exported; local drafts are preserved':'exported';
});
</script>
</body>
</html>
"""


def _metric(value: object, percent: bool = False) -> str:
    if not isinstance(value, dict) or value.get("mean") is None:
        return "n/a"
    mean = float(value["mean"])
    stddev = float(value.get("stddev") or 0)
    if percent:
        return f"{mean * 100:.1f}% +/- {stddev * 100:.1f}%"
    return f"{mean:.2f} +/- {stddev:.2f}"


def _candidate_map(configurations: list[str], iteration: object, reveal: bool) -> dict[str, str]:
    if reveal:
        return {name: name for name in configurations}
    ordered = sorted(
        configurations,
        key=lambda name: hashlib.sha256(f"{iteration}:{name}".encode()).hexdigest(),
    )
    return {name: f"Candidate {chr(65 + index)}" for index, name in enumerate(ordered)}


def _output_files(outputs: Path) -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    if not outputs.is_dir():
        return files
    for path in sorted(outputs.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink() or not path.is_file():
            continue
        preview: str | None = None
        data_url: str | None = None
        if path.suffix.lower() in TEXT_SUFFIXES:
            try:
                text = path.read_text(encoding="utf-8")
                preview = text[:MAX_PREVIEW_CHARS]
                if len(text) > MAX_PREVIEW_CHARS:
                    preview += "\n...preview truncated..."
            except UnicodeDecodeError:
                preview = None
        mime_type = IMAGE_MIME_TYPES.get(path.suffix.lower())
        if mime_type and path.stat().st_size <= MAX_EMBED_BYTES:
            data_url = (
                f"data:{mime_type};base64,"
                + base64.b64encode(path.read_bytes()).decode("ascii")
            )
        files.append(
            {
                "name": path.relative_to(outputs).as_posix(),
                "size": path.stat().st_size,
                "preview": preview,
                "data_url": data_url,
            }
        )
    return files


def build_review_data(root: Path, reveal: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = load_json(root / "run_plan.json")
    if not isinstance(plan, dict) or not isinstance(plan.get("runs"), list):
        raise ValueError("run_plan.json is missing the runs array")
    configurations = plan.get("configurations")
    if not isinstance(configurations, list) or not all(
        isinstance(value, str) for value in configurations
    ):
        raise ValueError("run_plan.json is missing configurations")
    labels = _candidate_map(configurations, plan.get("iteration"), reveal)
    grouped: dict[str, dict[str, Any]] = {}
    manifest_runs: dict[str, str] = {}
    for run in plan["runs"]:
        if not isinstance(run, dict):
            raise ValueError("each run_plan.runs entry must be an object")
        run_dir = Path(str(run.get("run_dir", ""))).expanduser().resolve()
        try:
            run_dir.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"run_dir escapes the iteration directory: {run_dir}") from exc
        run_id = str(run.get("run_id"))
        candidate_id = "review-" + hashlib.sha256(run_id.encode()).hexdigest()[:12]
        manifest_runs[candidate_id] = run_id
        grading_path = run_dir / "grading.json"
        grading: list[dict[str, Any]] = []
        if grading_path.is_file():
            grading_data = load_json(grading_path)
            if isinstance(grading_data, dict) and isinstance(
                grading_data.get("expectations"), list
            ):
                grading = grading_data["expectations"]
        eval_name = str(run.get("eval_name"))
        item = grouped.setdefault(
            eval_name,
            {"name": eval_name, "prompt": str(run.get("prompt", "")), "runs": []},
        )
        item["runs"].append(
            {
                "candidate_id": candidate_id,
                "candidate": labels[str(run.get("configuration"))],
                "repetition": run.get("repetition"),
                "files": _output_files(run_dir / "outputs"),
                "grading": grading,
            }
        )

    benchmark_rows: list[dict[str, object]] = []
    benchmark_path = root / "benchmark.json"
    if benchmark_path.is_file():
        benchmark = load_json(benchmark_path)
        summaries = benchmark.get("configurations", {}) if isinstance(benchmark, dict) else {}
        if isinstance(summaries, dict):
            for configuration in configurations:
                summary = summaries.get(configuration, {})
                if not isinstance(summary, dict):
                    continue
                benchmark_rows.append(
                    {
                        "candidate": labels[configuration],
                        "runs": summary.get("runs", 0),
                        "pass_rate": _metric(summary.get("pass_rate"), percent=True),
                        "duration": _metric(summary.get("duration_seconds")),
                        "tokens": _metric(summary.get("total_tokens")),
                    }
                )

    data = {
        "title": f"{plan.get('skill_name', 'Skill')} · iteration-{plan.get('iteration')}",
        "evals": list(grouped.values()),
        "benchmark": benchmark_rows,
    }
    manifest = {
        "schema_version": 1,
        "blind": not reveal,
        "candidates": labels,
        "runs": manifest_runs,
    }
    return data, manifest


def generate_review(
    iteration_path: str | Path,
    output: str | Path | None = None,
    reveal: bool = False,
    replace: bool = False,
) -> tuple[Path, Path]:
    root = Path(iteration_path).expanduser().resolve()
    output_path = (
        Path(output).expanduser().resolve() if output is not None else root / "review.html"
    )
    manifest_path = root / "review_manifest.json"
    if not replace and (output_path.exists() or manifest_path.exists()):
        raise FileExistsError("review output already exists; pass --replace to overwrite explicitly")
    data, manifest = build_review_data(root, reveal=reveal)
    encoded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(
        ">", "\\u003e"
    )
    title = str(data["title"]).replace("&", "&amp;").replace("<", "&lt;").replace(
        ">", "&gt;"
    )
    html = HTML_TEMPLATE.replace("__TITLE__", title).replace("__DATA__", encoded)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8", newline="\n")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output_path, manifest_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="generate a local Skill review page that hides version identity by default")
    parser.add_argument("iteration_path", help="iteration-N directory")
    parser.add_argument("--output", help="HTML output path, default is iteration/review.html")
    parser.add_argument("--reveal", action="store_true", help="show the real configuration names in the page")
    parser.add_argument("--replace", action="store_true", help="explicitly overwrite an existing review output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output, manifest = generate_review(
            args.iteration_path,
            output=args.output,
            reveal=args.reveal,
            replace=args.replace,
        )
    except (ValueError, FileExistsError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"review page created: {output}")
    print(f"candidate mapping: {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
