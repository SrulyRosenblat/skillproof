import json
import os
import re
import sys

WORKDIR = os.environ.get("BENCH_WORKDIR", "/workspace")
COPY_PATH = os.path.join(WORKDIR, "ui_copy.json")

REQUIRED_KEYS = {
    "archive_action": ["button_label", "confirmation_message"],
    "remove_member_action": ["button_label", "confirmation_message"],
    "upload_error": ["message"],
    "empty_folder_state": ["heading", "body"],
}

# Internal/implementation terms from system_notes.md / limits.json that should never
# leak into text a customer sees. Short/ambiguous tokens are matched on word
# boundaries so legitimate words (e.g. "megabytes") aren't falsely flagged.
BANNED_WORD_BOUNDARY = [
    "endpoint", "webhook", "cron", "backend", "schema", "payload", "config",
    "database", "query", "byte", "bytes", "api", "json", "null", "boolean",
    "row", "server",
]
BANNED_SUBSTRING = [
    "sync_group", "sync-group", "syncgroup", "soft-delete", "soft delete",
    "revoke_membership", "max_upload_bytes", "314572800",
]

BANNED_APOLOGY = [
    "sorry", "apolog", "oops", "unfortunately", "something went wrong",
    "an error occurred", "error occurred",
]

GENERIC_BUTTON_LABELS = {"submit", "ok", "okay", "click here", "yes", "confirm"}

ACTIONABLE_FIX_WORDS = ["smaller", "compress", "reduce", "split", "shrink"]


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def load_copy():
    if not os.path.isfile(COPY_PATH):
        fail("ui_copy.json not found in /workspace")
    try:
        with open(COPY_PATH) as f:
            return json.load(f)
    except Exception as e:
        fail(f"ui_copy.json is not valid JSON: {e}")


def all_strings(data):
    out = []

    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(data)
    return out


def verb_stem(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if len(w) > 4 and w.endswith("e"):
        return w[:-1]
    return w


def check_structure(data):
    errors = []
    if not isinstance(data, dict):
        return ["ui_copy.json must contain a JSON object"]
    for key, subkeys in REQUIRED_KEYS.items():
        if key not in data or not isinstance(data[key], dict):
            errors.append(f"missing or malformed key: {key}")
            continue
        for sk in subkeys:
            val = data[key].get(sk)
            if not isinstance(val, str) or not val.strip():
                errors.append(f"missing or empty field: {key}.{sk}")
    return errors


def check_content(data):
    errors = []
    strs = all_strings(data)
    joined = "\n".join(strs).lower()

    for term in BANNED_WORD_BOUNDARY:
        if re.search(r"\b" + re.escape(term) + r"\b", joined):
            errors.append(f"internal/system jargon leaked into user-facing copy: '{term}'")

    for term in BANNED_SUBSTRING:
        if term in joined:
            errors.append(f"internal/system jargon leaked into user-facing copy: '{term}'")

    for term in BANNED_APOLOGY:
        if term in joined:
            errors.append(f"apologetic/vague filler language found: '{term}'")

    for key in ["archive_action", "remove_member_action"]:
        label = data[key]["button_label"].strip().lower().rstrip("!.")
        if label in GENERIC_BUTTON_LABELS:
            errors.append(f"{key}.button_label is a generic, non-descriptive label: '{label}'")

        words = re.findall(r"[a-z]+", label)
        first_word = words[0] if words else ""
        stem = verb_stem(first_word)
        confirmation = data[key]["confirmation_message"].lower()
        if not stem or stem not in confirmation:
            errors.append(
                f"{key}: confirmation_message doesn't clearly refer back to the same "
                f"action named in button_label ('{first_word}')"
            )

    upload_msg = data["upload_error"]["message"].lower()
    if "300" not in upload_msg or ("mb" not in upload_msg and "megabyte" not in upload_msg):
        errors.append(
            "upload_error.message doesn't state the actual size limit in "
            "human-readable form (300 MB)"
        )
    if not any(w in upload_msg for w in ACTIONABLE_FIX_WORDS):
        errors.append(
            "upload_error.message doesn't tell the person a concrete way to fix the problem"
        )

    empty_text = (
        data["empty_folder_state"]["heading"] + " " + data["empty_folder_state"]["body"]
    ).lower()
    if "upload" not in empty_text:
        errors.append("empty_folder_state doesn't invite the person to upload a file")

    return errors


def build_questions(data):
    return {
        "questions": [
            {
                "id": "q1",
                "question": (
                    "In the JSON below, do BOTH action pairs (archive_action and "
                    "remove_member_action) show a button_label and a confirmation_message "
                    "that clearly describe the same user action, so the confirmation reads "
                    "as the natural result of pressing that specific button rather than a "
                    "generic or mismatched confirmation? Answer yes only if this holds for "
                    "both pairs."
                ),
                "text": json.dumps(
                    {k: data[k] for k in ["archive_action", "remove_member_action"]}, indent=2
                ),
            },
            {
                "id": "q2",
                "question": (
                    "Does this error message clearly state what specifically went wrong "
                    "and clearly tell the person a concrete way to fix it, in a neutral "
                    "tone with no apology and no vague phrasing?"
                ),
                "text": data["upload_error"]["message"],
            },
            {
                "id": "q3",
                "question": (
                    "Does this empty-state text read as an invitation for the person to "
                    "take a specific action to fill the empty space, rather than merely "
                    "stating that nothing is there yet?"
                ),
                "text": data["empty_folder_state"]["heading"]
                + " — "
                + data["empty_folder_state"]["body"],
            },
            {
                "id": "q4",
                "question": (
                    "Below are the on-screen text strings a customer would actually see "
                    "in the product (field names/labels are not shown, only the text "
                    "itself). Is all of it written in plain, conversational language that "
                    "a non-technical small-business customer would understand, with no "
                    "internal engineering or system terminology (such as database "
                    "tables, APIs, config values, or internal code names) anywhere in it?"
                ),
                "text": "\n".join(all_strings(data)),
            },
        ]
    }


def main():
    data = load_copy()

    errors = check_structure(data)
    if errors:
        for e in errors:
            print("FAIL: " + e)
        sys.exit(1)

    errors = check_content(data)
    if errors:
        for e in errors:
            print("FAIL: " + e)
        sys.exit(1)

    judge_dir = os.path.join(WORKDIR, ".judge")
    answers_path = os.path.join(judge_dir, "answers.json")
    questions_path = os.path.join(judge_dir, "questions.json")

    if os.path.isfile(answers_path):
        with open(answers_path) as f:
            answers = json.load(f).get("answers", {})
        required_ids = ["q1", "q2", "q3", "q4"]
        missing_or_no = [qid for qid in required_ids if not answers.get(qid)]
        if missing_or_no:
            print(f"FAIL: judge answered no (or didn't answer) for: {missing_or_no}")
            sys.exit(1)
        print("PASS")
        sys.exit(0)
    else:
        os.makedirs(judge_dir, exist_ok=True)
        with open(questions_path, "w") as f:
            json.dump(build_questions(data), f, indent=2)
        sys.exit(3)


if __name__ == "__main__":
    main()
