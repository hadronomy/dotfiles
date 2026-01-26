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


## Task 4: Pathlib Migration (2026-01-26)

### Changes Made
- Added `from pathlib import Path` import
- Updated `InstallContext.dotfiles_dir` from `str` to `Path`
- Replaced ~20 instances of `os.path.expanduser()` with `Path.home() / "..."`
- Replaced ~15 instances of `os.path.join()` with Path `/` operator
- Replaced ~25 instances of `os.path.exists()` with `Path.exists()`
- Replaced ~10 instances of `os.makedirs()` with `Path.mkdir(parents=True, exist_ok=True)`
- Replaced 5 instances of `os.remove()` with `Path.unlink(missing_ok=True)`
- Replaced 1 instance of `os.chmod()` with `Path.chmod()`
- Replaced 1 instance of `os.listdir()` with `Path.iterdir()`
- Kept `os.walk()` as-is (wrapped ctx.dotfiles_dir in str() for compatibility)
- Kept `os.access()` as-is (no pathlib equivalent)

### Critical Wrapping Pattern
**IMPORTANT**: All Path objects must be wrapped in `str()` when passed to:
- `subprocess.run()` / `subprocess.Popen()` / `run_command()`
- `shutil.rmtree()`
- `urllib.request.urlretrieve()`
- Any external command-line tool

Examples:
```python
# CORRECT:
run_command(["git", "clone", repo_url, str(ctx.dotfiles_dir)])
shutil.rmtree(str(repo_path))
subprocess.run(["gpg", "--batch", "--generate-key", str(batch_file)])

# WRONG:
run_command(["git", "clone", repo_url, ctx.dotfiles_dir])  # Will fail!
```

### os.walk() Decision
Kept `os.walk()` as-is in `replace_username_in_files()` because:
1. Function iterates over potentially large directory tree
2. `os.walk()` is well-tested and efficient for this use case
3. Wrapped `ctx.dotfiles_dir` in `str()` for compatibility: `os.walk(str(ctx.dotfiles_dir))`
4. Converting to `Path.rglob()` would require significant refactoring of the loop logic

### Path Operations Mapping
| Old (os.path) | New (pathlib) |
|---------------|---------------|
| `os.path.expanduser("~/foo")` | `Path.home() / "foo"` |
| `os.path.join(a, b, c)` | `Path(a) / b / c` |
| `os.path.exists(path)` | `Path(path).exists()` |
| `os.makedirs(path, exist_ok=True)` | `Path(path).mkdir(parents=True, exist_ok=True)` |
| `os.remove(path)` | `Path(path).unlink(missing_ok=True)` |
| `os.chmod(path, mode)` | `Path(path).chmod(mode)` |
| `os.listdir(dir)` | `Path(dir).iterdir()` |
| `os.path.dirname(path)` | `Path(path).parent` |
| `os.path.abspath(__file__)` | `Path(__file__).resolve()` |

### Verification
- ✅ `python3 -m py_compile install.py` passes
- ✅ `./install.py --dry-run` works correctly
- ✅ All Path objects properly wrapped in str() for external calls

### Benefits
- More readable path operations (using `/` operator)
- Type safety (Path objects vs strings)
- Cross-platform compatibility (pathlib handles OS differences)
- Modern Python idioms (pathlib is the recommended approach since Python 3.4)

## Task 5: Modernize run_command and Subprocess (2026-01-26)

### Changes Made
- **Enhanced docstring**: Added comprehensive Args/Returns/Raises documentation
- **Improved shlex.quote usage**: Added `str()` wrapper to handle Path objects safely
- **Better command display**: Added type checking for shell vs list commands
- **Cleaner streaming logic**: Changed `.strip()` to `.rstrip()` to preserve leading whitespace
- **Enhanced error messages**: 
  - Show truncated command (100 chars max) in error output
  - Extract command name from FileNotFoundError for clearer messaging
  - Added helpful hint about PATH for missing commands
  - Show exit code in error message
- **Better error context**: Pass descriptive output to CalledProcessError
- **Code comments**: Added inline comments explaining streaming logic

### Key Improvements

#### 1. shlex.quote Safety
```python
# BEFORE:
cmd_str = " ".join(shlex.quote(arg) for arg in command)

# AFTER:
cmd_str = " ".join(shlex.quote(str(arg)) for arg in command)
```
**Why**: Handles Path objects from pathlib migration (Task 4). Without `str()`, Path objects would fail shlex.quote.

#### 2. Error Message Enhancement
```python
# BEFORE:
console.print(f"[bold red]Command failed with error code {e.returncode}[/bold red]")

# AFTER:
cmd_display = cmd_str if len(cmd_str) <= 100 else f"{cmd_str[:97]}..."
console.print(
    f"[bold red]Command failed with exit code {e.returncode}:[/bold red]\n"
    f"  {cmd_display}"
)
```
**Why**: 
- Shows actual command that failed (truncated if too long)
- Multi-line format is more readable
- "exit code" is more standard terminology than "error code"

#### 3. FileNotFoundError Clarity
```python
# BEFORE:
console.print(f"[bold red]Command not found: {e}[/bold red]")

# AFTER:
cmd_name = command[0] if isinstance(command, list) else command.split()[0]
console.print(
    f"[bold red]Command not found:[/bold red] {cmd_name}\n"
    f"  Make sure the command is installed and in your PATH"
)
```
**Why**:
- Extracts just the command name (not full exception message)
- Provides actionable hint about PATH
- Cleaner formatting

#### 4. Whitespace Preservation
```python
# BEFORE:
console.print(stdout_line.strip())

# AFTER:
console.print(stdout_line.rstrip())
```
**Why**: `.rstrip()` only removes trailing whitespace, preserving intentional indentation in command output (useful for formatted output like tree structures).

### Verification
- ✅ `python3 -m py_compile install.py` passes (exit code 0)
- ✅ `./install.py --dry-run` works correctly
- ✅ All error paths tested and improved
- ✅ shlex.quote handles Path objects safely

### Pattern Applied
**Modern subprocess with streaming:**
```python
# Use Popen for real-time output
process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=shell,
    env=env,
)

# Stream line by line
while True:
    stdout_line = process.stdout.readline() if process.stdout else ""
    stderr_line = process.stderr.readline() if process.stderr else ""
    
    if stdout_line:
        console.print(stdout_line.rstrip())
    if stderr_line:
        console.print(f"[dim]{stderr_line.rstrip()}[/dim]")
    
    if not stdout_line and not stderr_line and process.poll() is not None:
        break
```

### Design Decisions
1. **Kept Popen over subprocess.run**: Real-time streaming is valuable for long-running operations (Nix installs, git clones)
2. **Kept streaming implementation**: User feedback during long operations improves UX
3. **Added str() to shlex.quote**: Future-proofs against Path objects and other non-string types
4. **Truncate long commands**: Prevents terminal spam while still showing what failed
5. **Preserve function signature**: No breaking changes to existing callers

### Benefits
- More informative error messages help debugging
- Better handling of Path objects from pathlib migration
- Cleaner code with better documentation
- Preserved real-time output streaming (important for UX)
- More robust type handling in command string building

