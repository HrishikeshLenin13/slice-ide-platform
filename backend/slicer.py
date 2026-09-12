"""Core slicing logic: compute minimal context for a target symbol."""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional

from .parser import Symbol
from .graph import RepoGraph


@dataclass
class SliceResult:
    """Result of a slice computation."""
    target: str
    included: List[str]  # symbol ids in emission order
    callees: List[str]
    callers: List[str]
    type_refs: List[str]
    global_refs: List[str]
    sound: bool
    unsound_reasons: Dict[str, List[str]] = field(default_factory=dict)
    unresolved: Dict[str, List[str]] = field(default_factory=dict)

    def symbols_in_order(self) -> List[str]:
        """Get included symbols in order."""
        return self.included


def slice_for(
    graph: RepoGraph,
    target_id: str,
    *,
    callee_depth: Optional[int] = None,
    caller_depth: int = 1,
) -> SliceResult:
    """Compute minimal slice for a target symbol."""
    if target_id not in graph.symbols:
        raise KeyError(f"unknown symbol: {target_id!r}")

    # Compute callees
    callees: Set[str] = set()
    frontier = {target_id}
    depth = 0
    while frontier:
        if callee_depth is not None and depth >= callee_depth:
            break
        nxt: Set[str] = set()
        for sid in frontier:
            sym = graph.symbols[sid]
            for c in sym.calls:
                if c not in callees and c != target_id:
                    nxt.add(c)
        callees |= nxt
        frontier = nxt
        depth += 1

    # Compute callers
    callers: Set[str] = set()
    frontier = {target_id}
    depth = 0
    while frontier:
        if depth >= caller_depth:
            break
        nxt = set()
        for sid in frontier:
            for c in graph.callers.get(sid, set()):
                if c not in callers and c != target_id:
                    nxt.add(c)
        callers |= nxt
        frontier = nxt
        depth += 1

    # Compute type refs and global refs
    type_refs: Set[str] = set()
    global_refs: Set[str] = set()
    for sid in {target_id, *callees, *callers}:
        sym = graph.symbols[sid]
        type_refs |= sym.type_refs
        global_refs |= sym.global_refs
    
    # Include base classes
    changed = True
    while changed:
        changed = False
        for tid in list(type_refs):
            tsym = graph.symbols.get(tid)
            if tsym and tsym.kind == "class":
                new_bases = tsym.bases - type_refs
                if new_bases:
                    type_refs |= new_bases
                    changed = True

    # Build included list in order
    included_order = [target_id] + sorted(callees) + sorted(callers) + sorted(type_refs) + sorted(global_refs)
    seen = set()
    included = []
    for sid in included_order:
        if sid not in seen:
            seen.add(sid)
            included.append(sid)

    # Check soundness
    sound = True
    unsound_reasons: Dict[str, List[str]] = {}
    unresolved: Dict[str, List[str]] = {}
    for sid in included:
        if not graph.is_sound(sid):
            sound = False
            unsound_reasons[sid] = graph.soundness_reasons(sid)
        sym = graph.symbols[sid]
        if sym.unresolved_calls:
            unresolved[sid] = sorted(sym.unresolved_calls)

    return SliceResult(
        target=target_id,
        included=included,
        callees=sorted(callees),
        callers=sorted(callers),
        type_refs=sorted(type_refs),
        global_refs=sorted(global_refs),
        sound=sound,
        unsound_reasons=unsound_reasons,
        unresolved=unresolved,
    )


def render_slice(graph: RepoGraph, result: SliceResult, *, caller_signature_only: bool = True) -> str:
    """Render a slice as source code."""
    by_file: Dict[str, List[Symbol]] = {}
    for sid in result.included:
        sym = graph.symbols[sid]
        by_file.setdefault(sym.file_path, []).append(sym)

    parts = []
    for file_path in sorted(by_file):
        parts.append(f"# --- {file_path} ---")
        for sym in sorted(by_file[file_path], key=lambda s: s.lineno):
            tag = "TARGET" if sym.id == result.target else sym.kind.upper()
            src = sym.source
            if (
                caller_signature_only
                and sym.id in result.callers
                and sym.id != result.target
                and sym.kind in ("function", "method")
            ):
                first_line = src.splitlines()[0] if src else ""
                src = first_line + "\n    ...  # (caller body omitted; only the call site matters here)"
            parts.append(f"\n# [{tag}] {sym.id}\n{src}")
    return "\n".join(parts)
