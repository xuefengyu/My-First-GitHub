# Design Document: `%macro m_stats_sum`

## 1. Overview

| Field | Value |
|---|---|
| **Macro Name** | `m_stats_sum` |
| **Author** | Statistics Programming Team |
| **Created Date** | 2026-01-15 |
| **Last Modified** | 2026-05-12 |
| **Version** | 1.2 |
| **Status** | Approved |
| **Program Location** | `/macros/m_stats_sum.sas` |

## 2. Purpose

Generates summary statistics (N, Mean, Median, Std Dev, Min, Max) for one or more numeric variables, grouped by treatment arm, and outputs a formatted analysis dataset suitable for TLF reporting.

## 3. Parameters

| # | Parameter | Required | Type | Default | Description |
|---|-----------|----------|------|---------|-------------|
| 1 | `inds` | Yes | Dataset name | — | Input analysis dataset |
| 2 | `outds` | Yes | Dataset name | — | Output summary dataset |
| 3 | `varlist` | Yes | Variable list | — | Space-separated list of numeric analysis variables |
| 4 | `byvar` | No | Variable name | `TRTA` | Treatment grouping variable |
| 5 | `stats` | No | Keyword list | `N MEAN MEDIAN STD MIN MAX` | Statistics to compute |
| 6 | `decimal` | No | Integer | `1` | Number of decimal places for rounding |
| 7 | `debug` | No | Y/N | `N` | Keep intermediate datasets for debugging |

## 4. Input Datasets

| # | Dataset | Library | Key Variables | Description |
|---|---------|---------|---------------|-------------|
| 1 | `&inds` | WORK | `USUBJID`, `&byvar`, `&varlist` | Source analysis dataset (e.g., ADSL, ADLB) |

## 5. Output Datasets

| # | Dataset | Library | Key Variables | Description |
|---|---------|---------|---------------|-------------|
| 1 | `&outds` | WORK | `STAT`, `&byvar`, analysis variables | Summary statistics in long format |

## 6. Processing Steps

1. **Step 1 — Validation**
   - Verify `&inds` exists via `%SYSFUNC(exist())`
   - Check `&varlist` variables are numeric
   - Validate `&stats` keywords against allowed list
2. **Step 2 — Data Preparation**
   - Subset `&inds` to non-missing values of `&byvar`
   - Transpose variables if multiple in `&varlist`
3. **Step 3 — Core Logic**
   - Run `PROC MEANS` with requested statistics
   - Round results to `&decimal` decimal places
4. **Step 4 — Output Generation**
   - Transpose statistics into long format
   - Apply display formatting (e.g., "Mean (SD)" concatenation)
   - Output to `&outds`
5. **Step 5 — Cleanup**
   - Delete temp datasets `_ms_temp1`, `_ms_temp2` unless `&debug = Y`

## 7. Validation & Error Handling

| Check | Condition | Action |
|-------|-----------|--------|
| Input dataset exists | `%SYSFUNC(exist(&inds)) = 0` | `%PUT ERROR: Dataset &inds not found.` → abort |
| Variables are numeric | Variable type ≠ N | `%PUT WARNING: &var is not numeric — skipping.` |
| Valid stats keywords | Keyword not in allowed list | `%PUT ERROR: Invalid statistic &stat requested.` → abort |
| Output not overwritten | `&outds` already exists | `%PUT NOTE: &outds exists — overwriting.` |

## 8. Dependencies

- **Other Macros Called:** `%m_vartype`, `%m_dataset_exist`
- **External Files:** None
- **SAS Products Required:** Base SAS, SAS/STAT

## 9. Example Usage

```sas
%m_stats_sum(
  inds    = adam.adlb,
  outds   = work.lb_summary,
  varlist = AVAL CHG,
  byvar   = TRTA,
  stats   = N MEAN MEDIAN STD,
  decimal = 2,
  debug   = N
);
```

## 10. Modification History

| Date | Author | Version | Description |
|------|--------|---------|-------------|
| 2026-01-15 | J. Smith | 1.0 | Initial creation |
| 2026-03-20 | J. Smith | 1.1 | Added `decimal` parameter |
| 2026-05-12 | A. Lee | 1.2 | Added `debug` parameter; improved validation |
