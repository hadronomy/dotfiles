# Install Script Refactoring Plan

## Context
The `install.py` script is the entry point for bootstrapping the dotfiles. It currently has critical syntax errors (f-strings), uses legacy `os.path` methods, has verbose argument passing (`dry_run`), and lacks modern UX feedback.

## Work Objectives
1.  **Fix Critical Syntax Errors**: Repair all broken f-strings to ensure the script compiles.
2.  **Architecture Refactor**: Introduce an `InstallContext` object to manage global state (`dry_run`, configuration).
3.  **Modernize Codebase**: Migrate from `os.path` to `pathlib` for robust path handling.
4.  **UX Enhancement**: Implement `rich` status spinners and progress indicators for a "delightful" experience.

## Verification Strategy
- **Syntax Check**: `python3 -m py_compile install.py` MUST pass after Phase 1.
- **Dry Run Verification**: `install.py --dry-run` MUST output expected commands without errors.
- **Manual QA**: Verify UX improvements (spinners) visually if possible (or via detailed logs).

---

## TODOs

### Phase 1: Critical Syntax Repairs
- [x] 1. Fix f-string syntax errors
  **What to do**:
  - Locate all instances of f-strings containing backslashes or nested quotes that break parsing.
  - Refactor them to extract complex logic into variables BEFORE the f-string.
  - **Identified locations**: lines 216-218, 1485-1487, 1513-1514, 1552-1555, 1598-1600, 1619-1620, 1645-1648, 1664-1667, 1702-1705, 1750-1753, 1777-1780.
  - **Verification**: Run `python3 -m py_compile install.py` and ensure it returns exit code 0.
  **References**:
  - `install.py:216` (Error handling)
  - `install.py:1485` (Key title generation)

### Phase 2: Architecture & State Management
- [x] 2. Introduce `InstallContext` dataclass
  **What to do**:
  - Create a `@dataclass class InstallContext` to hold: `dry_run`, `console`, `dotfiles_dir`, `repo_url`, `user_config`.
  - Initialize this context in the `install` command.
  - Refactor functions to accept `ctx: InstallContext` instead of individual arguments.
  - Remove global `REPO_URL`, `DOTFILES_DIR`, `USER_CONFIG` variables (move to context).
  **References**:
  - `install.py:34-46` (Global variables)
  - `install.py:1966` (Main command)

- [x] 3. Refactor function signatures
  **What to do**:
  - Update `install_nix`, `install_home_manager`, `clone_dotfiles`, etc., to take `ctx`.
  - Update all callsites to pass the context object.
  - **Verification**: Run `install.py --dry-run` to ensure logic flows correctly.

### Phase 3: Pathlib Migration
- [x] 4. Migrate to `pathlib.Path`
  **What to do**:
  - Replace `os.path.join`, `os.path.expanduser`, `os.path.exists` with `Path` methods.
  - Update `InstallContext` to store paths as `Path` objects.
  - **CRITICAL**: Wrap `Path` objects in `str()` when passing to `subprocess` or `shutil`.
  - Refactor `os.walk` usage (keep as-is or use `rglob` if safe).
  **References**:
  - `install.py:34` (DOTFILES_DIR)
  - `install.py:1125` (temp_dir)

### Phase 4: UX & Modernization
- [x] 5. Modernize `run_command` and Subprocess
  **What to do**:
  - Simplify `run_command` to use `subprocess.run` for blocking calls where streaming isn't strictly needed (or keep streaming but clean up implementation).
  - Ensure `shlex.quote` is used correctly.
  - Improve error reporting.

- [ ] 6. Implement Delightful UX
  **What to do**:
  - Use `console.status("Installing Nix...")` for long-running operations.
  - Use `rich.panel` to group output sections (e.g., "Configuration", "Installation").
  - Improve the "dry run" visual feedback (maybe a distinct style/color).
  - Ensure prompts are clear and interactive.

## Success Criteria
- [ ] Script compiles without syntax errors.
- [ ] `install.py --dry-run` executes successfully.
- [ ] Codebase uses `pathlib` and `InstallContext`.
- [ ] Output is visually distinct and helpful (spinners, panels).
