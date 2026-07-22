"""Template verifier tests — replace.

Upstream contract: deterministic, outcome-based pytest (4-10 focused assertions;
numeric tolerances where appropriate). Test the produced artifacts, not the process
that made them. No LLM judging — if an outcome can't be asserted deterministically,
the task doesn't belong in this format.
"""


def test_template_placeholder():
    raise AssertionError("template verifier: not a real task")
