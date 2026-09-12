"""Build dependency graph from parsed symbols."""

import ast
import builtins
from typing import Dict, Set, Callable, Optional, List

from .parser import Symbol, ModuleInfo
from .soundness import check_function, check_module_star_imports, SoundnessReport

BUILTIN_NAMES = set(dir(builtins))


def _flatten_annotation_names(node: Optional[ast.AST]) -> List[str]:
    """Extract all names from an annotation."""
    names: List[str] = []
    if node is None:
        return names
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.append(child.id)
        elif isinstance(child, ast.Attribute):
            names.append(child.attr)
    return names


def _assigned_names(fn_node: ast.AST) -> Set[str]:
    """Find all locally-assigned names in a function."""
    names: Set[str] = set()
    if isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for a in fn_node.args.args + fn_node.args.posonlyargs + fn_node.args.kwonlyargs:
            names.add(a.arg)
        if fn_node.args.vararg:
            names.add(fn_node.args.vararg.arg)
        if fn_node.args.kwarg:
            names.add(fn_node.args.kwarg.arg)
    
    for child in ast.walk(fn_node):
        if isinstance(child, ast.Assign):
            for t in child.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
        elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            names.add(child.target.id)
        elif isinstance(child, (ast.For, ast.AsyncFor)) and isinstance(child.target, ast.Name):
            names.add(child.target.id)
        elif isinstance(child, ast.comprehension) and isinstance(child.target, ast.Name):
            names.add(child.target.id)
        elif isinstance(child, ast.With):
            for item in child.items:
                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                    names.add(item.optional_vars.id)
    return names


def _local_type_hints(fn_node: ast.AST, resolve_name: Callable) -> Dict[str, str]:
    """Extract intra-procedural type hints."""
    hints: Dict[str, str] = {}

    if isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for a in list(fn_node.args.args) + list(fn_node.args.posonlyargs) + list(fn_node.args.kwonlyargs):
            if a.annotation is not None:
                for n in _flatten_annotation_names(a.annotation):
                    sid = resolve_name(n)
                    if sid:
                        hints[a.arg] = sid
                        break

    for child in ast.walk(fn_node):
        if isinstance(child, ast.Assign) and isinstance(child.value, ast.Call):
            callee = child.value.func
            if isinstance(callee, ast.Name):
                sid = resolve_name(callee.id)
                if sid:
                    for t in child.targets:
                        if isinstance(t, ast.Name):
                            hints[t.id] = sid
    return hints


class RepoGraph:
    """Dependency graph for a repository."""

    def __init__(self, modules: Dict[str, ModuleInfo], symbols: Dict[str, Symbol]):
        self.modules = modules
        self.symbols = symbols
        self.callers: Dict[str, Set[str]] = {sid: set() for sid in symbols}
        self.soundness: Dict[str, SoundnessReport] = {}
        self.module_soundness: Dict[str, SoundnessReport] = {}
        self._build()

    def _resolver_for(self, module: str) -> Callable:
        """Create a name resolver for a module."""
        mod_info = self.modules[module]

        def resolve_name(name: str) -> Optional[str]:
            local_id = f"{module}.{name}"
            if local_id in self.symbols:
                return local_id
            if name in mod_info.import_map:
                target = mod_info.import_map[name]
                if target in self.symbols:
                    return target
                return None
            return None

        return resolve_name

    def _class_owner(self, sym: Symbol) -> Optional[Symbol]:
        """Get the class that owns a method."""
        if sym.kind != "method":
            return None
        class_id = f"{sym.module}.{sym.qualname.split('.')[0]}"
        return self.symbols.get(class_id)

    def _build(self) -> None:
        """Build the complete dependency graph."""
        # Check module-level soundness
        for module, mod_info in self.modules.items():
            self.module_soundness[module] = check_module_star_imports(mod_info.star_imports)

        # Resolve symbols
        for sid, sym in self.symbols.items():
            resolve_name = self._resolver_for(sym.module)

            if sym.kind == "class":
                # Extract base classes
                for base in sym.node.bases:
                    base_names = _flatten_annotation_names(base)
                    for bn in base_names:
                        resolved = resolve_name(bn)
                        if resolved:
                            sym.bases.add(resolved)
                            sym.type_refs.add(resolved)
                continue

            if sym.kind == "global":
                continue

            # Function or method
            self.soundness[sid] = check_function(sym.node)

            local_names = _assigned_names(sym.node)
            local_type_hints = _local_type_hints(sym.node, resolve_name)
            owner_class = self._class_owner(sym)

            # Extract annotations
            fn = sym.node
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for a in list(fn.args.args) + list(fn.args.posonlyargs) + list(fn.args.kwonlyargs):
                    for n in _flatten_annotation_names(a.annotation):
                        r = resolve_name(n)
                        if r and self.symbols[r].kind == "class":
                            sym.type_refs.add(r)
                for n in _flatten_annotation_names(fn.returns):
                    r = resolve_name(n)
                    if r and self.symbols[r].kind == "class":
                        sym.type_refs.add(r)

            # Walk AST and resolve references
            for child in ast.walk(sym.node):
                # Function calls
                if isinstance(child, ast.Call):
                    callee = child.func
                    target_id = None

                    if isinstance(callee, ast.Name):
                        target_id = resolve_name(callee.id)
                        if target_id is None and callee.id not in local_names and callee.id not in BUILTIN_NAMES:
                            sym.unresolved_calls.add(callee.id)

                    elif isinstance(callee, ast.Attribute):
                        if isinstance(callee.value, ast.Name) and callee.value.id == "self" and owner_class:
                            mid = f"{sym.module}.{owner_class.qualname}.{callee.attr}"
                            if mid in self.symbols:
                                target_id = mid
                            else:
                                for base_id in owner_class.bases:
                                    base_sym = self.symbols.get(base_id)
                                    if base_sym:
                                        cand = f"{base_sym.module}.{base_sym.qualname}.{callee.attr}"
                                        if cand in self.symbols:
                                            target_id = cand
                                            break
                                if target_id is None:
                                    sym.unresolved_calls.add(f"self.{callee.attr}")
                        elif isinstance(callee.value, ast.Name) and callee.value.id in local_type_hints:
                            base_sym = self.symbols[local_type_hints[callee.value.id]]
                            cand = f"{base_sym.module}.{base_sym.qualname}.{callee.attr}"
                            if cand in self.symbols:
                                target_id = cand
                            else:
                                sym.unresolved_calls.add(f"{callee.value.id}.{callee.attr}")
                        else:
                            name_hint = getattr(callee.value, "id", "<expr>")
                            sym.unresolved_calls.add(f"{name_hint}.{callee.attr}")

                    if target_id:
                        target_sym = self.symbols[target_id]
                        if target_sym.kind == "class":
                            sym.type_refs.add(target_id)
                        else:
                            sym.calls.add(target_id)
                            self.callers.setdefault(target_id, set()).add(sid)

                # Global variable reads
                elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    if child.id not in local_names:
                        gid = resolve_name(child.id)
                        if gid and self.symbols[gid].kind == "global":
                            sym.global_refs.add(gid)

    def is_sound(self, sid: str) -> bool:
        """Check if a symbol is sound."""
        sym = self.symbols.get(sid)
        if sym is None:
            return False
        if sym.kind in ("function", "method"):
            rep = self.soundness.get(sid)
            if rep and not rep.sound:
                return False
        if self.module_soundness.get(sym.module) and not self.module_soundness[sym.module].sound:
            return False
        return True

    def soundness_reasons(self, sid: str) -> List[str]:
        """Get reasons why a symbol is unsound."""
        sym = self.symbols.get(sid)
        if sym is None:
            return [f"unknown symbol: {sid}"]
        reasons = []
        rep = self.soundness.get(sid)
        if rep:
            reasons += rep.reasons
        mrep = self.module_soundness.get(sym.module)
        if mrep:
            reasons += mrep.reasons
        return reasons
