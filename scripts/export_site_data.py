#!/usr/bin/env python
"""Export the full site dataset (benchmarks, code, runs, harness internals).

Usage: .venv/bin/python scripts/export_site_data.py <output.json>
"""
import json, sys, glob
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import yaml, frontmatter

MAX = 14000
TEXT_EXT = {'.md','.txt','.py','.sh','.json','.yaml','.yml','.csv','.svg','.js','.html','.xml','.ts','.tsx','.jsx'}
ROOT = Path(__file__).resolve().parents[1]
SOURCES = json.loads((ROOT/'skills/SOURCES.json').read_text()) if (ROOT/'skills/SOURCES.json').is_file() else {}


def file_entry(p, base):
    rel = str(p.relative_to(base)); size = p.stat().st_size
    e = {"path": rel, "bytes": size}
    if p.suffix.lower() in TEXT_EXT and size < 200_000:
        try:
            t = p.read_text(encoding='utf-8')
            e["content"] = t[:MAX] + (f"\n… [truncated, {size} bytes total]" if len(t) > MAX else "")
        except Exception:
            pass
    return e


def main(out_path):
    from skillproof.codex.prompts import CONTRACT, _sandbox_packages
    from skillproof.agent.tools import TOOL_SCHEMAS
    from skillproof.agent.loop import SYSTEM_PREAMBLE, SKILL_BLOCK_TEMPLATE
    from skillproof.judge import _SYSTEM as JUDGE_SYSTEM

    out = {"generated": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
           "skills": {}, "harness": {
        "authoring_contract": CONTRACT.replace('{{','{').replace('}}','}'),
        "sandbox_packages": _sandbox_packages(), "tool_schemas": TOOL_SCHEMAS,
        "agent_system_preamble": SYSTEM_PREAMBLE,
        "skill_injection_template": SKILL_BLOCK_TEMPLATE,
        "judge_system_prompt": JUDGE_SYSTEM,
        "dockerfile": (ROOT/'docker/Dockerfile').read_text(),
        "config_yaml": (ROOT/'skillproof.yaml').read_text(),
        "readme": (ROOT/'README.md').read_text(),
    }}
    for skill_dir in sorted((ROOT/'skills').iterdir()):
        if not (skill_dir/'SKILL.md').is_file():
            continue
        name = skill_dir.name
        post = frontmatter.loads((skill_dir/'SKILL.md').read_text())
        entry = {"description": str(post.metadata.get('description',''))[:400],
                 "source": SOURCES.get(name, {}),
                 "skill_md_excerpt": post.content[:3000], "benchmarks": [], "runs": []}
        bdir = ROOT/'benchmarks'/name
        if bdir.is_dir():
            cj = bdir/'clusters.json'
            if cj.is_file():
                c = json.loads(cj.read_text())
                entry['n_chunks'] = c['n_chunks']; entry['k_selected'] = c['k_selected']
                entry['embedding'] = c.get('embedding_model','')
                entry['clusters'] = [{"id": cl['cluster_id'], "label": cl['label'],
                                      "chunks": len(cl['chunk_ids']),
                                      "selected": cl['cluster_id'] in c['selected_cluster_ids']}
                                     for cl in c['all_clusters']]
            for b in sorted(bdir.glob('bench_*')):
                rec = {"id": b.name, "files": {}}
                if (b/'FAILED.md').exists():
                    rec['status'] = 'failed'; rec['failed_md'] = (b/'FAILED.md').read_text()[:2000]
                elif (b/'benchmark.yaml').is_file():
                    y = yaml.safe_load((b/'benchmark.yaml').read_text())
                    rec.update(status='validated' if y.get('validation',{}).get('reference_passed') else 'in-progress',
                               title=y.get('title',''), capability=y.get('capability',''),
                               difficulty=y.get('difficulty'),
                               attempts=y.get('validation',{}).get('codex_attempts'),
                               authoring=y.get('authoring') or {},
                               spec_yaml=(b/'benchmark.yaml').read_text())
                    for fname in ('README.md','task_prompt.md'):
                        if (b/fname).is_file():
                            rec['files'][fname] = (b/fname).read_text()[:MAX]
                    for sub in ('grader','reference_solution','files'):
                        d = b/sub
                        if d.is_dir():
                            rec['files'][sub] = [file_entry(p, b) for p in sorted(d.rglob('*')) if p.is_file()]
                else:
                    rec['status'] = 'generating'
                entry['benchmarks'].append(rec)
        for run_dir in sorted(glob.glob(str(ROOT/f'results/{name}/*/'))):
            rj = Path(run_dir)/'results.json'
            if not rj.is_file():
                continue
            d = json.loads(rj.read_text())
            run = {"run_id": d['run_id'], "trials": d['config_snapshot']['eval']['trials'],
                   "models": d['config_snapshot']['eval']['models'], "results": []}
            for r in d['results']:
                trials = [{"arm": t['arm'], "trial": t['trial'], "passed": t['passed'],
                           "turns": t['turns_used'], "wall_s": t['wall_seconds'],
                           "tokens_in": t['tokens_in'], "tokens_out": t['tokens_out'],
                           "cost": t.get('cost_usd'), "stop": t['stop_reason'],
                           "error": t.get('error'),
                           "grader_output": (t.get('grader_output') or '')[:600],
                           "judge_qa": t.get('judge_qa') or [],
                           "skill_files_read": t.get('skill_files_read')}
                          for t in r['trials']]
                run['results'].append({"benchmark": r['benchmark_id'], "model": r['model'],
                                       "with": r['with_skill_pass_rate'],
                                       "without": r['without_skill_pass_rate'],
                                       "uplift": r['uplift'], "trials": trials})
            entry['runs'].append(run)
        out['skills'][name] = entry
    Path(out_path).write_text(json.dumps(out))
    print(f"wrote {out_path}: {len(json.dumps(out))//1024}KB, "
          f"{len(out['skills'])} skills, {sum(len(s['runs']) for s in out['skills'].values())} runs")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'site/site_data_full.json')
