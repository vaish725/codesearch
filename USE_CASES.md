# Real-World Use Cases for Codesearch

This document demonstrates practical scenarios where codesearch excels.

## Use Case 1: Finding Security Vulnerabilities

**Scenario**: Audit codebase for hardcoded credentials

```bash
# Find potential API keys or passwords
codesearch query "api_key" --topk 50
codesearch query "password =" --topk 50
codesearch query "secret" lang:python

# Find database connection strings
codesearch query "mongodb://" 
codesearch query "postgres://"
```

## Use Case 2: Code Migration

**Scenario**: Migrating from one library to another

```bash
# Find all usages of old library
codesearch query "import:requests"

# Find specific function calls
codesearch query "requests.get"
codesearch query "requests.post"

# After migration, verify no old imports remain
codesearch query "import:requests" --json | jq '.total_results'
```

## Use Case 3: Debugging Production Issues

**Scenario**: Find where a specific error is raised

```bash
# Find error raising locations
codesearch query "raise ValueError" lang:python
codesearch query "throw new Error" lang:javascript

# Find error handling
codesearch query "except ValueError" --context 3
codesearch query "catch (error)" lang:javascript --context 3
```

## Use Case 4: Code Review Assistance

**Scenario**: Review changes before merging

```bash
# Find all TODO/FIXME comments
codesearch query "TODO" path:src
codesearch query "FIXME" path:src

# Check for debugging code
codesearch query "console.log" lang:javascript
codesearch query "print(" lang:python

# Verify no test code in production
codesearch query "import:pytest" path:src
```

## Use Case 5: Learning New Codebase

**Scenario**: Understanding a large project structure

```bash
# Find main entry points
codesearch query "def:main"
codesearch query "if __name__ == '__main__'"

# Understand API endpoints
codesearch query "@app.route" lang:python
codesearch query "app.get" lang:javascript

# Find configuration files
codesearch query "class:Config"
codesearch query "import:config"
```

## Use Case 6: Dependency Analysis

**Scenario**: Understand project dependencies

```bash
# List all external imports
codesearch query "import:" --json | jq '.results[].symbol_name' | sort -u

# Find deprecated package usage
codesearch query "import:deprecated_package"

# Check third-party library usage
codesearch query "import:numpy"
codesearch query "import:pandas"
```

## Use Case 7: Refactoring

**Scenario**: Safely rename a function across codebase

```bash
# Step 1: Find all usages
codesearch query "def:old_function_name"
codesearch query "old_function_name" --topk 100

# Step 2: After rename, verify old name is gone
codesearch query "old_function_name" --json
```

## Use Case 8: Documentation Generation

**Scenario**: Find undocumented functions

```bash
# Find all function definitions
codesearch query "def:" lang:python --json > all_functions.json

# Find functions with docstrings
codesearch query '"""' path:src lang:python

# Compare to find undocumented ones
```

## Use Case 9: Performance Optimization

**Scenario**: Find performance bottlenecks

```bash
# Find database queries
codesearch query "SELECT" 
codesearch query "query(" lang:python

# Find loops that might be slow
codesearch query "for .* in .*:" lang:python --context 3

# Find synchronous operations
codesearch query "time.sleep"
codesearch query ".join()" lang:python
```

## Use Case 10: Compliance & Standards

**Scenario**: Ensure coding standards compliance

```bash
# Check for proper error handling
codesearch query "try:" lang:python --topk 200

# Verify logging usage
codesearch query "import:logging"
codesearch query "logger."

# Check for type hints
codesearch query "def.*->.*:" lang:python
```

## Automation Scripts

### Daily Security Scan
```bash
#!/bin/bash
# security-scan.sh

echo "🔍 Running daily security scan..."

echo "Checking for hardcoded secrets..."
codesearch query "password\s*=\s*['\"]" --json > secrets_scan.json

echo "Checking for API keys..."
codesearch query "api_key|API_KEY" --json >> secrets_scan.json

if [ $(jq '.total_results' secrets_scan.json) -gt 0 ]; then
    echo "⚠️  WARNING: Potential secrets found!"
    jq '.results[] | "\(.file_path):\(.line_number)"' secrets_scan.json
else
    echo "✅ No secrets detected"
fi
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running codesearch pre-commit checks..."

# Check for debugging code
DEBUG_COUNT=$(codesearch query "console.log|print(" --json | jq '.total_results')

if [ "$DEBUG_COUNT" -gt 0 ]; then
    echo "⚠️  Found $DEBUG_COUNT debugging statements"
    echo "Please remove before committing"
    exit 1
fi

echo "✅ Pre-commit checks passed"
```

## Integration with Other Tools

### With Git Hooks
```bash
# Find recent changes
git diff --name-only | xargs -I {} codesearch query "path:{}"
```

### With CI/CD
```yaml
# .github/workflows/code-quality.yml
- name: Check for TODOs
  run: |
    TODO_COUNT=$(codesearch query "TODO|FIXME" --json | jq '.total_results')
    echo "Found $TODO_COUNT TODOs"
    if [ "$TODO_COUNT" -gt 50 ]; then
      echo "::warning::Too many TODOs ($TODO_COUNT). Consider addressing them."
    fi
```

### With Jupyter Notebooks
```python
import json
import subprocess

def search_code(query):
    """Search code and return results as DataFrame"""
    result = subprocess.run(
        ['codesearch', 'query', query, '--json'],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)
    return pd.DataFrame(data['results'])

# Usage
df = search_code('def:process_payment')
df[['file_path', 'line_number', 'symbol_name']]
```

---

These use cases demonstrate codesearch's versatility beyond basic search, making it a valuable tool for developers, security teams, and DevOps engineers.
