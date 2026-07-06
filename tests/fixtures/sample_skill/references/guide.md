# Advanced CSV guide

## Deduplication

Use `df.drop_duplicates(subset=[...], keep="first")`. Always log how many rows were
removed so data loss is visible.

## Merging files

Use `pd.concat` for same-schema files and `pd.merge` for joins. Validate join keys
with `validate="one_to_one"` where applicable.
