"""Detection of dynamic constructs that break static analysis."""

import ast
from dataclasses import dataclass, field
from typing import List

DYNAMIC_BUILTINS = {"eval", "exec", "getattr", "setattr", "delattr", "globals", "locals", "vars"}
DYNAMIC_ATTR_HOOKS = {"__getattr__", "__setattr__", "__getattribute__", "__call__"}
DYNAMIC_IMPORT_CALLS = {"import_module", "__import__"}


@dataclass
class SoundnessReport:
    """Result of soundness check."""
    sound: bool = True
    reasons: List[str] = field(default_factory=list)

    def flag(self, reason: str) -> None:
        """Mark as unsound with a reason."""
        self.sound = False
        self.reasons.append(reason)


def check_function(node: ast.AST) -> SoundnessReport:
    """Check if a function has dynamic constructs."""
    report = SoundnessReport()

    # Find dispatch table patterns
    subscript_bound_names: set = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Assign) and isinstance(child.value, ast.Subscript):
            for t in child.targets:
                if isinstance(t, ast.Name):
                    subscript_bound_names.add(t.id)

    # Check for dynamic constructs
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            callee = child.func
            if isinstance(callee, ast.Name) and callee.id in DYNAMIC_BUILTINS:
                report.flag(
                    f"call to builtin `{callee.id}()` at line {child.lineno} "
                    f"— target is not statically knowable"
                )
            if isinstance(callee, ast.Attribute) and callee.attr in DYNAMIC_IMPORT_CALLS:
                report.flag(f"dynamic import via `.{callee.attr}()` at line {child.lineno}")
            if isinstance(callee, ast.Subscript):
                report.flag(
                    f"call through a computed/subscripted callable at line {child.lineno} "
                    f"(e.g. dispatch table) — target not statically fixed"
                )
            if isinstance(callee, ast.Name) and callee.id in subscript_bound_names:
                report.flag(
                    f"call to `{callee.id}()` at line {child.lineno} whose value came "
                    f"from a subscript lookup (dispatch table) — target not statically fixed"
                )

        if isinstance(child, ast.FunctionDef) and child.name in DYNAMIC_ATTR_HOOKS:
            report.flag(
                f"defines `{child.name}` at line {child.lineno} — attribute "
                f"access on instances of this class is not statically resolvable"
            )

    return report


def check_module_star_imports(star_imports: List[str]) -> SoundnessReport:
    """Check for unresolvable star imports."""
    report = SoundnessReport()
    for mod in star_imports:
        report.flag(
            f"`from {mod} import *` — names entering this module's "
            f"namespace are not statically enumerable"
        )
    return report
