# Slice IDE Platform

Python backend building blocks for dependency-aware code-context slicing. This repository currently contains parser, graph, slicing, soundness, and configuration modules. It does **not** yet include a runnable HTTP API, VS Code extension, or JetBrains plugin.

## Implemented

- Python AST symbol parsing and dependency-graph construction.
- Configurable callee/caller traversal depths, including zero-depth slices.
- Type/global references, source rendering, and static soundness diagnostics.
- `SliceResult.to_dict()` returns an independent, JSON-serializable report for future IDE clients.
- `symbols_in_order()` returns a copy, so consumers cannot mutate report ordering.

## Test

The core tests use the Python standard library:

```sh
python3 -m unittest discover -s tests -v
```

Run this command from the repository root. Optional service dependencies are listed in `backend/requirements.txt`; the core tests do not require a web server.

## Integration example

```python
import json
from backend.slicer import slice_for

# graph is a backend.graph.RepoGraph built from parsed Python modules.
# result = slice_for(graph, 'package.module.function', callee_depth=2)
# print(json.dumps(result.to_dict(), indent=2))
```

The commented lines require a populated graph and a real symbol ID; they are an integration sketch, not a server quickstart.

## Limits and next steps

Dynamic Python behavior can defeat static analysis. Inspect `sound`, `unsound_reasons`, and `unresolved` rather than treating a small slice as proof of complete coverage. Other-language parsers, a service endpoint, IDE extensions, and session integration remain future work.

## License

MIT. See [LICENSE](LICENSE).
