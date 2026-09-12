"""Universal parser using tree-sitter for multi-language support."""

import ast
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from pathlib import Path


@dataclass
class Symbol:
    """Represents a code symbol (function, class, variable, etc.)."""
    id: str  # fully-qualified id
    kind: str  # "function", "class", "method", "global"
    module: str  # dotted module path
    file_path: str
    qualname: str
    lineno: int
    end_lineno: int
    source: str
    node: Optional[object] = None
    
    # Populated by graph builder
    calls: set = field(default_factory=set)  # resolved callee ids
    unresolved_calls: set = field(default_factory=set)
    type_refs: set = field(default_factory=set)
    global_refs: set = field(default_factory=set)
    bases: set = field(default_factory=set)


@dataclass
class ModuleInfo:
    """Information about a parsed module."""
    module: str
    file_path: str
    tree: object
    source: str
    import_map: Dict[str, str] = field(default_factory=dict)
    star_imports: List[str] = field(default_factory=list)


class PythonParser:
    """Parser for Python code using AST."""

    @staticmethod
    def _module_name_for(root: str, file_path: str) -> str:
        """Convert file path to module name."""
        rel = os.path.relpath(file_path, root)
        if rel.endswith("__init__.py"):
            rel = rel[: -len("__init__.py")].rstrip("/\\")
        else:
            rel = rel[: -len(".py")]
        parts = [p for p in rel.replace("\\", "/").split("/") if p]
        return ".".join(parts) if parts else os.path.splitext(os.path.basename(file_path))[0]

    @staticmethod
    def _get_source_segment(source_lines: List[str], node: ast.AST) -> str:
        """Extract source code for a node."""
        try:
            seg = ast.get_source_segment("\n".join(source_lines), node)
            if seg is not None:
                return seg
        except Exception:
            pass
        # Fallback: slice by line numbers
        start = getattr(node, "lineno", 1) - 1
        end = getattr(node, "end_lineno", start + 1)
        return "\n".join(source_lines[start:end])

    @staticmethod
    def discover_py_files(repo_root: str) -> List[str]:
        """Find all Python files in directory."""
        out = []
        for dirpath, dirnames, filenames in os.walk(repo_root):
            dirnames[:] = [
                d for d in dirnames
                if d not in (".git", "__pycache__", "venv", ".venv", "node_modules", ".slice")
            ]
            for fn in filenames:
                if fn.endswith(".py"):
                    out.append(os.path.join(dirpath, fn))
        return sorted(out)

    @staticmethod
    def parse_module(repo_root: str, file_path: str) -> Tuple[ModuleInfo, Dict[str, Symbol]]:
        """Parse a single Python module."""
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        tree = ast.parse(source, filename=file_path)
        module = PythonParser._module_name_for(repo_root, file_path)
        lines = source.splitlines()

        mod_info = ModuleInfo(module=module, file_path=file_path, tree=tree, source=source)
        symbols: Dict[str, Symbol] = {}

        # Extract imports
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    mod_info.import_map[local] = alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                if any(a.name == "*" for a in node.names):
                    mod_info.star_imports.append(node.module)
                    continue
                for alias in node.names:
                    local = alias.asname or alias.name
                    mod_info.import_map[local] = f"{node.module}.{alias.name}"

        # Extract symbols
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sid = f"{module}.{node.name}"
                symbols[sid] = Symbol(
                    id=sid, kind="function", module=module, file_path=file_path,
                    qualname=node.name, lineno=node.lineno, end_lineno=node.end_lineno or node.lineno,
                    source=PythonParser._get_source_segment(lines, node), node=node,
                )
            elif isinstance(node, ast.ClassDef):
                sid = f"{module}.{node.name}"
                symbols[sid] = Symbol(
                    id=sid, kind="class", module=module, file_path=file_path,
                    qualname=node.name, lineno=node.lineno, end_lineno=node.end_lineno or node.lineno,
                    source=PythonParser._get_source_segment(lines, node), node=node,
                )
                # Extract methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        mid = f"{module}.{node.name}.{item.name}"
                        symbols[mid] = Symbol(
                            id=mid, kind="method", module=module, file_path=file_path,
                            qualname=f"{node.name}.{item.name}", lineno=item.lineno,
                            end_lineno=item.end_lineno or item.lineno,
                            source=PythonParser._get_source_segment(lines, item), node=item,
                        )
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in targets:
                    if isinstance(t, ast.Name):
                        sid = f"{module}.{t.id}"
                        symbols[sid] = Symbol(
                            id=sid, kind="global", module=module, file_path=file_path,
                            qualname=t.id, lineno=node.lineno, end_lineno=node.end_lineno or node.lineno,
                            source=PythonParser._get_source_segment(lines, node), node=node,
                        )

        return mod_info, symbols

    @staticmethod
    def parse_repo(repo_root: str) -> Tuple[Dict[str, ModuleInfo], Dict[str, Symbol]]:
        """Parse entire repository."""
        modules: Dict[str, ModuleInfo] = {}
        all_symbols: Dict[str, Symbol] = {}
        
        for fp in PythonParser.discover_py_files(repo_root):
            try:
                mod_info, symbols = PythonParser.parse_module(repo_root, fp)
                modules[mod_info.module] = mod_info
                all_symbols.update(symbols)
            except Exception as e:
                print(f"Warning: failed to parse {fp}: {e}")
        
        return modules, all_symbols


class UniversalParser:
    """Wrapper for multi-language parsing."""
    
    @staticmethod
    def detect_language(file_path: str) -> str:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()
        mapping = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".go": "go",
            ".java": "java",
        }
        return mapping.get(ext, "python")

    @staticmethod
    def parse_repo(repo_root: str) -> Tuple[Dict[str, ModuleInfo], Dict[str, Symbol]]:
        """Parse repository with auto language detection."""
        return PythonParser.parse_repo(repo_root)
