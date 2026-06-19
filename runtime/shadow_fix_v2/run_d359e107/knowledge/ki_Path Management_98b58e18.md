# Knowledge Item: Golden Rule: Use Relative Paths in Scripts

- **Source**: 60345d04-07a6-4812-bbe5-18e270df66b9
- **Date**: 2026-06-12T22:23:17.980224+00:00

## Lessons Learned
- Migrate all legacy files before updating associated indexes.
- Validate that every file reference is correctly updated after migration.
- Prefer relative paths over hard‑coded absolute paths to keep scripts portable.
- Test migration scripts in multiple environments to ensure path independence.

## Anti-Patterns
- Hardcoding absolute file paths inside migration scripts.