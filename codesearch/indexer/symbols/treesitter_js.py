"""
Regex-based symbol extraction for JavaScript/TypeScript.

Extracts symbols from JS/TS files using regex patterns.
Note: This is a pragmatic regex-based approach rather than full Tree-sitter parsing.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class Symbol:
    """Represents an extracted symbol."""

    name: str
    kind: str  # class, function, method, import, export
    start_line: int
    end_line: int
    signature: Optional[str] = None


class JSSymbolExtractor:
    """
    Extracts symbols from JavaScript/TypeScript using regex patterns.

    Supports:
    - Function declarations (function foo() {})
    - Arrow functions (const foo = () => {})
    - Class declarations
    - Methods in classes
    - Import statements (import, require)
    - Export statements
    """

    # Regex patterns for JS/TS constructs
    FUNCTION_DECL = re.compile(
        r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\((.*?)\)", re.MULTILINE
    )

    ARROW_FUNCTION = re.compile(
        r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>",
        re.MULTILINE,
    )

    CLASS_DECL = re.compile(r"^\s*(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?", re.MULTILINE)

    METHOD_DECL = re.compile(
        r"^\s*(?:async\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*[^{]+)?\s*\{", re.MULTILINE
    )

    IMPORT_STMT = re.compile(
        r'^\s*import\s+(?:{([^}]+)}|(\w+)|\*\s+as\s+(\w+))\s+from\s+[\'"]([^\'"]+)[\'"]',
        re.MULTILINE,
    )

    REQUIRE_STMT = re.compile(
        r'(?:const|let|var)\s+(?:{([^}]+)}|(\w+))\s*=\s*require\s*\([\'"]([^\'"]+)[\'"]\)',
        re.MULTILINE,
    )

    EXPORT_STMT = re.compile(
        r"^\s*export\s+(?:default\s+)?(?:class|function|const|let|var)?\s+(\w+)", re.MULTILINE
    )

    def extract_from_file(self, file_path: Path) -> List[Symbol]:
        """
        Extract symbols from a JS/TS file.

        Args:
            file_path: Path to JS/TS file

        Returns:
            List of extracted symbols
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.extract_from_source(content)
        except Exception:
            return []

    def extract_from_source(self, source: str) -> List[Symbol]:
        """
        Extract symbols from JS/TS source code.

        Args:
            source: JS/TS source code as string

        Returns:
            List of extracted symbols
        """
        symbols = []
        lines = source.split("\n")

        # Extract functions
        symbols.extend(self._extract_functions(source, lines))

        # Extract arrow functions
        symbols.extend(self._extract_arrow_functions(source, lines))

        # Extract classes and methods
        symbols.extend(self._extract_classes_and_methods(source, lines))

        # Extract imports
        symbols.extend(self._extract_imports(source, lines))

        return symbols

    def _extract_functions(self, source: str, lines: List[str]) -> List[Symbol]:
        """Extract function declarations."""
        symbols = []
        for match in self.FUNCTION_DECL.finditer(source):
            name = match.group(1)
            params = match.group(2)
            line_num = source[: match.start()].count("\n") + 1

            # Check if async
            full_match = match.group(0)
            is_async = "async" in full_match
            prefix = "async function" if is_async else "function"

            signature = f"{prefix} {name}({params})"

            symbols.append(
                Symbol(
                    name=name,
                    kind="function",
                    start_line=line_num,
                    end_line=line_num,  # Simplified
                    signature=signature,
                )
            )

        return symbols

    def _extract_arrow_functions(self, source: str, lines: List[str]) -> List[Symbol]:
        """Extract arrow function expressions."""
        symbols = []
        for match in self.ARROW_FUNCTION.finditer(source):
            name = match.group(1)
            params = match.group(2)
            line_num = source[: match.start()].count("\n") + 1

            # Check if async
            full_match = match.group(0)
            is_async = "async" in full_match
            prefix = "async" if is_async else "const"

            signature = f"{prefix} {name} = ({params}) =>"

            symbols.append(
                Symbol(
                    name=name,
                    kind="function",
                    start_line=line_num,
                    end_line=line_num,
                    signature=signature,
                )
            )

        return symbols

    def _extract_classes_and_methods(self, source: str, lines: List[str]) -> List[Symbol]:
        """Extract classes and their methods."""
        symbols = []

        # Find all classes
        for class_match in self.CLASS_DECL.finditer(source):
            class_name = class_match.group(1)
            extends = class_match.group(2)
            class_line = source[: class_match.start()].count("\n") + 1

            # Build class signature
            if extends:
                signature = f"class {class_name} extends {extends}"
            else:
                signature = f"class {class_name}"

            symbols.append(
                Symbol(
                    name=class_name,
                    kind="class",
                    start_line=class_line,
                    end_line=class_line,  # Simplified
                    signature=signature,
                )
            )

            # Find methods within this class
            # Look for the class body
            class_end = class_match.end()
            # Find the opening brace
            brace_start = source.find("{", class_end)
            if brace_start == -1:
                continue

            # Find matching closing brace (simplified - just look ahead ~500 chars)
            class_body_end = min(brace_start + 5000, len(source))
            class_body = source[brace_start:class_body_end]

            # Extract methods
            for method_match in self.METHOD_DECL.finditer(class_body):
                method_name = method_match.group(1)
                params = method_match.group(2)

                # Skip constructor (already implied by class)
                if method_name in ["constructor", "if", "for", "while", "switch", "catch"]:
                    continue

                method_line = source[: brace_start + method_match.start()].count("\n") + 1

                # Check if async
                full_method = method_match.group(0)
                is_async = "async" in full_method
                prefix = "async" if is_async else ""

                signature = f"{prefix} {method_name}({params})".strip()

                symbols.append(
                    Symbol(
                        name=f"{class_name}.{method_name}",
                        kind="method",
                        start_line=method_line,
                        end_line=method_line,
                        signature=signature,
                    )
                )

        return symbols

    def _extract_imports(self, source: str, lines: List[str]) -> List[Symbol]:
        """Extract import statements."""
        symbols = []

        # ES6 imports
        for match in self.IMPORT_STMT.finditer(source):
            named_imports = match.group(1)  # { foo, bar }
            default_import = match.group(2)  # import Foo
            namespace_import = match.group(3)  # import * as Foo
            module = match.group(4)
            line_num = source[: match.start()].count("\n") + 1

            if named_imports:
                # Handle multiple named imports
                names = [n.strip() for n in named_imports.split(",")]
                for name in names:
                    if name:
                        symbols.append(
                            Symbol(
                                name=f"{module}.{name}",
                                kind="import",
                                start_line=line_num,
                                end_line=line_num,
                            )
                        )
            elif default_import:
                symbols.append(
                    Symbol(name=module, kind="import", start_line=line_num, end_line=line_num)
                )
            elif namespace_import:
                symbols.append(
                    Symbol(
                        name=f"{module}.*", kind="import", start_line=line_num, end_line=line_num
                    )
                )

        # CommonJS require
        for match in self.REQUIRE_STMT.finditer(source):
            destructured = match.group(1)
            name = match.group(2)
            module = match.group(3)
            line_num = source[: match.start()].count("\n") + 1

            if destructured:
                names = [n.strip() for n in destructured.split(",")]
                for n in names:
                    if n:
                        symbols.append(
                            Symbol(
                                name=f"{module}.{n}",
                                kind="import",
                                start_line=line_num,
                                end_line=line_num,
                            )
                        )
            elif name:
                symbols.append(
                    Symbol(name=module, kind="import", start_line=line_num, end_line=line_num)
                )

        return symbols
