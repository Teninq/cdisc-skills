# CDISC Programming Reference Guide

Lightweight reference for generating correct clinical data code. Always query the CDISC Library API for authoritative variable definitions before writing code.

## SDTM Data Model

### Observation Class Hierarchy

SDTM organizes domains by observation class:

| Class | Description | Example Domains |
|-------|-------------|-----------------|
| **Interventions** | Treatments administered | CM, EX, SU |
| **Events** | Discrete occurrences | AE, DS, MH, CE |
| **Findings** | Measurements/observations | LB, VS, EG, PE, QS |
| **Special Purpose** | Subject-level and cross-domain | DM, SE, SV |
| **Relationship** | Links between records | RELREC, SUPPQUAL |
| **Trial Design** | Study design metadata | TA, TE, TI, TS, TV |

### Standard Variable Prefixes

Domain-specific variables use the two-letter domain code as prefix:

- `AE` domain: `AETERM`, `AEDECOD`, `AESTDTC`, `AEENDTC`, `AESEV`, `AESER`
- `LB` domain: `LBTESTCD`, `LBTEST`, `LBORRES`, `LBORRESU`, `LBSTRESC`, `LBSTRESN`
- `VS` domain: `VSTESTCD`, `VSTEST`, `VSORRES`, `VSORRESU`, `VSSTRESN`, `VSSTRESU`

### Key Identifier Variables

Every SDTM dataset includes these identifiers:

| Variable | Description | Required |
|----------|-------------|----------|
| `STUDYID` | Study Identifier | Required |
| `DOMAIN` | Two-character domain abbreviation | Required |
| `USUBJID` | Unique Subject Identifier (STUDYID + SITEID + SUBJID) | Required |
| `--SEQ` | Sequence Number (e.g., `AESEQ`, `LBSEQ`) | Required |

### Timing Variables

SDTM uses ISO 8601 format for dates:

| Variable | Format | Example |
|----------|--------|---------|
| `--DTC` (e.g., `AESTDTC`) | ISO 8601 | `2024-03-15T10:30:00` |
| `--DY` (e.g., `AESTDY`) | Integer (study day) | `15` |
| `--STRF` / `--ENRF` | Relative to reference period | `BEFORE`, `DURING`, `AFTER` |

## ADaM Data Model

### Core Data Structures

| Structure | Purpose | Key Feature |
|-----------|---------|-------------|
| **ADSL** | Subject-Level Analysis | One row per subject, all baseline and demographic variables |
| **BDS** | Basic Data Structure | One row per subject per parameter per analysis timepoint |
| **OCCDS** | Occurrence Data Structure | One row per subject per event occurrence |
| **ADTTE** | Time-to-Event | One row per subject per analysis parameter |

### Key ADaM Variables

#### ADSL (Subject-Level)

| Variable | Description |
|----------|-------------|
| `USUBJID` | Unique Subject Identifier |
| `SITEID` | Study Site Identifier |
| `ARM` / `ARMCD` | Planned treatment arm |
| `TRT01P` / `TRT01A` | Planned / actual treatment for period 01 |
| `AGEGR1` | Pooled age group |
| `RACE` | Race |
| `SEX` | Sex |
| `SAFFL` | Safety Population Flag (Y/N) |
| `ITTFL` | Intent-to-Treat Population Flag (Y/N) |
| `RANDFL` | Randomized Population Flag (Y/N) |

#### BDS (Basic Data Structure)

| Variable | Description |
|----------|-------------|
| `PARAMCD` | Parameter Code (short) |
| `PARAM` | Parameter (descriptive) |
| `AVAL` | Analysis Value (numeric) |
| `AVALC` | Analysis Value (character) |
| `BASE` | Baseline Value |
| `CHG` | Change from Baseline (AVAL - BASE) |
| `PCHG` | Percent Change from Baseline |
| `AVISIT` | Analysis Visit |
| `AVISITN` | Analysis Visit (numeric) |
| `ADT` | Analysis Date |
| `DTYPE` | Derivation Type (e.g., LOCF, WOCF) |
| `ANL01FL` | Analysis Record Flag 01 |

### Traceability Variables

| Variable | Description |
|----------|-------------|
| `SRCDOM` | Source domain |
| `SRCVAR` | Source variable |
| `SRCSEQ` | Source sequence number |

## Controlled Terminology

### Codelist-to-Variable Binding

Each SDTM/ADaM variable may be bound to a CDISC Controlled Terminology codelist. Query the API to verify:

1. Which codelist applies: query the variable definition and check for codelist reference.
2. Valid values: use `codelist-terms` to get the allowed submission values.

### Submission Value vs Decoded Value

| Concept | Example |
|---------|---------|
| **Submission Value** (`AESEV`) | `MILD`, `MODERATE`, `SEVERE` |
| **Decoded Value** (`AESEVCD`) | Numeric or coded equivalent |

Always use the **Submission Value** in datasets unless the variable definition specifies otherwise.

## Code Patterns

### Reading/Writing XPT (SAS Transport) Files

#### SAS

```sas
/* Read XPT */
libname xptdata xport '/path/to/ae.xpt';
data work.ae;
  set xptdata.ae;
run;

/* Write XPT */
libname xptout xport '/path/to/ae.xpt';
proc copy in=work out=xptout;
  select ae;
run;
```

#### R

```r
# Read XPT (haven package)
library(haven)
ae <- read_xpt("ae.xpt")

# Write XPT
write_xpt(ae, "ae.xpt")
```

#### Python

```python
# Read XPT (pandas)
import pandas as pd
ae = pd.read_sas("ae.xpt", format="xport")

# Write XPT (xport package)
import xport.v5
with open("ae.xpt", "wb") as f:
    xport.v5.dump([ae], f)
```

### Common Derivation Patterns

#### Derive Study Day (--DY)

```sas
/* SAS: Study day from reference date */
if nmiss(adt, rfstdtc_n) = 0 then do;
  if adt >= rfstdtc_n then --dy = adt - rfstdtc_n + 1;
  else --dy = adt - rfstdtc_n;
end;
```

#### Derive Change from Baseline (CHG)

```sas
/* SAS: Change from baseline in BDS */
if nmiss(aval, base) = 0 then chg = aval - base;
```

```r
# R: Change from baseline
adlb <- adlb %>%
  group_by(USUBJID, PARAMCD) %>%
  mutate(CHG = AVAL - BASE)
```

#### Merge ADSL Variables into BDS

```sas
/* SAS: Standard ADSL merge */
proc sort data=adsl; by usubjid; run;
proc sort data=adlb; by usubjid; run;
data adlb;
  merge adlb (in=a) adsl (keep=usubjid trt01p trt01a saffl ittfl);
  by usubjid;
  if a;
run;
```

```r
# R: Standard ADSL merge
adlb <- adlb %>%
  left_join(
    adsl %>% select(USUBJID, TRT01P, TRT01A, SAFFL, ITTFL),
    by = "USUBJID"
  )
```
