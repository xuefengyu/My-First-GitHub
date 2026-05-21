# Design Document: `%macro m_stats_sum`

## 1. Overview

| Field | Value |
|---|---|
| **Macro Name** | `m_stats_sum` |
| **Author** | FY |
| **Created Date** | 20FEB2026 |
| **Last Modified** | 19MAY2026 |
| **Version** | 1.12 |
| **Status** | Approved |
| **Program Location** | `m_stats_sum.sas` |
| **SAS Version** | Linux SAS 9.4 |

## 2. Purpose

End-to-end macro for producing a descriptive statistics summary table from an ADaM BDS dataset (e.g., ADLB, ADVS). Performs four integrated steps:

1. Calculates descriptive statistics for AVAL, and optionally BASE, CHG, and PCHG, using PROC MEANS with support for geometric statistics (GEO_MEAN, GEO_CV).
2. Derives Big-N population counts from a denominator dataset and appends them to the statistics output.
3. Formats numeric statistics to the appropriate decimal precision by merging with a global and/or local precision lookup table. Combines individual statistics into display-ready strings (Mean (SD), Q1/Q3, Min/Max).
4. Generates a PROC REPORT output table with treatment arms as columns, analysis visits as row groups, and automatic page-break logic.

## 3. Parameters

| # | Parameter | Required | Type | Default | Description |
|---|-----------|----------|------|---------|-------------|
| 1 | `popds` | Yes | Dataset name (with optional WHERE) | _(none)_ | Denominator population dataset. Supports inline WHERE clause, e.g. `adam.adsl(where=(saffl='Y'))` |
| 2 | `inds` | Yes | Dataset name (with optional WHERE) | _(none)_ | Input ADaM BDS dataset including conditions to select observations and PARAMCDs |
| 3 | `byvar` | No | Space-delimited variable list | `paramcd param avisitn avisit` | BY variables for statistics grouping. PARCAT1 and PARAMN auto-removed if not in dataset |
| 4 | `trtnvar` | Yes | Variable name | _(none)_ | Numeric treatment variable name |
| 5 | `trtvar` | Yes | Variable name | _(none)_ | Character treatment variable name |
| 6 | `stat_list` | No | Space-delimited keyword list | `n mean stddev median q1 q3 min max use_chg use_pchg` | PROC MEANS statistics to compute. Supports standard keywords plus `GEO_MEAN`, `GEO_CV`. Add `USE_CHG` and/or `USE_PCHG` to include change/percent-change statistics |
| 7 | `cleanup` | No | Y/N | `Y` | Delete all intermediate work datasets on completion |
| 8 | `outid` | No | Text | _(blank)_ | Output identifier passed to `%ODSSTART` for file naming |
| 9 | `param_title` | No | Y/N | `Y` | If Y, prints `title8 "Parameter: #byval(param)"` |
| 10 | `c1_width` | No | Numeric (inches) | `1` | Column width for Analysis Visit. Minimum enforced: 0.8in |
| 11 | `c2_width` | No | Numeric (inches) | `1` | Column width for Endpoint and Statistics. Minimum enforced: 0.8in |
| 12 | `page_sec` | No | Integer | `2` | Number of sections per page for page breaking |

### Internal (Hard-coded) Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `lookupdir_glb` | `LOOKUP_D` | Libref for global precision lookup table |
| `lookup_glb` | `PRECISION_UPDATED` | Member name of global precision lookup table |
| `lookupdir_loc` | `LOOKUP_L` | Libref for study-level local precision lookup table |
| `lookup_loc` | `PRECISION_E` | Member name of local precision lookup table |

## 4. Input Datasets

| # | Dataset | Library | Key Variables | Description |
|---|---------|---------|---------------|-------------|
| 1 | `&inds` (parsed as `&inds_lib..&inds_mem`) | User-specified or WORK | `USUBJID`, `&trtnvar`, `&trtvar`, `PARAMCD`, `PARAM`, `AVAL`, optionally `BASE`, `CHG`, `PCHG`, `PARCAT1`, `PARAMN`, `AVISITN`, `AVISIT`, `ABLFL` | Source ADaM BDS analysis dataset |
| 2 | `&popds` (parsed as `&popds_lib..&popds_mem`) | User-specified or WORK | `USUBJID`, `&trtnvar`, `&trtvar` | Denominator population dataset for Big-N counts |
| 3 | `&lookupdir_glb..&lookup_glb` | LOOKUP_D | `PARAMCD`, `PARAM`, `MAX_DECIMAL_LENGTH`, optionally `PARCAT1` | Global precision lookup table |
| 4 | `&lookupdir_loc..&lookup_loc` | LOOKUP_L | `PARAMCD`, `PARAM`, `MAX_DECIMAL_LENGTH`, optionally `PARCAT1` | Local (study-level) precision lookup table |
| 5 | `&lookupdir_loc..LOOKUP_STAT` | LOOKUP_L | `STAT_VAR`, `STATISTIC`, `RULE` | Optional table specifying decimal-place rules per statistic |

## 5. Output Datasets

| # | Dataset | Library | Key Variables | Description |
|---|---------|---------|---------------|-------------|
| 1 | `outdir.&outdset._stats_out` | OUTDIR | `&byvar`, `STAT_VAR`, `STATISTIC`, `VALUE`, `&trtnvar`, `STAT_ORD` | Raw statistics in long format |
| 2 | `outdir.&outdset._stats_fmt` | OUTDIR | `&byvar`, `STAT_VAR`, `STATISTIC`, `C_VALUE`, `STAT_DISPLAY`, `SECTION_ORDER`, `STAT_ORDER` | Formatted statistics with display labels |
| 3 | `outdir.&outdset` | OUTDIR | `&byvar`, `STAT_DISPLAY`, `TRT_1`–`TRT_n`, `PAGE_GROUP` | Final wide-format report dataset |
| 4 | QC copy via `%u_copyod` | QCDATA | Same as above | Copy of output for QC purposes |

## 6. Processing Steps

1. **Step 0 — Parameter Parsing & Validation**
   - Parse `&inds` and `&popds` to extract library/member/WHERE clause (handles `adam.adoct`, `adam.adoct(where=(...))`, `adoct`, `adoct(where=(...))`)
   - Verify `&inds` and `&popds` datasets exist
   - Check `AVAL` exists (abort if not)
   - Check `BASE`, `CHG`, `PCHG` existence (warn if missing when requested)
   - Auto-detect and remove `PARCAT1` and `PARAMN` from `&byvar` if not in dataset
   - Validate `&trtnvar` is numeric and `&trtvar` is character in both `&inds` and `&popds` via `%check_var_types`
   - Verify 1:1 mapping between `PARAMCD` and `PARAM` (warn if violated)

2. **Step 1 — Data Preparation**
   - Stack `BASE` (where `ABLFL=''`), `AVAL`, `CHG`, `PCHG` into single `NEWVAL` column with `STAT_VAR` indicator
   - Filter to non-missing `NEWVAL` only
   - Sort by `&byvar`, `STAT_VAR`, `NEWVALN`, `&trtnvar`, `&trtvar`

3. **Step 2 — Statistics Calculation**
   - Parse `&stat_list` to identify standard and geometric statistics
   - Run `PROC MEANS` with cleaned stat list on `NEWVAL`
   - If `GEO_MEAN` / `GEO_CV` requested: log-transform positive values, compute via `PROC MEANS`, back-transform
   - Merge geometric stats with standard stats
   - Transpose to long format (`STATISTIC`, `VALUE` columns)
   - Clean statistic names from auto-named variables

4. **Step 3 — Population Counts (Big-N)**
   - Compute `COUNT(DISTINCT USUBJID)` per `&trtnvar` from `&popds` via `PROC SQL`
   - Left-join Big-N to statistics output as `__FREQ__`
   - Assign `STAT_ORD` for sorting (N=1, MEAN=2, ..., GEO_CV=12, LCLM=13, UCLM=14)

5. **Step 4 — Precision Lookup**
   - Load global lookup table (`LOOKUP_D.PRECISION_UPDATED`)
   - If local lookup table exists (`LOOKUP_L.PRECISION_E`), merge with global (local takes precedence for matching PARAMCDs)
   - Identify PARAMCDs in data but missing from both lookup tables (warn)

6. **Step 5.1 — Formatting Statistics**
   - If `LOOKUP_L.LOOKUP_STAT` exists, merge `RULE` column for per-statistic decimal control
   - Merge precision (`MAX_DECIMAL_LENGTH` → `avalc_decimals`) onto statistics
   - Apply decimal formatting rules:
     - **With LOOKUP_STAT**: N → 8.0; CV → `avalc_decimals+1`; GEO_CV → 12.2; others → `avalc_decimals + RULE`
     - **Without LOOKUP_STAT (AVAL/BASE/CHG)**: N → 8.0; MEAN/MEDIAN/Q1/Q3/GEO_MEAN → +1 decimal; STDDEV/STDERR/LCLM/UCLM → +2; MIN/MAX → same as AVAL; CV → +1; GEO_CV → 12.2
     - **Without LOOKUP_STAT (PCHG)**: MEAN/MEDIAN/Q1/Q3 → +2; STDDEV/STDERR → +3; MIN/MAX → +1; CV → +2; GEO_CV → +1
   - Round values before formatting (`r_value = round(value, 10**(-(decimals)))`)
   - Remove leading minus from formatted zeros (e.g., `-0.0` → `0.0`)
   - Combine paired statistics: `MEAN (SD)`, `Q1, Q3`, `Min, Max` (with `NA` for missing SD when N=1)

7. **Step 5.2 — Report Preparation**
   - Map statistics to display labels with indentation (e.g., `'   Mean (SD)'`)
   - Create section headers: Baseline, Observed, Change from Baseline, Percent Change from Baseline
   - Add `'NA'` for N in visits with no observations
   - Add blank spacing before each section

8. **Step 5.3 — Page Break Logic**
   - Count sections per BY group
   - Assign `PAGE_GROUP = ceil(section_count / &page_sec)`

9. **Step 5.4–5.5 — Column Width Calculation**
   - Extract treatment labels and Big-N for column headers
   - Calculate treatment column widths: `(9.95 - fixed_widths - padding) / trt_count`
   - Enforce minimum 0.8in per column

10. **Step 5.6 — Wide Format Transpose**
    - Transpose `C_VALUE` by `&trtnvar` into `TRT_1`, `TRT_2`, ... columns

11. **Step 5.7 — PROC REPORT Generation**
    - Dynamic BY statement from PARAM-related variables (used for titles)
    - Dynamic COLUMNS with hidden ORDER variables (e.g., `AVISITN`) and visible row-group variable (last `*VISIT*` variable)
    - Treatment columns centered with headers showing `Treatment Name (N=xxx)`
    - Page breaks after every `&page_sec` sections
    - ODS RTF output via `%ODSSTART` / `%ODSSTOP`
    - QC copy via `%u_copyod`

12. **Step 6 — Cleanup**
    - If `&cleanup=Y`, delete all `_&SYSJOBID._*` temp datasets

## 7. Validation & Error Handling

| Check | Condition | Action |
|-------|-----------|--------|
| `&inds` parameter empty | `%length(&inds) = 0` | `%PUT ERROR` → `%RETURN` |
| `&popds` parameter empty | `%length(&popds) = 0` | `%PUT ERROR` → `%RETURN` |
| Input dataset does not exist | `%SYSFUNC(exist(&inds_)) = 0` | `%PUT ERROR` → `%RETURN` |
| Temp dataset not created | `%SYSFUNC(exist(_&SYSJOBID._&inds_mem)) = 0` | `%PUT ERROR` → `%RETURN` |
| AVAL not found in input | `VARNUM = 0` | `%PUT ERROR` → `%RETURN` |
| BASE not found | `VARNUM = 0` | `%PUT WARNING` — skip BASE stats |
| CHG not found when USE_CHG=Y | `VARNUM = 0` | `%PUT WARNING` — skip CHG stats |
| PCHG not found when USE_PCHG=Y | `VARNUM = 0` | `%PUT WARNING` — skip PCHG stats |
| PARCAT1 not in dataset | `VARNUM = 0` | Auto-remove from `&byvar`, NOTE |
| PARAMN not in dataset | `VARNUM = 0` | Auto-remove from `&byvar`, NOTE |
| `&trtnvar` wrong type or missing | Via `%check_var_types` | `%PUT ERROR` |
| `&trtvar` wrong type or missing | Via `%check_var_types` | `%PUT ERROR` |
| PARAMCD↔PARAM not 1:1 | `COUNT(DISTINCT) > 1` | `%PUT WARNING` with detail listing |
| No precision for PARAMCD | Merge miss (`a and not p`) | `%PUT WARNING`, output to `_get_deci` |
| Statistics dataset missing | `%SYSFUNC(exist) = 0` | `%PUT ERROR` → `%RETURN` |
| Global lookup table missing | `%SYSFUNC(exist) = 0` | `%PUT WARNING` — no formatted report |
| Local lookup table missing | `%SYSFUNC(exist) = 0` | `%PUT WARNING` — use global only |
| LOOKUP_STAT missing | `%SYSFUNC(exist) = 0` | `%PUT WARNING` — use default decimal rules |
| Column width too narrow | `< 0.8` | Force to 0.8in with WARNING |

## 8. Dependencies

- **Utility Macros (embedded):**
  - `%is_empty` — checks if a dataset has zero observations
  - `%check_var_types` — validates variable existence and type (C/N) in a dataset

- **External Macros Called:**
  - `%ODSSTART` — opens ODS RTF destination with titles
  - `%ODSSTOP` — closes ODS RTF destination
  - `%u_copyod` — copies output dataset to QC directory

- **External Files/Libraries:**
  - `LOOKUP_D` library — global precision lookup table
  - `LOOKUP_L` library — local (study-level) precision and LOOKUP_STAT tables
  - `OUTDIR` library — output dataset destination
  - `meta.titles` — titles metadata dataset

- **SAS Products Required:** Base SAS, SAS/STAT (PROC MEANS)

## 9. Example Usage

```sas
%m_stats_sum(
  popds       = adam.adsl(where=(saffl='Y')),
  inds        = adam.adlb(where=(saffl='Y' and anl01fl='Y' and paramcd in ('ALB','ALP','ALT'))),
  byvar       = paramcd param avisitn avisit,
  trtnvar     = trt01an,
  trtvar      = trt01a,
  stat_list   = n mean stddev median q1 q3 min max use_chg use_pchg,
  cleanup     = Y,
  outid       = t_14_3_1_1,
  param_title = Y,
  c1_width    = 1,
  c2_width    = 1,
  page_sec    = 2
);
```

## 10. Modification History

| Date | Author | Version | Description |
|------|--------|---------|-------------|
| 20FEB2026 | FY | 1.0 | Initial creation |
| 28FEB2026 | FY | 1.1 | Initial version |
| 10MAR2026 | FY | 1.2 | Output STATS_OUT & STATS_FORMATTED to QC data |
| 25MAR2026 | FY | 1.3 | Remove default values for POPDS, INDS; remove DECI_UPDATE, DEFAULT_DECI macro vars |
| 26MAR2026 | FY | 1.4 | Add PARAM in BY variables for merging with _DECI_LOOKUP; set PARCAT1 length to $200 |
| 30MAR2026 | FY | 1.5 | Move lookup params internal; combine WHERE_CLAUSE/PARAM_FILTER with INDS; combine USE_CHG/USE_PCHG with STAT_LIST; add _&SYSJOBID._ prefix to temp datasets; add PARAMN to default BYVAR; add PARAMCD↔PARAM 1:1 check |
| 06APR2026 | FY | 1.6 | Add &INDS_ and &POPDS_ to allow WHERE conditions in &INDS and &POPDS |
| 07APR2026 | FY | 1.7 | Add one more digit for PCHG; make MIN & MAX same decimal places as AVAL |
| 20APR2026 | FY | 1.8 | Remove '-' from '-0.0' values; handle N=1 STDDEV missing → 'Mean (NA)'; add 'NA' for N in empty visits; add spacing before AVISITN; add PARAM_TITLE |
| 28APR2026 | FY | 1.9 | Add STAT_ORD in _stats_out; move SECTION_ORDER/STAT_ORDER to _STATS_FORMATTED |
| 04MAY2026 | FY | 1.10 | Remove TRTNVAR/TRTVAR defaults; add %CHECK_VAR_TYPES; dynamic PROC REPORT with %DO loops; library/member parsing for INDS & POPDS |
| 05MAY2026 | FY | 1.11 | Remove font_weight=bold; set thin border style in PROC REPORT |
| 07MAY2026 | FY | 1.11a | Add AVISIT to default BYVAR |
| 08MAY2026 | FY | 1.11b | Add asis=on for stat_display indentation |
| 19MAY2026 | FY | 1.12 | Merge LOOKUP_STAT for per-statistic decimal rules; add r_value rounding before formatting |
