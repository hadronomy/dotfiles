# Linux Support Refactor & Reconciliation

## Context
User wants to commit current local changes, reconcile with remote (prioritizing local), and refactor the dotfiles (Nix Flake) to support both macOS (current) and Linux (x86_64).

## Work Objectives
1. **Git Reconciliation**: Secure local changes and sync with remote.
2. **Multi-OS Support**: Refactor `flake.nix` and `home/default.nix` to handle both Darwin and Linux.
3. **Installation Update**: Ensure `install.sh` works on both platforms.

## Verification Strategy
- **Manual Verification (No CI)**:
  - Git status: Clean and ahead/sync after pull.
  - Nix check: `nix flake check` passes.
  - Build check: `nix build .#homeConfigurations.hadronomy.activationPackage` (macOS) and `nix build .#homeConfigurations.hadronomy-linux.activationPackage` (Linux).

---

## TODOs

### Phase 1: Git Reconciliation
- [x] 1. Commit and Reconcile
  **What to do**:
  - `git add .`
  - `git commit -m "chore: save local changes before reconciliation"`
  - `git pull --rebase -X ours origin main`
  - Verify: `git status` is clean.

### Phase 2: Core Refactoring
- [x] 2. Refactor `flake.nix` for Multi-Arch
  **What to do**:
  - Change `systems` to include `"x86_64-linux"`.
  - Create a reusable `mkHome` function or define `homeConfigurations."hadronomy-linux"`.
  - Ensure `pkgs` is instantiated with the correct system for each config.
  - Target: `homeConfigurations."hadronomy"` (macOS, existing) and `homeConfigurations."hadronomy-linux"` (Linux, new).
  **References**:
  - `flake.nix:38` (Outputs)

- [x] 3. Refactor `home/default.nix` for Path Compatibility
  **What to do**:
  - Replace hardcoded `/Users/${config.home.username}` with conditional logic.
  - Use `pkgs.stdenv.isDarwin` to decide home directory path.
  **References**:
  - `home/default.nix:15` (Home Directory)

- [x] 4. Update `install.sh` for Linux Detection
  **What to do**:
  - Add OS detection (uname).
  - If Linux, use flake output `#hadronomy-linux`.
  - If macOS, use flake output `#hadronomy` (default).
  **References**:
  - `install.sh:108` (home-manager switch command)

### Phase 3: Verification
- [ ] 5. Verify Builds
  **What to do**:
  - Run `nix flake check`.
  - Run `nix build .#homeConfigurations.hadronomy.activationPackage --dry-run` (on macOS).
  - (Optional) Run `nix build .#homeConfigurations.hadronomy-linux.activationPackage --dry-run` (if cross-compilation allows, otherwise skip).

---

## Success Criteria
- Git repo is clean and synced.
- `flake.nix` has `hadronomy` (Darwin) and `hadronomy-linux` (Linux) outputs.
- `home/default.nix` has no hardcoded `/Users/`.
- `install.sh` selects correct output based on OS.
