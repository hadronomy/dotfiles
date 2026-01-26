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

## InstallContext Dataclass Introduction (2026-01-26)

### Refactoring Approach
Successfully introduced `InstallContext` dataclass to replace global variables and improve code organization.

### Changes Made
1. **Created InstallContext dataclass** (lines 37-55):
   - Fields: `dry_run`, `console`, `dotfiles_dir`, `repo_url`, `user_config`
   - Used `@dataclass` with `field(default_factory=...)` for mutable defaults
   - Kept `DEFAULT_USER` and `CURRENT_USER` as module-level constants (not configurable)

2. **Removed global variables**:
   - `DOTFILES_DIR` → `ctx.dotfiles_dir`
   - `REPO_URL` → `ctx.repo_url`
   - `USER_CONFIG` → `ctx.user_config`

3. **Updated 14 function signatures** to accept `ctx: InstallContext`:
   - `install_nix(ctx)`
   - `install_home_manager_standalone(ctx)`
   - `install_home_manager(ctx)`
   - `clone_dotfiles(ctx)`
   - `customize_dotfiles(ctx, force_customize=False)`
   - `collect_user_info(ctx)`
   - `gpg_key_options(ctx)`
   - `ssh_key_options(ctx)`
   - `list_gpg_keys(ctx)`
   - `create_gpg_key(ctx, name, email)`
   - `list_ssh_keys(ctx)`
   - `create_ssh_key(ctx, email)`
   - `add_key_to_github(ctx, key_type, key_path_or_id)`
   - `replace_username_in_files(ctx)`
   - `update_git_config(ctx)`
   - `apply_home_manager(ctx)`

4. **Updated run_command()** to accept optional `console` parameter:
   - Signature: `run_command(command, check=True, shell=False, dry_run=False, env=None, console=None)`
   - Falls back to `Console()` if not provided
   - All calls from ctx functions pass `console=ctx.console`

5. **Replaced ~190 references**:
   - `console.` → `ctx.console.`
   - `dry_run` → `ctx.dry_run`
   - `DOTFILES_DIR` → `ctx.dotfiles_dir`
   - `REPO_URL` → `ctx.repo_url`
   - `USER_CONFIG` → `ctx.user_config`

### Automation Strategy
Used Python scripts for bulk refactoring due to scale (190+ replacements):
1. Updated function signatures with regex
2. Replaced console/dry_run references within function bodies
3. Replaced global variable references
4. Updated function calls to pass ctx
5. Fixed duplicate parameters

### Verification
- ✅ `python3 -m py_compile install.py` returns exit code 0
- ✅ `./install.py --help` displays correct usage
- ✅ No syntax errors
- ✅ All function signatures updated
- ✅ All global variables removed

### Key Lessons
1. **Dataclass with mutable defaults**: Use `field(default_factory=lambda: {...})` for dict/list defaults
2. **Bulk refactoring**: Python scripts more efficient than manual edits for 100+ changes
3. **Context pattern**: Passing context object cleaner than individual parameters
4. **Backward compatibility**: `run_command()` kept optional console param for non-ctx callers
5. **Module constants**: Keep truly constant values (DEFAULT_USER, CURRENT_USER) at module level

### Pattern Applied
```python
# Before:
def install_nix(dry_run=False):
    if dry_run:
        console.print("...")
    run_command(..., dry_run=dry_run)

# After:
def install_nix(ctx: InstallContext):
    if ctx.dry_run:
        ctx.console.print("...")
    run_command(..., dry_run=ctx.dry_run, console=ctx.console)
```

