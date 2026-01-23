# Contributing to Codesearch

Thank you for your interest in contributing to codesearch! This document provides guidelines and information for contributors.

## 🚧 Development Status

Codesearch is currently under active development. We welcome contributions after Phase 6 is complete.

## 📋 Prerequisites

- Python 3.9 or higher
- Git
- Basic understanding of SQLite and full-text search
- Familiarity with AST parsing (for symbol extraction work)

## 🛠️ Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/codesearch.git
cd codesearch
```

### 2. Set up development environment

```bash
# Run the setup script
./scripts/setup_dev.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Verify installation

```bash
# Run tests
make test

# Or directly:
pytest tests/ -v
```

## 📁 Project Structure

```
codesearch/
├── codesearch/           # Main package
│   ├── indexer/         # Indexing components
│   │   └── symbols/     # Language-specific extractors
│   ├── query/           # Query processing
│   ├── storage/         # Database layer
│   └── utils/           # Utility functions
├── tests/
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── examples/            # Usage examples
├── scripts/             # Development scripts
├── docs/                # Documentation
└── benchmarks/          # Performance benchmarks
```

## 🧪 Testing

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-int

# With coverage
make coverage
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names: `test_<feature>_<scenario>`
- Use pytest fixtures from `tests/conftest.py`

Example:

```python
import pytest

def test_query_parser_handles_symbol_filters():
    from codesearch.query.parser import QueryParser
    
    parser = QueryParser()
    result = parser.parse("def:main")
    
    assert result.def_filter == "main"
```

## 🎨 Code Style

We follow PEP 8 with some modifications:

- Line length: 100 characters
- Use type hints where appropriate
- Write docstrings for all public functions/classes

### Formatting

```bash
# Format code
make format

# Check formatting
make lint
```

Tools we use:
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking

## 📝 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Example:**

```
feat(indexer): add incremental indexing support

Implement hash-based change detection to only re-index
modified files. This significantly improves re-indexing
performance on large repositories.

Closes #42
```

## 🔄 Development Workflow

### 1. Create a branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make changes

- Write code following style guidelines
- Add tests for new functionality
- Update documentation as needed

### 3. Test your changes

```bash
make test
make lint
```

### 4. Commit your changes

```bash
git add .
git commit -m "feat(scope): your descriptive message"
```

### 5. Push and create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 🎯 Areas for Contribution

### Phase 1-6 (Core Development)
Currently being implemented by the maintainer.

### After Phase 6

#### High Priority
- [ ] Additional language support (Java, Go, Rust)
- [ ] Performance optimizations
- [ ] Better error handling and logging
- [ ] Additional query operators

#### Medium Priority
- [ ] Find references functionality
- [ ] Semantic search integration
- [ ] Configuration file support
- [ ] Custom ranking strategies

#### Low Priority
- [ ] Web UI
- [ ] IDE integrations
- [ ] Cloud sync support (optional)

## 📚 Documentation

### Updating Documentation

- Architecture docs: `docs/architecture.md`
- User guide: `README.md`
- API docs: Inline docstrings

### Building Documentation

Documentation is currently markdown-based. Future versions may include Sphinx/MkDocs.

## 🐛 Reporting Bugs

### Before Submitting

1. Check existing issues
2. Verify you're on the latest version
3. Reproduce the bug with minimal example

### Bug Report Template

```markdown
**Description:**
Clear description of the bug

**To Reproduce:**
Steps to reproduce the behavior:
1. Index repository '...'
2. Run query '...'
3. See error

**Expected Behavior:**
What you expected to happen

**Environment:**
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.11.0]
- Codesearch version: [e.g., 0.1.0]

**Additional Context:**
Any other relevant information
```

## 💡 Feature Requests

Feature requests are welcome! Please:

1. Check if the feature is already planned in `prd.md`
2. Explain the use case clearly
3. Consider implementation complexity
4. Be open to discussion

## 🔍 Code Review Process

All contributions go through code review:

1. **Automated checks**: Tests, linting, coverage
2. **Manual review**: Code quality, design, documentation
3. **Testing**: Verify functionality works as expected
4. **Merge**: Once approved, changes are merged

## 📊 Performance Considerations

When contributing performance-sensitive code:

- Run benchmarks before and after changes
- Profile code if making optimization claims
- Document performance characteristics
- Consider trade-offs (speed vs memory vs complexity)

## 🔒 Security

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email security concerns to: your.email@example.com
3. Allow time for assessment and fix
4. Coordinate disclosure timing

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🤝 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Expected Behavior

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the project
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing private information

## 📞 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Chat**: (Coming soon)

## 🎉 Recognition

Contributors will be recognized in:
- `README.md` contributors section
- Release notes
- Project documentation

Thank you for contributing to codesearch! 🚀
