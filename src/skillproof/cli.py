"""skillproof CLI: cluster → generate → run → report (or `all`)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Automatic benchmark generation and evaluation for Agent Skills.")
console = Console()

ConfigOpt = typer.Option("skillproof.yaml", "--config", "-c", help="Path to config YAML")


def _load(config_path: str):
    from .config import Config

    return Config.load(config_path)


@app.command()
def cluster(
    skill_path: Path = typer.Argument(..., help="Path to a skill folder (contains SKILL.md)"),
    k: int = typer.Option(None, "--k", help="Number of benchmarks (dissimilar clusters)"),
    config: str = ConfigOpt,
):
    """Chunk a skill, embed, cluster, and select the most dissimilar clusters."""
    from .bench import store
    from .chunking import chunk_skill
    from .clustering import run_clustering
    from .skill_loader import load_skill

    cfg = _load(config)
    if k:
        cfg.clustering.k_benchmarks = k
    skill = load_skill(skill_path)
    chunks = chunk_skill(skill, cfg.clustering)
    console.print(f"[bold]{skill.name}[/bold]: {len(chunks)} chunks")
    report = run_clustering(skill, chunks, cfg)
    path = store.save_cluster_report(report, cfg.benchmarks_dir)

    table = Table(title=f"Selected clusters ({report.k_selected})")
    table.add_column("id"); table.add_column("label"); table.add_column("chunks")
    table.add_column("dissimilarity")
    for c in report.selected_clusters():
        table.add_row(str(c.cluster_id), c.label, str(len(c.chunk_ids)),
                      f"{c.centroid_distance_score:.3f}")
    console.print(table)
    console.print(f"wrote {path}")


@app.command()
def generate(
    skill_path: Path = typer.Argument(...),
    only: str = typer.Option(None, "--only", help="Regenerate a single benchmark id"),
    force: bool = typer.Option(False, "--force", help="Re-author even validated benchmarks"),
    config: str = ConfigOpt,
):
    """Author one validated benchmark per selected cluster (skips already-validated)."""
    from .bench import store
    from .bench.spec import BenchmarkSpec
    from .codex.harness import check_codex, generate_benchmark
    from .skill_loader import load_skill

    cfg = _load(config)
    check_codex(cfg)
    skill = load_skill(skill_path)
    report = store.load_cluster_report(cfg.benchmarks_dir, skill.name)

    ok = failed = skipped = 0
    for i, cl in enumerate(report.selected_clusters(), start=1):
        bench_id = store.bench_dir_name(i, cl.label)
        if only and bench_id != only:
            continue
        bench_dir = store.skill_bench_dir(cfg.benchmarks_dir, skill.name) / bench_id
        if not force and not only and (bench_dir / "benchmark.yaml").is_file():
            try:
                if BenchmarkSpec.load(bench_dir).is_validated:
                    console.print(f"  [dim]{bench_id} already validated — skipping[/dim]")
                    skipped += 1
                    continue
            except Exception:
                pass  # unparseable spec -> re-author
        _, success = generate_benchmark(skill, report, cl, i, cfg)
        ok += success
        failed += not success
    console.print(f"[bold]done:[/bold] {ok} validated, {failed} failed, {skipped} skipped")
    if failed and not ok and not skipped:
        raise typer.Exit(1)


@app.command()
def validate(
    bench_dir: Path = typer.Argument(..., help="Path to a single benchmark directory"),
    config: str = ConfigOpt,
):
    """Re-run validation (structure, reference passes, baseline fails) on a benchmark."""
    from .codex.validate import validate_benchmark

    cfg = _load(config)
    result = validate_benchmark(bench_dir, cfg.sandbox, judge_cfg=cfg.judge)
    if result.ok:
        console.print("[green]VALID[/green] — reference passes, baseline fails")
    else:
        console.print(f"[red]INVALID[/red]\n{result.report()}")
        raise typer.Exit(1)


@app.command()
def run(
    skill_path: Path = typer.Argument(...),
    models: str = typer.Option(None, "--models", help="Comma-separated OpenRouter model ids"),
    trials: int = typer.Option(None, "--trials"),
    resume: str = typer.Option(None, "--resume", help="Existing run id to resume"),
    parallel: int = typer.Option(None, "--parallel"),
    only: str = typer.Option(None, "--only", help="Comma-separated benchmark ids"),
    config: str = ConfigOpt,
):
    """Evaluate models on the skill's benchmarks (with vs without the skill)."""
    from .eval.runner import run_eval
    from .report import markdown_report
    from .skill_loader import load_skill

    cfg = _load(config)
    if models:
        cfg.eval.models = [m.strip() for m in models.split(",") if m.strip()]
    if trials:
        cfg.eval.trials = trials
    if parallel:
        cfg.eval.parallel = parallel
    skill = load_skill(skill_path)
    results, run_dir = run_eval(
        skill, cfg, run_id=resume,
        only_benchmarks=[b.strip() for b in only.split(",")] if only else None,
    )
    path = markdown_report.write(results, run_dir)
    console.print(f"\n[bold green]report:[/bold green] {path}")


@app.command()
def report(
    run_dir: Path = typer.Argument(..., help="results/<skill>/<run_id> directory"),
):
    """Regenerate report.md from an existing results.json."""
    from .eval.uplift import aggregate
    from .models import RunResults
    from .report import markdown_report

    results = RunResults.model_validate_json((run_dir / "results.json").read_text())
    # Re-aggregate from raw trials so reports pick up newly added metrics.
    trials = [t for r in results.results for t in r.trials]
    error_policy = results.config_snapshot.get("eval", {}).get("error_policy", "fail")
    results.results = aggregate(trials, error_policy)
    path = markdown_report.write(results, run_dir)
    console.print(f"wrote {path}")


@app.command("all")
def run_all(
    skill_path: Path = typer.Argument(...),
    config: str = ConfigOpt,
):
    """Full pipeline: cluster → generate → run → report."""
    cluster(skill_path=skill_path, k=None, config=config)
    generate(skill_path=skill_path, only=None, config=config)
    run(skill_path=skill_path, models=None, trials=None, resume=None,
        parallel=None, only=None, config=config)


@app.command("build-image")
def build_image(
    config: str = ConfigOpt,
    dockerfile_dir: Path = typer.Option(Path("docker"), "--dockerfile-dir"),
):
    """Build the sandbox Docker image."""
    cfg = _load(config)
    # --provenance/--sbom off: attestation manifests can leave the tag unresolvable
    # by `docker inspect`/the SDK under the containerd image store.
    cmd = ["docker", "build", "--provenance=false", "--sbom=false",
           "-t", cfg.sandbox.image, str(dockerfile_dir)]
    console.print(f"$ {' '.join(cmd)}")
    raise typer.Exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    app()
