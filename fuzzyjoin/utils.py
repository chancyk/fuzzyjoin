import os
import csv
import sys
import inspect
import importlib
from typing import Iterator, Dict, List, Any, Optional

import colorama  # type: ignore

colorama.init(autoreset=True)


def iter_csv_as_records(filepath: str) -> Iterator[Dict[str, str]]:
    """Yield each line of `filepath` as a dict using
    the first line as the keys.
    """
    with open(filepath, "r") as f:
        csv_reader = csv.reader(f)
        header = next(csv_reader)
        for row in csv_reader:
            yield dict(zip(header, row))


def load_csv_as_records(filepath: str) -> List[Dict[str, str]]:
    """Return a list of dicts using the first line as a
    header for the dictionary keys.
    """
    records = list(iter_csv_as_records(filepath))
    return records


def prompt_if_exists(filepath: str):
    """Prompt the user if `filepath` already exists."""
    if os.path.exists(filepath):
        resp = input(f"[WARN] <{filepath}> already exists. Overwrite it? [y|N]: ")
        if resp not in "yY":
            raise Exception("User aborted.")


def append_to_stack(stack: List[Any], item: Any, size: int) -> List[Any]:
    if len(stack) > 0 and len(stack) < size:
        stack.append(item)
    elif len(stack) > 0:
        stack.pop(0)
        stack.append(item)
    else:
        stack.append(item)

    return stack


def color_red(text: str) -> str:
    return colorama.Fore.RED + text + colorama.Fore.RESET


def scan_for_token(
    token: str, filepath: str, context_lines: int
) -> Optional[List[str]]:
    prev_context = []  # type: List[str]
    next_context = []  # type: List[str]
    with open(filepath, "r") as file:
        for line in file:
            if token in line:
                parts = line.split(token, 1)
                token_line = "".join([parts[0], color_red(token), parts[1]])
                # If we found the token, return the next `size`
                # lines after it.
                for i, line_after in enumerate(file, 1):
                    next_context.append(line_after)
                    if i >= context_lines:
                        break

                return prev_context + [token_line] + next_context
            else:
                # Keep the previous `size` lines.
                append_to_stack(stack=prev_context, item=line, size=context_lines)

    return None


def import_function(fq_module_path: str):
    sys.path.insert(0, "")
    module_path, function_name = fq_module_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    function = getattr(module, function_name)
    sys.path.pop(0)
    return function


def yield_chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def bump_version(version_text, part):
    if part not in ('major', 'minor', 'patch'):
        raise Exception("part must be one of: major, minor, patch")

    p_major, p_minor, p_patch = [int(x) for x in version_text.split('.')]
    if part == 'major':
        p_major += 1
        p_minor = 0
        p_patch = 0
    elif part == 'minor':
        p_minor += 1
        p_patch = 0
    elif part == 'patch':
        p_patch += 1
    else:
        raise Exception("Invalid part. Must be one of: major, minor, patch")

    new_version = f'{p_major}.{p_minor}.{p_patch}'
    return new_version


def current_frame():
    frame = inspect.currentframe().f_back
    return frame


def current_function():
    code = inspect.currentframe().f_back.f_code
    filename = os.path.basename(code.co_filename)
    lineno = code.co_firstlineno
    function_name = code.co_name
    fq_name = f'{filename}::{lineno}::{function_name}'
    return fq_name
