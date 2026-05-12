#!/usr/bin/env python3
"""SAS Macro Design Document Generator

Parses a .sas macro file and pre-fills a design document template
with extracted metadata (parameters, datasets, macro calls, etc.).

Usage:
    python generate_macro_doc.py path/to/macro.sas [-o output.md]
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import date


def extract_macro_name(code: str) -> str:
    m = re.search(r'%macro\s+(\w+)', code, re.IGNORECASE)
    return m.group(1) if m else 'UNKNOWN'


def extract_parameters(code: str) -> list[dict]:
    """Extract parameters from the %macro statement."""
    m = re.search(r'%macro\s+\w+\s*\(([^;]*?)\)\s*;', code, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    param_block = m.group(1)
    params = []
    for i, chunk in enumerate(re.split(r',(?![^(]*\))', param_block), 1):
        chunk = chunk.strip()
        if not chunk:
            continue
        if '=' in chunk:
            name, default = chunk.split('=', 1)
            name = name.strip()
            default = default.strip() or '(blank)'
        else:
            name = chunk.strip()
            default = '(none — required)'
        params.append({
            'num': i,
            'name': name,
            'required': 'Yes' if default == '(none — required)' else 'No',
            'default': default,
        })
    return params


def extract_input_datasets(code: str) -> list[str]:
    datasets = set()
    for pattern in [
        r'\bset\s+([\w.]+)',
        r'\bmerge\s+([\w.]+)',
        r'\bfrom\s+([\w.]+)',
    ]:
        for m in re.finditer(pattern, code, re.IGNORECASE):
            datasets.add(m.group(1))
    return sorted(datasets)


def extract_output_datasets(code: str) -> list[str]:
    datasets = set()
    for pattern in [
        r'\bdata\s+([\w.]+)',
        r'\bout\s*=\s*([\w.]+)',
    ]:
        for m in re.finditer(pattern, code, re.IGNORECASE):
            ds = m.group(1)
            if ds.upper() not in ('_NULL_', '_WEBOUT'):
                datasets.add(ds)
    return sorted(datasets)


def extract_macro_calls(code: str) -> list[str]:
    calls = set()
    for m in re.finditer(r'%(?!macro|mend|if|else|then|do|end|let|put|global|local|sysfunc|str|upcase|lowcase|substr|scan|eval|sysevalf|nrstr|bquote|quote|nrbquote)([a-zA-Z_]\w*)\s*\(', code, re.IGNORECASE):
        calls.add(m.group(1))
    return sorted(calls)


def extract_validations(code: str) -> list[str]:
    validations = []
    for m in re.finditer(r'%put\s+(ERROR|WARNING)[^;]*;', code, re.IGNORECASE):
        validations.append(m.group(0).strip().rstrip(';'))
    return validations


def extract_header_comments(code: str) -> str:
    m = re.match(r'^\s*(/\*.*?\*/)', code, re.DOTALL)
    return m.group(1) if m else ''


def build_doc(code: str, filepath: str) -> str:
    name = extract_macro_name(code)
    params = extract_parameters(code)
    inputs = extract_input_datasets(code)
    outputs = extract_output_datasets(code)
    macro_calls = extract_macro_calls(code)
    validations = extract_validations(code)
    header = extract_header_comments(code)

    lines = []
    lines.append(f'# Design Document: `%macro {name}`\n')

    # Overview
    lines.append('## 1. Overview\n')
    lines.append('| Field | Value |')
    lines.append('|---|---|')
    lines.append(f'| **Macro Name** | `{name}` |')
    lines.append(f'| **Author** | TBD |')
    lines.append(f'| **Created Date** | TBD |')
    lines.append(f'| **Last Modified** | {date.today().isoformat()} |')
    lines.append(f'| **Version** | 1.0 |')
    lines.append(f'| **Status** | Draft |')
    lines.append(f'| **Program Location** | `{filepath}` |')
    lines.append('')

    # Purpose
    lines.append('## 2. Purpose\n')
    lines.append('_TBD — Add a description of what this macro does._\n')

    # Parameters
    lines.append('## 3. Parameters\n')
    lines.append('| # | Parameter | Required | Type | Default | Description |')
    lines.append('|---|-----------|----------|------|---------|-------------|')
    if params:
        for p in params:
            lines.append(f'| {p["num"]} | `{p["name"]}` | {p["required"]} | TBD | `{p["default"]}` | TBD |')
    else:
        lines.append('| — | _No parameters found_ | — | — | — | — |')
    lines.append('')

    # Input Datasets
    lines.append('## 4. Input Datasets\n')
    lines.append('| # | Dataset | Library | Key Variables | Description |')
    lines.append('|---|---------|---------|---------------|-------------|')
    for i, ds in enumerate(inputs, 1):
        lines.append(f'| {i} | `{ds}` | TBD | TBD | TBD |')
    if not inputs:
        lines.append('| — | _None detected_ | — | — | — |')
    lines.append('')

    # Output Datasets
    lines.append('## 5. Output Datasets\n')
    lines.append('| # | Dataset | Library | Key Variables | Description |')
    lines.append('|---|---------|---------|---------------|-------------|')
    for i, ds in enumerate(outputs, 1):
        lines.append(f'| {i} | `{ds}` | TBD | TBD | TBD |')
    if not outputs:
        lines.append('| — | _None detected_ | — | — | — |')
    lines.append('')

    # Processing Steps
    lines.append('## 6. Processing Steps\n')
    lines.append('1. **Step 1 — Validation** — TBD')
    lines.append('2. **Step 2 — Data Preparation** — TBD')
    lines.append('3. **Step 3 — Core Logic** — TBD')
    lines.append('4. **Step 4 — Output Generation** — TBD')
    lines.append('5. **Step 5 — Cleanup** — TBD\n')

    # Validation
    lines.append('## 7. Validation & Error Handling\n')
    lines.append('| Check | Condition | Action |')
    lines.append('|-------|-----------|--------|')
    if validations:
        for v in validations:
            lines.append(f'| Auto-detected | TBD | `{v}` |')
    else:
        lines.append('| — | _None detected_ | — |')
    lines.append('')

    # Dependencies
    lines.append('## 8. Dependencies\n')
    lines.append(f'- **Other Macros Called:** {(", ".join(f"`%{c}`" for c in macro_calls)) if macro_calls else "None detected"}')
    lines.append('- **External Files:** TBD')
    lines.append('- **SAS Products Required:** Base SAS\n')

    # Example Usage
    lines.append('## 9. Example Usage\n')
    lines.append('```sas')
    param_str = ',\n  '.join(f'{p["name"]} = ' for p in params) if params else ''
    lines.append(f'%{name}(')
    if param_str:
        lines.append(f'  {param_str}')
    lines.append(');')
    lines.append('```\n')

    # Modification History
    lines.append('## 10. Modification History\n')
    lines.append('| Date | Author | Version | Description |')
    lines.append('|------|--------|---------|-------------|')
    lines.append(f'| {date.today().isoformat()} | TBD | 1.0 | Initial creation |')

    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description='Generate a SAS macro design document.')
    parser.add_argument('sasfile', help='Path to the .sas macro file')
    parser.add_argument('-o', '--output', help='Output markdown file path (default: stdout)')
    args = parser.parse_args()

    sas_path = Path(args.sasfile)
    if not sas_path.exists():
        print(f'Error: {sas_path} not found', file=sys.stderr)
        sys.exit(1)

    code = sas_path.read_text(encoding='utf-8', errors='replace')
    doc = build_doc(code, str(sas_path))

    if args.output:
        Path(args.output).write_text(doc, encoding='utf-8')
        print(f'Design doc written to {args.output}')
    else:
        print(doc)


if __name__ == '__main__':
    main()
