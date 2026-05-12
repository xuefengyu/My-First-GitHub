# SAS Macro Design Doc — Copilot Prompt

Use this prompt with GitHub Copilot Chat (or any LLM) to generate a design document for a SAS macro.

---

## Instructions

1. Copy the prompt below.
2. Paste your SAS macro code after the prompt.
3. Submit to Copilot Chat.

---

## Prompt

```
You are a SAS programming documentation specialist. Given the SAS macro code below, generate a complete design document using the following structure. Extract all information directly from the code. If something cannot be determined from the code, mark it as "TBD".

### Output format
Use the exact Markdown template structure:

1. **Overview** — macro name, author (from header comments), dates, version, file path
2. **Purpose** — one paragraph summarizing what the macro does
3. **Parameters** — table with columns: #, Parameter, Required, Type, Default, Description
4. **Input Datasets** — table with columns: #, Dataset, Library, Key Variables, Description
5. **Output Datasets** — table with columns: #, Dataset, Library, Key Variables, Description
6. **Processing Steps** — numbered list of major steps (Validation → Data Prep → Core Logic → Output → Cleanup)
7. **Validation & Error Handling** — table of checks, conditions, and actions taken
8. **Dependencies** — other macros called, external files, SAS products required
9. **Example Usage** — a realistic SAS code example calling the macro
10. **Modification History** — table from header comments or "TBD"

### Rules
- Extract parameter defaults from the `%macro` statement.
- Identify datasets from `SET`, `MERGE`, `DATA`, `OUT=`, `PROC` statements.
- Identify validation from `%IF` checks on parameters or `%PUT ERROR`/`%PUT WARNING` patterns.
- List every macro invoked via `%macroname(` or `%SYSFUNC`.
- Keep descriptions concise (one sentence each).

### SAS Macro Code
<PASTE YOUR MACRO CODE HERE>
```
