# Learnings - Install Refactor

## Notepad Purpose
This file captures conventions, patterns, and accumulated wisdom during the install-refactor work session.

---


## F-String Syntax Error Fixes (2026-01-26)

### Root Causes Identified
1. **Nested quotes in f-strings**: String literals like `"''"` inside f-strings break the parser
2. **Ternary expressions with string literals**: `{'text' if condition else ''}` with nested quotes breaks parsing
3. **Complex string operations**: Multiple chained `.replace()` calls with `chr(92)` inside f-strings

### Fix Pattern Applied
**ALWAYS extract complex operations into intermediate variables BEFORE the f-string:**

```python
# BEFORE (broken):
f"{str(e).replace(chr(92), chr(92) * 2).replace('[', "'').replace(']', '')}"

# AFTER (fixed):
error_msg = str(e).replace(chr(92), chr(92) * 2).replace('[', '').replace(']', '')
f"{error_msg}"
```

```python
# BEFORE (broken):
f"{'[DRY RUN] Would set' if dry_run else 'Set'} value"

# AFTER (fixed):
set_text = '[DRY RUN] Would set' if dry_run else 'Set'
f"{set_text} value"
```

### Locations Fixed (11 total)
- Line 216-218: Complex string operations with nested quotes
- Line 1485-1487: Ternary with 'signing-' string literal
- Line 1510-1514: `.get('message', 'Unknown error')` with nested quotes
- Line 1548-1552: Ternary with '[DRY RUN] Would replace' vs 'Replacing'
- Line 1591-1593: Ternary with '[DRY RUN] Would update' vs 'Updated'
- Line 1609-1611: Ternary with '[DRY RUN] Updating' vs 'Updating'
- Line 1632-1635: Ternary with '[DRY RUN] Would set' vs 'Set' (Git user name)
- Line 1647-1650: Ternary with '[DRY RUN] Would set' vs 'Set' (Git email)
- Line 1681-1684: Ternary with '[DRY RUN] Would set' vs 'Set' (GPG key)
- Line 1725-1728: Ternary with '[DRY RUN] Would set' vs 'Set' (SSH key)
- Line 1748-1751: Ternary with '[DRY RUN] Would disable' vs 'Disabled'

### Verification
- ✅ `python3 -m py_compile install.py` returns exit code 0
- ✅ No syntax errors in file
- ✅ All f-string errors resolved

### Key Lesson
**Python f-strings cannot contain:**
- Backslashes (use `chr(92)` outside the f-string)
- Nested quotes that match the f-string delimiter
- Complex expressions with string literals (extract to variables first)

**Best practice:** Keep f-strings simple. Extract any complex logic into variables before the f-string.
