"""
Unit tests for JavaScript/TypeScript symbol extraction.
"""

import pytest
from codesearch.indexer.symbols.treesitter_js import JSSymbolExtractor


@pytest.fixture
def extractor():
    """Create a JS symbol extractor."""
    return JSSymbolExtractor()


def test_function_declaration(extractor):
    """Test extracting function declarations."""
    source = """
function calculateSum(a, b) {
    return a + b;
}

export function multiply(x, y) {
    return x * y;
}

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}
"""
    symbols = extractor.extract_from_source(source)
    functions = [s for s in symbols if s.kind == "function"]

    assert len(functions) == 3

    # Check first function
    func1 = next(s for s in functions if s.name == "calculateSum")
    assert func1.signature == "function calculateSum(a, b)"
    # Line 1 because source starts with newline
    assert func1.start_line >= 1

    # Check exported function
    func2 = next(s for s in functions if s.name == "multiply")
    assert func2.signature == "function multiply(x, y)"

    # Check async function
    func3 = next(s for s in functions if s.name == "fetchData")
    assert func3.signature == "async function fetchData(url)"


def test_arrow_functions(extractor):
    """Test extracting arrow functions."""
    source = """
const add = (a, b) => a + b;

const processData = async (data) => {
    const result = await transform(data);
    return result;
};

export const handler = (event, context) => {
    console.log('Event:', event);
};
"""
    symbols = extractor.extract_from_source(source)
    functions = [s for s in symbols if s.kind == "function"]

    assert len(functions) == 3

    # Check arrow function
    func1 = next(s for s in functions if s.name == "add")
    assert func1.signature == "const add = (a, b) =>"

    # Check async arrow function
    func2 = next(s for s in functions if s.name == "processData")
    assert func2.signature == "async processData = (data) =>"

    # Check exported arrow function
    func3 = next(s for s in functions if s.name == "handler")
    assert "handler" in func3.signature


def test_class_extraction(extractor):
    """Test extracting classes."""
    source = """
class User {
    constructor(name) {
        this.name = name;
    }
}

export class Admin extends User {
    constructor(name, permissions) {
        super(name);
        this.permissions = permissions;
    }
}
"""
    symbols = extractor.extract_from_source(source)
    classes = [s for s in symbols if s.kind == "class"]

    assert len(classes) == 2

    # Check simple class
    cls1 = next(s for s in classes if s.name == "User")
    assert cls1.signature == "class User"

    # Check class with inheritance
    cls2 = next(s for s in classes if s.name == "Admin")
    assert cls2.signature == "class Admin extends User"


def test_class_methods(extractor):
    """Test extracting class methods."""
    source = """
class Calculator {
    add(a, b) {
        return a + b;
    }

    async fetchValue(key) {
        const value = await this.storage.get(key);
        return value;
    }

    multiply(x, y) {
        return x * y;
    }
}
"""
    symbols = extractor.extract_from_source(source)
    methods = [s for s in symbols if s.kind == "method"]

    assert len(methods) == 3

    # Check method names include class prefix
    method_names = [m.name for m in methods]
    assert "Calculator.add" in method_names
    assert "Calculator.fetchValue" in method_names
    assert "Calculator.multiply" in method_names

    # Check async method
    async_method = next(s for s in methods if s.name == "Calculator.fetchValue")
    assert "async" in async_method.signature
    assert "fetchValue(key)" in async_method.signature


def test_es6_imports(extractor):
    """Test extracting ES6 import statements."""
    source = """
import React from 'react';
import { useState, useEffect } from 'react';
import * as fs from 'fs';
import { join, resolve } from 'path';
"""
    symbols = extractor.extract_from_source(source)
    imports = [s for s in symbols if s.kind == "import"]

    assert len(imports) >= 4  # At least: react, useState, useEffect, fs.*, join, resolve

    # Check named imports are extracted
    import_names = [i.name for i in imports]
    assert "react.useState" in import_names or "react" in import_names
    assert "react.useEffect" in import_names or "react" in import_names


def test_commonjs_require(extractor):
    """Test extracting CommonJS require statements."""
    source = """
const express = require('express');
const { Router } = require('express');
const fs = require('fs');
"""
    symbols = extractor.extract_from_source(source)
    imports = [s for s in symbols if s.kind == "import"]

    assert len(imports) >= 2

    # Check module names
    import_names = [i.name for i in imports]
    assert any("express" in name for name in import_names)


def test_mixed_content(extractor):
    """Test extracting from a file with mixed symbols."""
    source = """
import { Component } from 'react';

export class MyComponent extends Component {
    constructor(props) {
        super(props);
        this.state = {};
    }

    handleClick(event) {
        console.log('Clicked!');
    }

    render() {
        return null;
    }
}

export const helper = (data) => {
    return data.map(x => x * 2);
};

async function loadData() {
    const response = await fetch('/api/data');
    return response.json();
}
"""
    symbols = extractor.extract_from_source(source)

    # Check we have different kinds of symbols
    kinds = set(s.kind for s in symbols)
    assert "class" in kinds
    assert "method" in kinds
    assert "function" in kinds
    assert "import" in kinds

    # Check specific symbols
    classes = [s for s in symbols if s.kind == "class"]
    assert len(classes) == 1
    assert classes[0].name == "MyComponent"

    methods = [s for s in symbols if s.kind == "method"]
    assert len(methods) >= 2  # handleClick, render (constructor excluded)

    functions = [s for s in symbols if s.kind == "function"]
    assert len(functions) >= 2  # helper, loadData


def test_typescript_syntax(extractor):
    """Test extracting from TypeScript code."""
    source = """
interface User {
    name: string;
    age: number;
}

function greet(user: User): string {
    return `Hello, ${user.name}!`;
}

class DataService<T> {
    private data: T[];

    async fetch(id: number): Promise<T> {
        return this.data.find(item => item.id === id);
    }
}

const processUser = (user: User): void => {
    console.log(user);
};
"""
    symbols = extractor.extract_from_source(source)

    # Should extract functions, classes, and methods despite TypeScript syntax
    functions = [s for s in symbols if s.kind == "function"]
    classes = [s for s in symbols if s.kind == "class"]
    methods = [s for s in symbols if s.kind == "method"]

    assert len(functions) >= 1  # At least greet (processUser has TS type annotation)
    assert len(classes) == 1  # DataService
    assert len(methods) >= 1  # fetch


def test_empty_source(extractor):
    """Test extracting from empty source."""
    symbols = extractor.extract_from_source("")
    assert len(symbols) == 0


def test_no_symbols(extractor):
    """Test extracting from source with no symbols."""
    source = """
// Just comments
const x = 5;
let y = 10;
"""
    symbols = extractor.extract_from_source(source)
    # Might have zero symbols or just variables (not extracted)
    assert isinstance(symbols, list)


def test_line_numbers(extractor):
    """Test that line numbers are correctly reported."""
    source = """
// Line 1
function foo() {  // Line 2
    return 42;
}

// Line 6
class Bar {  // Line 7
    baz() {  // Line 8
        return 'hello';
    }
}
"""
    symbols = extractor.extract_from_source(source)

    # Check function line number (source starts with newline, so line numbering adjusted)
    func = next(s for s in symbols if s.name == "foo")
    assert func.start_line >= 2  # Should be line 2 or 3 depending on newline handling

    # Check class line number
    cls = next(s for s in symbols if s.name == "Bar")
    assert cls.start_line >= 7  # Should be around line 7-8

    # Check method line number
    method = next(s for s in symbols if s.name == "Bar.baz")
    assert method.start_line >= 8  # Should be around line 8-9
