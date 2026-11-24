# AGENTS.md

Repository map for coding agents. The code is the source of current behavior; this file keeps what the code does not say.

## How to work here

PyNexe is a small CLI that turns a project's `config.yaml` into a Nuitka build of a Windows `.exe`. Read the code of the area before changing it; there are two modules.

Code: `pynexe.py` (entry point) → `src/cli.py` (commands `run`, `info`, `help`; file validation; all Rich output) → `src/builder.py` (`BuilderConfig` loads and validates the YAML; `Builder` creates a temp venv, installs `build_libs` and `project_libs`, runs Nuitka, cleans up). The root `config.yaml` is the sample config users copy, not PyNexe's own settings.

## Commands

- Setup: `pip install -r requirements.txt` (Python 3.13+, per README).
- Lint: `ruff check .` (`ruff.toml`; Ruff is not in `requirements.txt`).
- Smoke: `python pynexe.py help` and `python pynexe.py info` (reads `./config.yaml`, builds nothing).
- `python pynexe.py run` is a real build: Windows with Visual Studio Build Tools, network for pip, several minutes. On macOS/Linux it only warns and then fails; do not use it as a check there.

There is no test suite and no CI.

## Easy to forget

- **Paths resolve against the current directory**, not the config file's folder: `main_file`, `icon_file`, `include_data_dirs`, `output_name`, `cleanup_items`. `--config` only picks which file is read.
- **`run` deletes paths in the current directory** during cleanup: `<project_name>.build`, `.dist`, `.onefile-build`, `__pycache__`, and every `cleanup_items` entry. Run it only in a disposable project folder.
- **Defaults live in three places**: the `BuilderConfig` fallbacks in `src/builder.py`, the root `config.yaml`, and the README configuration section. Change them together.
- **`src/builder.py` stays UI-free**: no Rich, no printing, no `sys.exit`. It raises `FileNotFoundError`, `ValueError`, or `RuntimeError`, which `src/cli.py` turns into error panels; progress goes through the callback of `install_dependencies_with_callback`.
- **The build venv is not PyNexe's environment**: it gets only `build_libs` and `project_libs`, never `rich` or `pyyaml`.

## Documents

- [README.md](README.md): user-facing install, config keys, usage, troubleshooting.

**When to update:** a change to a CLI command, a config key, a default, or a requirement updates the README in the same change. Refactors do not.

## Definition of done

- `ruff check .` passes and `python pynexe.py info` still runs against the root `config.yaml`.
- A change to the build path (`Builder`, Nuitka arguments) says whether a real Windows build verified it.
- No residue: no dead code, unused helpers, debug output, commented-out blocks, or stray files (build outputs, `.exe`, scratch scripts) left in the tree.

## Local instructions

- Follow your host's instruction precedence; the user's message in the session wins.
- Scratch work goes in the host scratchpad or the OS temp dir, never in the repo.
- Project skills arrive through `brantz install` (`.brantz-lock.json`); do not edit their copies under `.agents/`, `.claude/`, or `.cursor/`. Use `integrity-review` before claiming a change done, `write-readme` for README changes, and `git-commit` when committing.
