# Reusable validated slicing reports

This guide covers implemented behavior. It does not change deployment or account configuration.

## Usage

```python
from backend.parser import PythonParser
from backend.graph import RepoGraph
from backend.slicer import slice_many, SliceResult, source_units
graph = RepoGraph(*PythonParser.parse_repo('.'))
# Replace targets with IDs present in graph.symbols.
targets = list(graph.symbols)[:2]
for target, result in slice_many(graph, targets).items():
    restored = SliceResult.from_dict(result.to_dict())
    print(target, restored.summary(), len(source_units(graph, restored)))
```

## Contracts and limits

- from_dict validates report shape and deep-copies list metadata. Unknown fields and malformed required fields are rejected.
- summary returns counts rather than exposing mutable internal member lists.
- Rendered caller context preserves complete multiline signatures while omitting caller bodies. source_units deliberately returns full selected source for consumers that require it.
- slice_many validates targets and depths before computation, deduplicates in request order, and reuses a parsed graph. It does not cache across source edits.

## Source map

- [`backend/slicer.py`](../backend/slicer.py)
<!-- source: backend/slicer.py -->
- [`tests/test_api_round2.py`](../tests/test_api_round2.py)
<!-- source: tests/test_api_round2.py -->
- [`backend/parser.py`](../backend/parser.py)
<!-- source: backend/parser.py -->

## Regression command

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

