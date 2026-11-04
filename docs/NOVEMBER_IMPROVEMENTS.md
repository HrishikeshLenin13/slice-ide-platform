# Python source extraction

Nested tuple/list unpacking and starred targets now produce module-level global symbols. Attribute and subscription stores are not misidentified as new globals. Source spans and existing chained assignments are preserved.

Relative imports now resolve against their actual package, including `from . import module`, aliases, parent-package imports and package initializers. Imports beyond the known repository package hierarchy remain unresolved rather than inventing a target.

PythonParser and UniversalParser accept an optional `diagnostics` list. Failed files produce serializable filename/kind/message records in that collector without contaminating stdout; successful files remain available. Default warning behavior is retained.
