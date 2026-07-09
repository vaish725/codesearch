"""
Python AST-based symbol extraction.

Extracts symbols from Python files using the built-in ast module.
"""

import ast
from dataclasses import dataclass
from typing import List, Optional, Union
from pathlib import Path


@dataclass
class Symbol:
    """Represents an extracted symbol."""

    name: str
    kind: str  # class, function, method, import
    start_line: int
    end_line: int
    signature: Optional[str] = None


class PythonASTExtractor:
    """
    Extracts symbols from Python source code using AST parsing.
    """

    def extract_from_file(self, file_path: Path) -> List[Symbol]:
        """
        Extract symbols from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of extracted symbols
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.extract_from_source(content)
        except Exception:
            # Log error and return empty list
            return []

    def extract_from_source(self, source: str) -> List[Symbol]:
        """
        Extract symbols from Python source code.

        Args:
            source: Python source code as string

        Returns:
            List of extracted symbols
        """
        symbols: List[Symbol] = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Return empty list if parse fails
            return symbols

        # Walk the AST with context to distinguish methods from functions
        self._walk_ast(tree, symbols, parent_class=None)

        return symbols

    def _walk_ast(self, node: ast.AST, symbols: List[Symbol], parent_class: Optional[str] = None):
        """
        Walk the AST tree and extract symbols with context.

        Args:
            node: Current AST node
            symbols: List to accumulate symbols
            parent_class: Name of parent class (for method detection)
        """
        if isinstance(node, ast.ClassDef):
            # Extract class symbol
            class_symbol = self._extract_class(node)
            if class_symbol:
                symbols.append(class_symbol)

            # Walk class body to find methods
            for child in node.body:
                self._walk_ast(child, symbols, parent_class=node.name)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Determine if it's a method or function
            if parent_class:
                method_symbol = self._extract_method(node, parent_class)
                if method_symbol:
                    symbols.append(method_symbol)
            else:
                function_symbol = self._extract_function(node)
                if function_symbol:
                    symbols.append(function_symbol)

        elif isinstance(node, ast.Import):
            # Extract import symbols
            for alias in node.names:
                import_symbol = self._extract_import(alias.name, node.lineno)
                if import_symbol:
                    symbols.append(import_symbol)

        elif isinstance(node, ast.ImportFrom):
            # Extract from imports
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    # from module import *
                    import_symbol = Symbol(
                        name=f"{module}.*" if module else "*",
                        kind="import",
                        start_line=node.lineno,
                        end_line=node.lineno,
                    )
                    symbols.append(import_symbol)
                else:
                    # from module import name
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    import_symbol = self._extract_import(full_name, node.lineno)
                    if import_symbol:
                        symbols.append(import_symbol)

        else:
            # Continue walking for other node types
            for child_node in ast.iter_child_nodes(node):
                self._walk_ast(child_node, symbols, parent_class=parent_class)

    def _extract_class(self, node: ast.ClassDef) -> Optional[Symbol]:
        """Extract a class symbol."""
        end_line = getattr(node, "end_lineno", node.lineno)

        # Build signature with base classes
        bases = [self._get_name(base) for base in node.bases]
        if bases:
            signature = f"class {node.name}({', '.join(bases)})"
        else:
            signature = f"class {node.name}"

        return Symbol(
            name=node.name,
            kind="class",
            start_line=node.lineno,
            end_line=end_line,
            signature=signature,
        )

    def _extract_function(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Optional[Symbol]:
        """Extract a function symbol."""
        end_line = getattr(node, "end_lineno", node.lineno)
        signature = self._build_function_signature(node)

        return Symbol(
            name=node.name,
            kind="function",
            start_line=node.lineno,
            end_line=end_line,
            signature=signature,
        )

    def _extract_method(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], class_name: str
    ) -> Optional[Symbol]:
        """Extract a method symbol."""
        end_line = getattr(node, "end_lineno", node.lineno)
        signature = self._build_function_signature(node)

        return Symbol(
            name=f"{class_name}.{node.name}",
            kind="method",
            start_line=node.lineno,
            end_line=end_line,
            signature=signature,
        )

    def _extract_import(self, module_name: str, lineno: int) -> Optional[Symbol]:
        """Extract an import symbol."""
        return Symbol(
            name=module_name,
            kind="import",
            start_line=lineno,
            end_line=lineno,
        )

    def _build_function_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """
        Build a function signature string.

        Args:
            node: Function or async function node

        Returns:
            Signature string like "def foo(a, b, *args, **kwargs)"
        """
        args_parts = []
        args = node.args

        # Regular arguments
        for i, arg in enumerate(args.args):
            arg_str = arg.arg
            # Add default value indicator if present
            default_offset = len(args.args) - len(args.defaults)
            if i >= default_offset:
                arg_str += "=..."
            args_parts.append(arg_str)

        # *args
        if args.vararg:
            args_parts.append(f"*{args.vararg.arg}")

        # Keyword-only arguments
        for i, arg in enumerate(args.kwonlyargs):
            arg_str = arg.arg
            if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
                arg_str += "=..."
            args_parts.append(arg_str)

        # **kwargs
        if args.kwarg:
            args_parts.append(f"**{args.kwarg.arg}")

        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        return f"{prefix} {node.name}({', '.join(args_parts)})"

    def _get_name(self, node: ast.AST) -> str:
        """
        Get the name from a node (for base classes, etc).

        Args:
            node: AST node

        Returns:
            Name string or empty string
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle cases like BaseClass.SubClass
            value_name = self._get_name(node.value)
            return f"{value_name}.{node.attr}" if value_name else node.attr
        else:
            return ""
