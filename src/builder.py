"""
PyNexe Builder
Core building logic for Python projects with Nuitka.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


class BuilderConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path

        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> dict[str, Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _validate_config(self) -> None:
        required_fields = ["project_name", "main_file", "output_name"]

        missing_fields = []
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    @property
    def project_name(self) -> str:
        return self.config["project_name"]

    @property
    def main_file(self) -> str:
        return self.config["main_file"]

    @property
    def output_name(self) -> str:
        return self.config["output_name"]

    @property
    def build_libs(self) -> list[str]:
        return self.config.get("build_libs", ["nuitka", "ordered-set"])

    @property
    def project_libs(self) -> list[str]:
        return self.config.get("project_libs", [])

    @property
    def include_packages(self) -> list[str]:
        return self.config.get("include_packages", [])

    @property
    def include_data_dirs(self) -> list[str]:
        return self.config.get("include_data_dirs", [])

    @property
    def icon_file(self) -> str | None:
        return self.config.get("icon_file")

    @property
    def windows_metadata(self) -> dict[str, str]:
        return self.config.get(
            "windows_metadata",
            {
                "product_name": "Windows System Manager",
                "file_description": "System Configuration Manager",
                "product_version": "10.0.19041.1",
                "file_version": "10.0.19041.1",
                "copyright": "Microsoft Corporation",
                "company_name": "Microsoft Corporation",
            },
        )

    @property
    def nuitka_plugins(self) -> list[str]:
        return self.config.get("nuitka_plugins", ["upx", "no-qt", "tk-inter"])

    @property
    def nuitka_extra_args(self) -> list[str]:
        return self.config.get(
            "nuitka_extra_args",
            [
                "--lto=no",
                "--show-scons",
                "--jobs=1",
            ],
        )

    @property
    def cleanup_items(self) -> list[str]:
        base_items = [
            f"{self.project_name}.build",
            f"{self.project_name}.dist",
            f"{self.project_name}.onefile-build",
            "__pycache__",
        ]
        custom_items = self.config.get("cleanup_items", [])
        return base_items + custom_items


class Builder:
    def __init__(self, config: BuilderConfig):
        self.config = config

        self._temp_dir: str | None = None
        self._venv_path: str | None = None
        self._python_exe: str | None = None

    def create_temp_env(self) -> None:
        """Create a temporary virtual environment."""
        self._temp_dir = tempfile.mkdtemp(prefix="build_")
        self._venv_path = Path(self._temp_dir) / "venv"

        result = subprocess.run(
            [sys.executable, "-m", "venv", str(self._venv_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create venv: {result.stderr}")

        if os.name == "nt":
            self._python_exe = self._venv_path / "Scripts" / "python.exe"
        else:
            self._python_exe = self._venv_path / "bin" / "python"

    def _install_single_dependency(self, dep: str) -> None:
        """Install a single dependency."""
        result = subprocess.run(
            [str(self._python_exe), "-m", "pip", "install", dep],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to install {dep}: {result.stderr}")

    def install_dependencies(self) -> None:
        """Install all dependencies."""
        # Install build libraries
        for dep in self.config.build_libs:
            self._install_single_dependency(dep)

        # Install project libraries (if any)
        if self.config.project_libs:
            for dep in self.config.project_libs:
                self._install_single_dependency(dep)

    def build_with_nuitka(self) -> None:
        """Build the project with Nuitka."""
        if not os.path.exists(self.config.main_file):
            raise FileNotFoundError(f"Main file not found: {self.config.main_file}")

        nuitka_args = [
            str(self._python_exe),
            "-m",
            "nuitka",
            "--standalone",
            "--onefile",
            "--assume-yes-for-downloads",
            "--remove-output",
            "--no-pyi-file",
            f"--output-filename={self.config.output_name}",
            f"--product-name={self.config.windows_metadata['product_name']}",
            f"--file-description={self.config.windows_metadata['file_description']}",
            f"--product-version={self.config.windows_metadata['product_version']}",
            f"--file-version={self.config.windows_metadata['file_version']}",
            f"--copyright={self.config.windows_metadata['copyright']}",
            f"--company-name={self.config.windows_metadata['company_name']}",
        ]

        # Add extra args
        for arg in self.config.nuitka_extra_args:
            nuitka_args.append(arg)

        # Add packages (if any)
        for package in self.config.include_packages:
            nuitka_args.append(f"--include-package={package}")

        # Add data dirs (if any)
        for data_dir in self.config.include_data_dirs:
            # Parse format: "source=dest" or just "source"
            if "=" in data_dir:
                parts = data_dir.split("=", 1)  # Split only on first "="
                source_path = parts[0]
                dest_path = parts[1] if len(parts) > 1 else parts[0]
            else:
                source_path = data_dir
                dest_path = data_dir

            # Only add if source path exists
            if os.path.exists(source_path):
                nuitka_args.append(f"--include-data-dir={source_path}={dest_path}")

        # Add plugins
        for plugin in self.config.nuitka_plugins:
            nuitka_args.append(f"--plugin-enable={plugin}")

        # Add icon if provided
        if self.config.icon_file and os.path.exists(self.config.icon_file):
            nuitka_args.append(f"--windows-icon-from-ico={self.config.icon_file}")

        nuitka_args.append(self.config.main_file)

        result = subprocess.run(nuitka_args, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  Nuitka stdout: {result.stdout}")
            print(f"  Nuitka stderr: {result.stderr}")
            raise RuntimeError(f"Nuitka build failed: {result.stderr}")

        if not os.path.exists(self.config.output_name):
            raise RuntimeError(f"Output file not created: {self.config.output_name}")

    def cleanup(self) -> None:
        """Clean up build artifacts."""
        for item in self.config.cleanup_items:
            if os.path.exists(item):
                try:
                    if os.path.isdir(item):
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        os.remove(item)
                except (OSError, PermissionError) as exception:
                    # Log warning but don't crash on cleanup failures
                    print(f"Warning: Failed to remove {item}: {exception}")

        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except (OSError, PermissionError) as exception:
                print(f"Warning: Failed to remove temp directory {self._temp_dir}: {exception}")

    def build(self) -> None:
        """Main build method."""
        try:
            print(f"Building project: {self.config.project_name}")
            print(f"Main file: {self.config.main_file}")
            print(f"Output: {self.config.output_name}")
            if self.config.icon_file:
                print(f"Icon file: {self.config.icon_file}")

            print("Creating environment...")
            self.create_temp_env()

            print("Installing dependencies...")
            if self.config.project_libs:
                print(f"  Project libraries: {', '.join(self.config.project_libs)}")
            else:
                print("  No project libraries specified")
            self.install_dependencies()

            print("Compiling with Nuitka...")
            if "upx" in self.config.nuitka_plugins:
                print("  UPX compression via Nuitka plugin...")
            self.build_with_nuitka()

            print("Cleaning up...")
            self.cleanup()

            print(f"Build completed successfully: {self.config.output_name}")
            print(f"Project: {self.config.project_name}")

        except KeyboardInterrupt:
            print("Build interrupted by user")
            self.cleanup()
            sys.exit(1)

        except Exception as exception:
            print(f"Build failed: {exception}")
            self.cleanup()
            sys.exit(1)
