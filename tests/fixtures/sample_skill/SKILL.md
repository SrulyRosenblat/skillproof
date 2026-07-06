---
name: csv-wrangler
description: Clean, transform, and summarize CSV files with pandas.
---

# CSV Wrangler

## Overview

This skill covers reliable CSV processing: loading messy files, cleaning columns,
and producing summary statistics.

## Loading messy CSVs

Always load with explicit options to survive malformed rows:

```python
import pandas as pd
df = pd.read_csv("input.csv", on_bad_lines="skip", encoding="utf-8")
```

Strip whitespace from headers immediately: `df.columns = df.columns.str.strip()`.

## Cleaning columns

Convert numeric columns defensively with `pd.to_numeric(col, errors="coerce")`,
then decide explicitly how to treat NaNs. Never silently drop rows.

## Summarizing

Produce summaries with `df.describe()` and group-level aggregates with
`df.groupby(key).agg(...)`. Write outputs with `df.to_csv(path, index=False)`.
