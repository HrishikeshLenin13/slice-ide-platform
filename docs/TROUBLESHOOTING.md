# Troubleshooting slice-ide-platform

Use the smallest reproducible fixture before changing production data or configuration. Run commands from the repository root.

## A report fails to deserialize

Compare required fields with SliceResult.to_dict(). Do not silently drop unknown fields when crossing an API boundary.

## A caller body seems missing

Text rendering intentionally includes caller signatures only. Use source_units for full selected source and budget it accordingly.

## A batch fails for one missing target

Validate target IDs against graph.symbols first. The batch rejects missing targets before returning a partial result.

## Reproduce and report

1. Record the exact command or UI action, runtime version, expected result, and actual result.
2. Run the regression command below on the same checkout and keep its first failure, not only the final summary.
3. Reduce the issue to a deterministic fixture without personal data or credentials.
4. Include the affected source path from the [feature guide](RECENT_IMPROVEMENTS.md) and whether it reproduces on a clean checkout.

```sh
python3 -m unittest discover -s tests -v
```

## Recovery

Keep a copy of input data before experimenting. Revert the individual source change with Git and rerun the same fixture; a source revert does not automatically reverse browser storage, downloaded files, or external service state. Do not delete a lockfile or weaken a validation gate to make a failure disappear.
