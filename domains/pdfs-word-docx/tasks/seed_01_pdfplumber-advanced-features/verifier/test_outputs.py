"""Deterministic checks for /workspace/answer.txt and /workspace/matched_codes.txt.

/workspace/tags.pdf places 24 four-digit numeric tags at fixed, known (x, y)
positions on the page (plus one decoy four-digit number, 4413, embedded in a
sentence of header text -- not a standalone scanned tag). Exactly five of the
24 tags have a text-origin point that falls inside the target region
x in [200, 420], y in [420, 620] (PDF points, origin at the bottom-left of the
page): {2160, 3069, 4689, 5299, 8390}, which sum to 23607. Plain sequential
text extraction never exposes per-item coordinates, so getting this exact
sum/set requires actually reading each tag's placement position and testing
it against the region -- not just dumping or regexing the page text.
"""

from pathlib import Path

import pytest

ANSWER_PATH = Path("/workspace/answer.txt")
MATCHED_PATH = Path("/workspace/matched_codes.txt")

EXPECTED_MATCHED = {2160, 3069, 4689, 5299, 8390}
EXPECTED_SUM = sum(EXPECTED_MATCHED)


def test_answer_file_exists_and_is_a_bare_integer():
    assert ANSWER_PATH.exists(), f"{ANSWER_PATH} was not created"
    content = ANSWER_PATH.read_text().strip()
    assert content.isdigit(), f"expected a bare non-negative integer, got {content!r}"


def test_answer_value_is_correct_sum():
    value = int(ANSWER_PATH.read_text().strip())
    assert value == EXPECTED_SUM, (
        f"expected sum of tags inside the target region to be {EXPECTED_SUM}, got {value}"
    )


def test_matched_codes_file_exists_and_parses_as_integers():
    assert MATCHED_PATH.exists(), f"{MATCHED_PATH} was not created"
    lines = [ln.strip() for ln in MATCHED_PATH.read_text().splitlines() if ln.strip()]
    assert len(lines) > 0, "matched_codes.txt is empty"
    for ln in lines:
        assert ln.isdigit(), f"expected one bare integer per line, got {ln!r}"


def test_matched_codes_set_matches_expected_region_membership():
    lines = [ln.strip() for ln in MATCHED_PATH.read_text().splitlines() if ln.strip()]
    matched = {int(ln) for ln in lines}
    assert matched == EXPECTED_MATCHED, (
        f"expected exactly the tags located inside the target region {EXPECTED_MATCHED}, "
        f"got {matched}"
    )


def test_matched_codes_sum_is_internally_consistent_with_answer():
    lines = [ln.strip() for ln in MATCHED_PATH.read_text().splitlines() if ln.strip()]
    matched_sum = sum(int(ln) for ln in lines)
    answer_value = int(ANSWER_PATH.read_text().strip())
    assert matched_sum == answer_value, (
        "answer.txt must equal the sum of the codes listed in matched_codes.txt"
    )


def test_decoy_number_outside_the_region_is_excluded():
    lines = [ln.strip() for ln in MATCHED_PATH.read_text().splitlines() if ln.strip()]
    matched = {int(ln) for ln in lines}
    assert 4413 not in matched, (
        "4413 is a decoy number in the page header text, not a scanned tag inside the region"
    )
