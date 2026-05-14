# Design Document: `%macro m_global_lookup`

## 1. Overview

| Field | Value |
|---|---|
| **Macro Name** | `m_global_lookup` |
| **Author** | Frank Yu (FY) |
| **Created Date** | 06FEB2026 |
| **Last Modified** | 10APR2026 |
| **Version** | 1.2 |
| **Status** | Draft |
| **Program Location** | `m_global_lookup.sas` |

## 2. Purpose

Combines study-level precision lookup tables with a global lookup table, updating the global table with new PARAMCDs and resolving decimal-place discrepancies by taking the maximum precision across studies. This ensures a single, consistent global lookup table that provides decimal places for all studies.

## 3. Parameters

| # | Parameter | Required | Type | Default | Description |
|---|-----------|----------|------|---------|-------------|
| 1 | `lookupdir_glb` | No | Libref | `lookup_d` | Library reference for the global lookup table |
| 2 | `lookupdir_loc` | No | Libref | `lookup_l` | Library reference for the local (study) lookup table |
| 3 | `lookup_glb` | No | Dataset name | `PRECISION` | Name of the global lookup dataset |
| 4 | `lookup_loc` | No | Dataset name | `PRECISION_e` | Name of the local (study) lookup dataset |
| 5 | `deci_update` | No | Character (Y/N) | `Y` | Controls whether the global lookup table is updated with study-level decimal values |

## 4. Input Datasets

| # | Dataset | Library | Key Variables | Description |
|---|---------|---------|---------------|-------------|
| 1 | `PRECISION` (default) | `lookup_d` (default) | PARCAT1 (if exists), PARAMCD, PARAM | Global precision lookup table containing decimal places across all studies |
| 2 | `PRECISION_e` (default) | `lookup_l` (default) | PARCAT1 (if exists), PARAMCD, PARAM | Local study-level precision lookup table created by `m_stats_calc.sas` |

## 5. Output Datasets

| # | Dataset | Library | Key Variables | Description |
|---|---------|---------|---------------|-------------|
| 1 | `<lookup_glb>_updated` | `<lookupdir_glb>` | PARAMCD, PARAM | Updated global lookup table with merged precision values |
| 2 | `<lookup_loc>_updated` | WORK | PARAMCD, PARAM | Intermediate merged dataset used to build the final updated global table |
| 3 | `<lookup_loc>_mis` | WORK | PARAMCD, PARAM | PARAMCDs present in the local table but missing from the global table |
| 4 | `<lookup_loc>_dif` | WORK | PARAMCD, PARAM | PARAMCDs where global and local decimal places differ |

## 6. Processing Steps

1. **Step 1 — Validation**
   - Checks if PARCAT1 variable exists in the local lookup table via `%sysfunc(varnum())`.
   - Checks existence of global lookup table via `%sysfunc(exist())`.
   - Checks existence of local lookup table via `%sysfunc(exist())`.
2. **Step 2 — Data Preparation**
   - Sorts both global and local lookup tables by PARCAT1 (if present), PARAMCD, and PARAM.
3. **Step 3 — Core Logic**
   - Merges global and local tables; classifies each record into: missing from global (`_mis`), different decimals (`_dif`), or matched/global-only (`_updated`).
   - For missing PARAMCDs, assigns study decimal as the precision (when `deci_update=Y`).
   - For differing decimals, takes the maximum of global and study decimal values.
4. **Step 4 — Output Generation**
   - Creates the final `<lookup_glb>_updated` dataset with retained variable order.
   - Generates WARNING messages listing any missing or differing PARAMCDs.
5. **Step 5 — Cleanup**
   - Temporary sorted datasets (`_lookup_glb`, `_lookup_loc`) remain in WORK (no explicit cleanup).

## 7. Validation & Error Handling

| Check | Condition | Action |
|-------|-----------|--------|
| Global table existence | `%sysfunc(exist())` returns false | Outputs WARNING and skips all processing |
| Local table existence | `%sysfunc(exist())` returns false | Outputs WARNING and skips merge |
| PARCAT1 presence | `%sysfunc(varnum())` returns 0 | Excludes PARCAT1 from BY statements and variable lists |
| Missing PARAMCDs | Records in local but not global | Outputs WARNING listing missing PARAMCDs |
| Differing decimals | `MAX_DECIMAL_LENGTH ne STUDY_DECIMAL` | Outputs WARNING listing affected PARAMCDs |

## 8. Dependencies

- **Other Macros Called:** `%is_empty()` (utility macro defined in the same file), `%sysfunc()`, `%upcase()`
- **External Files:** Study lookup tables created by `m_stats_calc.sas`
- **SAS Products Required:** Base SAS 9.4

## 9. Example Usage

```sas
libname lookup_d '/Biometrics/standards/global/2025val/data_archive/lookup';
libname lookup_l '/Biometrics/dev2026/c3g310/csr/macros/LookUpTable';

%m_global_lookup(
  lookupdir_glb = lookup_d,
  lookupdir_loc = lookup_l,
  lookup_glb    = PRECISION,
  lookup_loc    = PRECISION_e,
  deci_update   = Y
);
```

## 10. Modification History

| Date | Author | Version | Description |
|------|--------|---------|-------------|
| 06FEB2026 | FY | 1.0 | Create Global LookUp Table from study LookUp Tables |
| 09APR2026 | FY | 1.1 | Check PARCAT1 existence in local table; add PARAM to merge BY variables |
| 10APR2026 | FY | 1.2 | Set explicit lengths for PARCAT1($200), PARAMCD($8), UPDATE_ID, STUDYID, DATASET_NAME, PARAM($200) |
