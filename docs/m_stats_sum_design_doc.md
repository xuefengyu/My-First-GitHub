# BIOSTATISTICS & STATISTICAL PROGRAMMING DESIGN DOCUMENT

## Standard Program/Macro

|  |  |
|---|---|
| **Name(s):** | M_STATS_SUM |
| **Description:** | End-to-end macro for producing a descriptive statistics summary table from an ADaM BDS dataset. Performs five integrated steps: (1) calculates statistics for AVAL and optionally BASE, CHG, PCHG; (2) derives Big-N population counts; (3) combines global and local precision lookup tables; (4) formats statistics using resolved precision; (5) generates a PROC REPORT output table with dynamic column layout driven by the BY variable list. |

|  |  |
|---|---|
| **Project Lead (Approved by):** | |
| Name: | |
| Signature: | |
| Date: | |

|  |  |
|---|---|
| **Development Programmer (Completed By):** | |
| Name: | |
| Signature: | |
| Date: | |

**Date of Document:** 2026-05-04

---

## 1. Detailed Description of Functions and Requirements

The general function is to produce a complete descriptive statistics summary table from an ADaM BDS dataset in a single macro call. M_STATS_SUM is an end-to-end wrapper that integrates statistics calculation, precision lookup, formatting, and PROC REPORT generation. It processes multiple analysis variables (BASE, AVAL, CHG, PCHG) by stacking them into a unified dataset, calculating statistics via PROC MEANS, formatting numeric results to protocol-specified decimal precision, and rendering the final table with treatment arms as columns and analysis visits as row groups. The PROC REPORT section is fully dynamic — column definitions, BY statements, and ORDER variables are all generated via `%DO` loops over the `BYVAR` parameter, allowing different report layouts without code modification.

| No. | Requirements | Detailed Description |
|-----|-------------|---------------------|
| 1 | Statistics Calculation | • Calculate standard descriptive statistics: n, Mean, SD, Median, Q1, Q3, Min, Max<br>• Support geometric statistics: Geometric Mean, Geometric CV<br>• Handle missing values by excluding from calculations<br>• Support multiple treatment groups and optional BY variables |
| 2 | Variable Stacking | • Stack BASE, AVAL, CHG, PCHG into unified NEWVAL variable<br>• Assign NEWVALN codes: 1=BASE, 2=AVAL, 3=CHG, 4=PCHG<br>• Create STAT_VAR indicator for each analysis variable<br>• BASE is auto-detected and included if present; no parameter needed<br>• CHG/PCHG included only when USE_CHG / USE_PCHG keywords are present in stat_list AND variable exists in dataset |
| 3 | Dataset Parsing | • Parse INDS and POPDS to extract library name and member name<br>• Handle four input forms: `lib.mem`, `lib.mem(where=(...))`, `mem`, `mem(where=(...))`<br>• Default library to WORK when no libref is provided<br>• Use member name only for temp dataset naming to avoid exceeding 8-character libref limit |
| 4 | Input Validation | • Validate input dataset exists; abort if not found<br>• Check AVAL variable present (required); abort if absent<br>• Issue WARNING for BASE, CHG, PCHG if not found<br>• Issue WARNING when PARCAT1 or PARAMN absent; auto-remove from BY variables<br>• Check TRTNVAR and TRTVAR exist with correct types (numeric/character) in both POPDS and INDS via %CHECK_VAR_TYPES utility macro<br>• Check 1:1 mapping between PARAMCD and PARAM; issue WARNING if duplicates found<br>• Display processing plan (variables included) in SAS log |
| 5 | Precision Lookup | • Merge global precision lookup table with study-level local lookup table<br>• PARAMCDs in both tables resolved in favour of local table<br>• PARAMCDs absent from both tables trigger a WARNING in log<br>• Both lookup tables must contain a MAX_DECIMAL_LENGTH column<br>• Lookup table librefs and member names are hardcoded inside the macro (not user-changeable) |
| 6 | Statistics Formatting | • Format numeric statistics to resolved decimal precision<br>• For AVAL, BASE, CHG: N uses integer format (8.0); Mean, Median, Q1, Q3, Geo Mean: base decimals + 1; SD, StdErr, LCLM, UCLM: base decimals + 2; Min, Max: base decimals (no addition); CV: value × 100, base decimals + 1; Geo CV: 12.2 fixed<br>• For PCHG: Mean, Median, Q1, Q3, Geo Mean: base decimals + 2; SD, StdErr, LCLM, UCLM: base decimals + 3; Min, Max: base decimals + 1; CV: value × 100, base decimals + 2; Geo CV: base decimals + 1<br>• Remove leading '-' from values like '-0.0' or '-0'<br>• If n=1, STDDEV is missing but MEAN is not, display as 'Mean (NA)'<br>• Combine MEAN/STDDEV into 'Mean (SD)'; Q1/Q3 into 'Q1, Q3'; Min/Max into 'Min, Max' |
| 7 | Dynamic Table Reporting | • PROC REPORT layout is fully driven by &BYVAR using %DO loops<br>• Automatically identifies the visible row-group column (last variable containing "VISIT" in &BYVAR; falls back to last variable if none found)<br>• PARAM-related variables (containing "PARAM" or equal to "PARCAT1") are placed in the BY statement for page-level titles<br>• All other variables become hidden ORDER NOPRINT columns for sorting<br>• Treatment columns are dynamically generated based on treatment count<br>• Automatic page-break logic controlled by page_sec parameter<br>• Column widths auto-calculated from c1_width, c2_width, and treatment count<br>• Treatment column minimum width enforced at 0.8 inch<br>• Section headers inserted as bold label rows (Baseline, Observed, Change from Baseline, % Change)<br>• 'NA' inserted for N in visits with no observations<br>• Spacing added before each visit group and after each section<br>• Optional PARAM_TITLE prints parameter value in title8 |
| 8 | Output Datasets | • Save _stats_out (unformatted statistics with STAT_ORD) to outdir library<br>• Save _stats_formatted (formatted statistics with SECTION_ORDER, STAT_ORDER) to outdir library<br>• Save final wide report dataset to outdir library<br>• Copy QC dataset via %u_copyod utility |
| 9 | Temp Dataset Management | • All intermediate datasets prefixed with `_&SYSJOBID._` to avoid naming conflicts with user datasets<br>• Cleanup parameter controls deletion of all temp datasets on completion |

---

## 2. Macro Name and Description of Macro Parameters

The name of the macro is m_stats_sum and the source file is 'm_stats_sum.sas'. All parameters are keyword-style. Parameters with no default value (popds, inds, trtnvar, trtvar) are required and the macro will abort with an ERROR if they are absent or resolve to a non-existent dataset.

### 2.1 User-Facing Macro Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| popds | Dataset | | Yes | Denominator population dataset, optionally with WHERE clause (e.g., `adam.adsl(where=(saffl='Y'))`). Provides Big-N treatment group counts. Supports forms: `lib.mem`, `lib.mem(where=(...))`, `mem`, `mem(where=(...))`. Library defaults to WORK if no libref provided. |
| inds | Dataset | | Yes | Input ADaM BDS dataset (e.g., `adam.adlb`, `adam.advs`). Must contain AVAL; BASE, CHG, PCHG auto-detected. Supports same forms as popds including inline WHERE clause and PARAMCD filtering. |
| byvar | String | paramcd param avisitn | No | Space-delimited BY variables for statistics grouping. PARCAT1 and PARAMN are auto-detected: if present in inds they are retained; if absent they are silently removed. The 4 variables PARAMCD, PARAM, AVISITN, and AVISIT are expected for standard use. The last variable containing "VISIT" becomes the visible row-group column in PROC REPORT. |
| trtnvar | String | | Yes | Numeric treatment variable name used for grouping and Big-N derivation. Must exist with numeric type in both POPDS and INDS. |
| trtvar | String | | Yes | Character treatment variable name used for column headers in the report. Must exist with character type in both POPDS and INDS. |
| stat_list | String | n mean stddev median q1 q3 min max use_chg use_pchg | No | Space-delimited list of PROC MEANS statistics to compute. Supports all standard keywords plus GEO_MEAN and GEO_CV. Geometric statistics are computed via log-transformation on NEWVAL > 0 records. Include keyword USE_CHG to calculate CHG statistics; include USE_PCHG to calculate PCHG statistics. These keywords are parsed and removed before passing to PROC MEANS. |
| cleanup | Y/N | Y | No | Delete all intermediate WORK datasets (prefixed `_&SYSJOBID._`) on completion: Y or N. Set to N for debugging. |
| outid | String | | No | Output identifier passed to %ODSSTART for ODS RTF file naming. |
| param_title | Y/N | Y | No | If Y, prints `title8 j=l "Parameter: #byval(param)"` in the report output. |
| c1_width | Numeric | 1 | No | Column width (inches) for the visible row-group column (e.g., Analysis Visit) in PROC REPORT. Minimum enforced at 0.8 inch. |
| c2_width | Numeric | 1 | No | Column width (inches) for Endpoint and Statistics column in PROC REPORT. Minimum enforced at 0.8 inch. |
| page_sec | Numeric | 2 | No | Number of visit-sections per page. Controls BREAK AFTER PAGE_GROUP in PROC REPORT. |

### 2.2 Internal (Hardcoded) Parameters

These are set inside the macro and cannot be changed by the user in the macro call:

| Parameter | Value | Description |
|-----------|-------|-------------|
| lookupdir_glb | LOOKUP_D | Libref for global precision lookup table. |
| lookup_glb | PRECISION_UPDATED | Member name of global precision lookup table. Must contain PARAMCD, PARAM, and MAX_DECIMAL_LENGTH columns. |
| lookupdir_loc | LOOKUP_L | Libref for study-level local precision lookup table. |
| lookup_loc | PRECISION_E | Member name of local precision lookup table. PARAMCDs present in both local and global tables are resolved in favour of local. |

### 2.3 Utility Macros

| Macro | Description |
|-------|-------------|
| %IS_EMPTY(dsn) | Returns the number of observations in a dataset. Used internally to check if warning datasets have records. |
| %CHECK_VAR_TYPES(CHECK_DATA=, CHECK_VAR=, CHECK_TYP=) | Validates that a variable exists in a dataset and has the expected type (C or N). Issues ERROR if variable is missing or wrong type; issues NOTE if correct. |

### 2.4 External Dependency Macros

The following utility macros must be available in the SAS session before invoking m_stats_sum:

| Macro | Purpose |
|-------|---------|
| %ODSSTART | Opens ODS RTF output with specified OutputID and title/footnote set. |
| %ODSSTOP | Closes ODS RTF output. |
| %u_copyod | Copies output dataset from outdir to qcdata library. |

---

## 3. Modification History

| Version Number | Date (YYYY-MM-DD) | Description |
|----------------|-------------------|-------------|
| 1.0 | 2026-02-28 | Initial Version |
| 1.1 | 2026-03-10 | Output Stat_out & stat_formatted to QC data |
| 1.2 | 2026-03-25 | Remove default values for POPDS, INDS. Remove macro variables DECI_UPDATE, DEFAULT_DECI |
| 1.3 | 2026-03-26 | Add PARAM in BY variables for merging with _DECI_LOOKUP. Set length of PARCAT1 as $200 if included in dataset |
| 1.4 | 2026-03-30 | Per Chao's suggestions: (1) Move lookupdir_glb, lookupdir_loc, lookup_glb, lookup_loc inside macro as hardcoded values. (2) Combine WHERE_CLAUSE, PARAM_FILTER with INDS; combine USE_CHG, USE_PCHG with STAT_LIST as keywords. (3) Add `_&SYSJOBID._` prefix to temp datasets to avoid naming conflicts. (4) Add PARAMN in byvar and check existence. (5) Add PARAMCD/PARAM 1:1 mapping check. |
| 1.5 | 2026-04-06 | Add INDS_ and POPDS_ parsing to allow WHERE conditions in INDS and POPDS parameters. |
| 1.6 | 2026-04-07 | Add one more digit for PCHG statistics. Make MIN & MAX same decimal places as AVAL. |
| 1.7 | 2026-04-20 | (1) Remove '-' if c_value is '-0.0' or similar. (2) If n=1 and STDDEV missing, set 'Mean (NA)'. (3) Add 'NA' for N in visits with no observations. (4) Add spacing before each AVISITN. (5) Add PARAM_TITLE parameter. |
| 1.8 | 2026-04-28 | Added STAT_ORD in _stats_out. Move SECTION_ORDER, STAT_ORDER from _REPORT_PREP to _STATS_FORMATTED. |
| 1.9 | 2026-05-04 | (1) Remove default values for TRTNVAR and TRTVAR (now required). (2) Add %CHECK_VAR_TYPES utility macro. (3) Dynamic PROC REPORT: columns, define, by, and compute statements use %DO loops over &BYVAR. NOTE: PARAMCD, PARAM, AVISITN, AVISIT are required in &BYVAR. (4) Library/member parsing for INDS & POPDS to fix libref overflow error when temp dataset names exceed 8 characters. |

---

## 4. Usage Notes (with reference examples)

| No. | Details |
|-----|---------|
| 1 | Population dataset (popds) should include WHERE clause to define the analysis population (e.g., `adam.adsl(where=(saffl='Y'))`). This ensures correct Big-N denominators per treatment arm. Supports `lib.mem`, `lib.mem(where=(...))`, `mem`, or `mem(where=(...))` forms. |
| 2 | Input dataset (inds) must be an ADaM BDS dataset with AVAL (required). BASE is auto-detected and included if present. CHG and PCHG are included only when USE_CHG / USE_PCHG keywords are present in stat_list AND the variable exists. WHERE conditions and PARAMCD filtering should be included inline (e.g., `adam.adlb(where=(saffl='Y' and paramcd in ('ALT','AST')))`). |
| 3 | PARCAT1 and PARAMN are auto-detected: if present in inds they are included in BY grouping; if absent they are silently removed from byvar. No manual action needed. |
| 4 | Global and local precision lookup tables must contain PARAMCD, PARAM, and MAX_DECIMAL_LENGTH. If a PARAMCD appears in both, the local table value takes precedence. PARAMCDs absent from both tables log a WARNING. The librefs (LOOKUP_D, LOOKUP_L) and member names (PRECISION_UPDATED, PRECISION_E) are hardcoded inside the macro. |
| 5 | Geometric statistics (GEO_MEAN, GEO_CV) are computed only for records where NEWVAL > 0. Sample size for geometric statistics may therefore differ from standard N. |
| 6 | The macro calls %ODSSTART, %ODSSTOP, and %u_copyod; these utility macros must be available in the SAS session before invoking m_stats_sum. |
| 7 | TRTNVAR and TRTVAR have no defaults and must be explicitly specified. The macro validates their existence and type in both POPDS and INDS using %CHECK_VAR_TYPES. |
| 8 | The PROC REPORT layout is fully dynamic. The last variable in &BYVAR containing "VISIT" becomes the visible row-group column. Variables containing "PARAM" or equal to "PARCAT1" become the BY statement (for page-level titles). All remaining variables become hidden ORDER columns for sorting. If no VISIT variable is found, the last &BYVAR variable is used as the visible column. |
| 9 | The macro checks for 1:1 mapping between PARAMCD and PARAM. If duplicates are found (one PARAMCD mapping to multiple PARAMs or vice versa), a WARNING is issued with details of affected values. This prevents incorrect merges with the precision lookup table. |
| 10 | Basic example — laboratory data with change from baseline:<br>`%m_stats_sum(`<br>`  popds=%str(adam.adsl(where=(saffl='Y'))),`<br>`  inds=%str(adam.adlb(where=(saffl='Y' and anl01fl='Y'))),`<br>`  byvar=parcat1 paramcd param avisitn avisit,`<br>`  trtnvar=trtan, trtvar=trta,`<br>`  stat_list=n mean stddev median q1 q3 min max use_chg,`<br>`  outid=t_lb_sum,`<br>`  page_sec=2`<br>`);` |
| 11 | PK data with geometric statistics:<br>`%m_stats_sum(`<br>`  popds=%str(adam.adsl(where=(pkfl='Y'))),`<br>`  inds=%str(adam.adpp(where=(paramcd in ('AUCIFO','CMAX')))),`<br>`  byvar=paramcd param pctptnum pctpt,`<br>`  trtnvar=trtpn, trtvar=trtp,`<br>`  stat_list=n mean stddev median min max geo_mean geo_cv,`<br>`  outid=t_pk_sum,`<br>`  page_sec=3`<br>`);` |
| 12 | WORK library dataset (no libref):<br>`%m_stats_sum(`<br>`  popds=adsl,`<br>`  inds=%str(adoct(where=(saffl='Y'))),`<br>`  byvar=paramcd param avisitn avisit,`<br>`  trtnvar=trt01an, trtvar=trt01a,`<br>`  stat_list=n mean stddev median q1 q3 min max,`<br>`  outid=t_oct_sum`<br>`);` |

---

## 5. Contents of Output Data

### 5.1 Unformatted Statistics Output (_stats_out — LONG Format)

Saved to outdir library as `&outdset._stats_out`. Contains one row per statistic per BY group per treatment arm. All numeric values are unformatted.

| # | Variable | Type | Len | Label |
|---|----------|------|-----|-------|
| 1 | PARCAT1 | Char | 200 | Parameter Category 1 (if present in inds) |
| 2 | PARAMCD | Char | 8 | Parameter Code |
| 3 | PARAM | Char | 200 | Parameter |
| 4 | AVISITN | Num | 8 | Analysis Visit (N) |
| 5 | AVISIT | Char | 200 | Analysis Visit |
| 6 | STAT_VAR | Char | 8 | Analysis Variable (BASE/AVAL/CHG/PCHG) |
| 7 | NEWVALN | Num | 8 | Analysis Variable Code (1=BASE, 2=AVAL, 3=CHG, 4=PCHG) |
| 8 | &trtnvar | Num | 8 | Treatment (Numeric) — name reflects trtnvar value |
| 9 | &trtvar | Char | 200 | Treatment (Character) — name reflects trtvar value |
| 10 | statistic | Char | 20 | Statistic Name (N, MEAN, STDDEV, MEDIAN, Q1, Q3, MIN, MAX, GEO_MEAN, GEO_CV, etc.) |
| 11 | value | Num | 8 | Unformatted Statistic Value |
| 12 | __FREQ__ | Num | 8 | Treatment Group Population Count (Big-N from popds) |
| 13 | _TYPE_ | Num | 8 | PROC MEANS Type Indicator |
| 14 | _FREQ_ | Num | 8 | PROC MEANS Frequency |
| 15 | stat_ord | Num | 8 | Statistic Display Order (1=N, 2=MEAN, ..., 14=UCLM, 99=other) |

### 5.2 Formatted Statistics Dataset (_stats_formatted)

Saved to outdir library as `&outdset._stats_fmt`. Contains formatted character values (c_value) and display labels. MEAN/STDDEV, Q1/Q3, and MIN/MAX are combined into paired display strings.

| # | Variable | Type | Len | Label |
|---|----------|------|-----|-------|
| 1 | PARCAT1 | Char | 200 | Parameter Category 1 (if present in inds) |
| 2 | PARAMCD | Char | 40 | Parameter Code |
| 3 | PARAM | Char | 200 | Parameter |
| 4 | AVISITN | Num | 8 | Analysis Visit (N) |
| 5 | AVISIT | Char | 200 | Analysis Visit |
| 6 | STAT_VAR | Char | 8 | Analysis Variable (BASE/AVAL/CHG/PCHG) |
| 7 | &trtnvar | Num | 8 | Treatment (Numeric) |
| 8 | &trtvar | Char | 200 | Treatment (Character) |
| 9 | statistic | Char | 50 | Display Statistic Name (N, MEAN_SD, Q1_Q3, MIN_MAX, MEDIAN, GEO_MEAN, GEO_CV, etc.) |
| 10 | c_value | Char | 50 | Formatted Statistic Value (decimal-precision applied) |
| 11 | __FREQ__ | Num | 8 | Treatment Group Population Count |
| 12 | stat_display | Char | 50 | Report Label (n, Mean (SD), Q1, Q3, Min, Max, Median, Geo Mean, Geo CV (%)) |
| 13 | stat_order | Num | 8 | Display Order of Statistic Row |
| 14 | stat_ord | Num | 8 | Statistic Order from Step 3 |
| 15 | section_header | Char | 100 | Section Label (Baseline, Observed, Change from Baseline, Percent Change from Baseline) |
| 16 | section_order | Num | 8 | Display Order of Section |
| 17 | visit_section | Char | 150 | Combined visit and section label for row display |

### 5.3 Final Wide Report Dataset

Saved to outdir library as `&outdset`. Transposed to wide format with one column per treatment arm (trt_1, trt_2, …). This is the dataset consumed by PROC REPORT.

| # | Variable | Type | Len | Label |
|---|----------|------|-----|-------|
| 1 | (BY variables from &byvar) | various | | All variables specified in &byvar |
| 2 | page_group | Num | 8 | Page Break Group (ceil(section_count / page_sec)) |
| 3 | section_order | Num | 8 | Section Display Order |
| 4 | stat_order | Num | 8 | Statistic Display Order |
| 5 | stat_display | Char | 50 | Statistic Label |
| 6 | section_count | Num | 8 | Cumulative section counter within visit |
| 7 | trt_1 … trt_N | Char | 50 | One column per treatment arm, transposed from c_value |

---

## 6. Dynamic PROC REPORT Logic

The PROC REPORT section uses the following algorithm to partition `&BYVAR` into three roles:

| Role | Selection Rule | PROC REPORT Usage |
|------|---------------|-------------------|
| **Visible row-group column** (`&rpt_vis_var`) | Last variable in &BYVAR whose name contains "VISIT" (case-insensitive). If none found, defaults to the last variable in &BYVAR. | `define ... / ID order order=internal` with cellwidth=&c1_width. Displayed in Column 1 of the report. |
| **BY statement variables** (`&rpt_by_vars`) | Variables whose name contains "PARAM" or equals "PARCAT1" (excluding the visible variable). | Placed in the `BY` statement of PROC REPORT. Controls page breaks by parameter. Used in `#byval()` title references. |
| **Hidden ORDER columns** (`&rpt_col_vars`) | All remaining variables (excluding visible and BY variables). Typically numeric sort keys like AVISITN, PARAMN. | `define ... / order order=internal noprint`. Provides sort order without displaying. |

**Example:** For `byvar=parcat1 paramn paramcd param avisitn avisit`:
- `rpt_vis_var` = AVISIT
- `rpt_by_vars` = PARCAT1 PARAMN PARAMCD PARAM
- `rpt_col_vars` = AVISITN

---

## 7. Dataset Parsing Logic

| Input Form | inds_ | inds_lib | inds_mem | Temp Dataset Name |
|------------|-------|----------|----------|-------------------|
| `adam.adoct` | adam.adoct | adam | adoct | `_&SYSJOBID._adoct` |
| `adam.adoct(where=(saffl='Y'))` | adam.adoct | adam | adoct | `_&SYSJOBID._adoct` |
| `adoct` | adoct | work | adoct | `_&SYSJOBID._adoct` |
| `adoct(where=(saffl='Y'))` | adoct | work | adoct | `_&SYSJOBID._adoct` |

The same logic applies to POPDS → `popds_`, `popds_lib`, `popds_mem`.
