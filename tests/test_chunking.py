from pathlib import Path

from skillproof.chunking import chunk_markdown, chunk_skill
from skillproof.config import ClusteringConfig
from skillproof.skill_loader import load_skill

FIXTURE = Path(__file__).parent / "fixtures" / "sample_skill"


def test_load_skill():
    skill = load_skill(FIXTURE)
    assert skill.name == "csv-wrangler"
    assert "CSV" in skill.description
    assert "references/guide.md" in skill.reference_files
    assert "scripts/helper.py" in skill.script_files
    assert "Loading messy CSVs" in skill.skill_md


def test_chunk_markdown_heading_paths():
    text = "# A\n\nintro\n\n## B\n\nbody b\n\n## C\n\nbody c\n\n### C1\n\ndeep"
    chunks = chunk_markdown(text, "SKILL.md")
    paths = [c.heading_path for c in chunks]
    assert ["A"] in paths
    assert ["A", "B"] in paths
    assert ["A", "C", "C1"] in paths


def test_chunk_ids_unique_and_deterministic():
    skill = load_skill(FIXTURE)
    cfg = ClusteringConfig(min_chunk_tokens=1)  # disable merging for id checks
    a = chunk_skill(skill, cfg)
    b = chunk_skill(skill, cfg)
    ids_a = [c.id for c in a]
    assert ids_a == [c.id for c in b]
    assert len(ids_a) == len(set(ids_a))
    assert all(c.id.split("#")[0] in ("SKILL.md", "references/guide.md") for c in a)


def test_headings_in_code_fences_ignored():
    text = "# Real\n\n```bash\n# not a heading\necho hi\n```\n\nmore"
    chunks = chunk_markdown(text, "SKILL.md")
    assert len(chunks) == 1
    assert "# not a heading" in chunks[0].text


def test_small_chunks_merged():
    skill = load_skill(FIXTURE)
    merged = chunk_skill(skill, ClusteringConfig(min_chunk_tokens=10_000))
    # aggressive merging collapses each file into one chunk
    files = {c.source_file for c in merged}
    assert len(merged) == len(files)


def test_oversized_chunks_split():
    body = "\n\n".join(f"paragraph {i} " + "x" * 200 for i in range(40))
    chunks = chunk_markdown(f"# Big\n\n{body}", "SKILL.md")
    from skillproof.chunking import _normalize_sizes

    out = _normalize_sizes(chunks, ClusteringConfig(min_chunk_tokens=1, max_chunk_tokens=500))
    assert len(out) > 1
    assert all(c.token_estimate <= 600 for c in out)  # small slack over budget
