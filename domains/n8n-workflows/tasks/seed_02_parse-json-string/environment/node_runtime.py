#!/usr/bin/env python3
"""Reproduces how n8n loads and runs a Code (Python) node's body.

n8n takes the text you write in a Code node and executes it as the body of
an implicit function: your top-level statements run in order, `_input` is
already bound to the incoming batch, and whatever you `return` becomes the
node's output. This script does the same thing to a standalone .py file so
you can try your node body outside of n8n itself.

Usage:
    python3 node_runtime.py <code.py> <input.json> <output.json>
"""
import ast
import json
import sys


class _Input:
    """Minimal stand-in for n8n's `_input` helper."""

    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items

    def first(self):
        return self._items[0]


def _wrap_as_function(source, filename):
    # Parsed via the AST (not text indentation) so multi-line strings and
    # comments in the node body can't be mangled by re-indenting source text.
    tree = ast.parse(source, filename=filename, mode="exec")
    body = tree.body if tree.body else [ast.Pass()]
    func = ast.FunctionDef(
        name="__n8n_node_main",
        args=ast.arguments(
            posonlyargs=[], args=[], vararg=None, kwonlyargs=[],
            kw_defaults=[], kwarg=None, defaults=[],
        ),
        body=body,
        decorator_list=[],
        returns=None,
        type_comment=None,
    )
    module = ast.Module(body=[func], type_ignores=[])
    ast.fix_missing_locations(module)
    return compile(module, filename, "exec")


def run(code_path, input_path, output_path):
    with open(code_path) as f:
        source = f.read()
    with open(input_path) as f:
        items = json.load(f)

    code_obj = _wrap_as_function(source, code_path)

    namespace = {"json": json, "_input": _Input(items)}
    exec(code_obj, namespace)

    result = namespace["__n8n_node_main"]()

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
