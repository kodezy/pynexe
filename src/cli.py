#!/usr/bin/env python3
"""PyNexe CLI
Simple and direct Python to Native Executable Builder.
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from src.builder import Builder, BuilderConfig, parse_data_dir_entry


class PyNexeCLI:
    def __init__(self):
        self._console = Console()

    def _print_error(self, title: str, lines: list[str], hint: str = "") -> None:
        text = Text()
        text.append(f"{title}\n", style="bold red")
        for line in lines:
            text.append(f"  {line}\n", style="red")
        if hint:
            text.append(f"\n{hint}", style="dim")
        self._console.print(Panel(text, title="Error", border_style="red"))

    def print_banner(self) -> None:
        banner_text = Text("PyNexe", style="bold blue")
        self._console.print(banner_text)

    def print_help(self) -> None:
        self.print_banner()

        help_text = Text()
        help_text.append("Commands\n", style="bold")
        help_text.append(
            "  run              Build executable from config.yaml\n",
            style="white",
        )
        help_text.append(
            "  info             Show project configuration\n",
            style="white",
        )
        help_text.append("  help             Show this help\n\n", style="white")

        help_text.append("Examples\n", style="bold")
        help_text.append("  python pynexe.py run\n", style="dim")
        help_text.append("  python pynexe.py run --config prod.yaml\n", style="dim")
        help_text.append("  python pynexe.py info\n", style="dim")

        panel = Panel(help_text, border_style="blue")
        self._console.print(panel)

    def build_project(self, config_path: str) -> None:
        try:
            config = BuilderConfig(config_path)

            validation_issues = self._validate_build_files(config)
            if validation_issues:
                self._print_error(
                    "Validation failed",
                    [f"• {issue}" for issue in validation_issues],
                    "Fix these issues before building.",
                )
                sys.exit(1)

            info_text = Text()
            info_text.append("Project: ", style="bold")
            info_text.append(f"{config.project_name}\n", style="cyan")
            info_text.append("Main: ", style="bold")
            info_text.append(f"{config.main_file}\n", style="cyan")
            info_text.append("Output: ", style="bold")
            info_text.append(f"{config.output_name}", style="cyan")

            info_panel = Panel(
                info_text,
                title="Build Configuration",
                border_style="blue",
            )
            self._console.print(info_panel)

            builder = Builder(config)

            total_deps = len(config.build_libs) + len(config.project_libs)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self._console,
            ) as progress:
                task1 = progress.add_task("Creating environment...", total=1)
                builder.create_temp_env()
                progress.update(task1, completed=1, description="✓ Environment ready")

                if total_deps > 0:
                    task2 = progress.add_task(
                        f"Installing {total_deps} dependencies...",
                        total=total_deps,
                    )
                    builder.install_dependencies_with_callback(
                        lambda dep, current, total: progress.update(
                            task2,
                            completed=current,
                            description=f"Installing {dep} ({current}/{total})...",
                        ),
                    )
                    progress.update(
                        task2,
                        completed=total_deps,
                        description="✓ Dependencies installed",
                    )
                else:
                    task2 = progress.add_task("No dependencies to install", total=1)
                    progress.update(task2, completed=1)

                task3 = progress.add_task("Compiling with Nuitka...", total=1)
                builder.build_with_nuitka()
                progress.update(
                    task3,
                    completed=1,
                    description="✓ Compilation complete",
                )

                task4 = progress.add_task("Cleaning up...", total=1)
                builder.cleanup()
                progress.update(task4, completed=1, description="✓ Cleanup finished")

            output_path = Path(config.output_name).absolute()
            file_size = output_path.stat().st_size if output_path.exists() else 0
            size_mb = file_size / (1024 * 1024)

            success_text = Text()
            success_text.append("Build completed successfully!\n\n", style="bold green")
            success_text.append("Output: ", style="bold")
            success_text.append(f"{output_path}\n", style="cyan")
            success_text.append("Size: ", style="bold")
            success_text.append(f"{size_mb:.2f} MB", style="cyan")

            success_panel = Panel(success_text, title="Success", border_style="green")
            self._console.print(success_panel)

        except KeyboardInterrupt:
            self._console.print("\n[yellow]Build interrupted by user[/yellow]")
            sys.exit(1)

        except FileNotFoundError as exception:
            self._print_error(
                "File not found",
                [str(exception)],
                "Check that all required files exist in your project.",
            )
            sys.exit(1)

        except ValueError as exception:
            self._print_error(
                "Configuration error",
                [str(exception)],
                "Check your config.yaml file for missing or invalid fields.",
            )
            sys.exit(1)

        except RuntimeError as exception:
            self._print_error(
                "Build failed",
                [str(exception)],
                "Check that:\n  • All dependencies are available\n  • Nuitka is properly installed\n  • You have sufficient disk space",
            )
            sys.exit(1)

        except Exception as exception:
            self._print_error(
                "Unexpected error",
                [str(exception)],
                "Please report this issue with the error details above.",
            )
            sys.exit(1)

    def show_info(self, config_path: str) -> None:
        try:
            config = BuilderConfig(config_path)

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")

            table.add_row("Project Name", config.project_name)

            main_path = Path(config.main_file).absolute()
            main_exists = main_path.exists()
            main_status = "✓" if main_exists else "✗"
            main_display = f"{main_status} {main_path}"
            table.add_row("Main File", main_display)

            output_path = Path(config.output_name).absolute()
            output_exists = output_path.exists()
            output_status = "✓" if output_exists else "✗"
            if output_exists:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                output_display = f"{output_status} {output_path} ({size_mb:.2f} MB)"
            else:
                output_display = f"{output_status} {output_path}"
            table.add_row("Output File", output_display)

            if config.icon_file:
                icon_path = Path(config.icon_file).absolute()
                icon_exists = icon_path.exists()
                icon_status = "✓" if icon_exists else "✗"
                icon_display = f"{icon_status} {icon_path}"
                table.add_row("Icon File", icon_display)
            else:
                table.add_row("Icon File", "[dim]Not configured[/dim]")

            build_deps = len(config.build_libs)
            project_deps = len(config.project_libs)
            total_deps = build_deps + project_deps
            deps_display = f"{total_deps} total ({build_deps} build, {project_deps} project)"
            table.add_row("Dependencies", deps_display)

            if config.project_libs:
                deps_list = ", ".join(config.project_libs[:5])
                if len(config.project_libs) > 5:
                    deps_list += f" ... (+{len(config.project_libs) - 5} more)"
                table.add_row("  Project libs", f"[dim]{deps_list}[/dim]")

            packages_count = len(config.include_packages)
            if packages_count > 0:
                packages_list = ", ".join(config.include_packages)
                table.add_row("Include Packages", f"{packages_count}: {packages_list}")
            else:
                table.add_row("Include Packages", "[dim]None[/dim]")

            data_dirs_count = len(config.include_data_dirs)
            if data_dirs_count > 0:
                data_dirs_list = ", ".join(config.include_data_dirs)
                table.add_row(
                    "Data Directories",
                    f"{data_dirs_count}: {data_dirs_list}",
                )
            else:
                table.add_row("Data Directories", "[dim]None[/dim]")

            self._console.print(table)

        except FileNotFoundError as exception:
            self._print_error(
                "Config file not found",
                [str(exception)],
                "Create a config.yaml file in your project root.",
            )

        except ValueError as exception:
            self._print_error(
                "Invalid configuration",
                [str(exception)],
                "Check your config.yaml for missing required fields.",
            )

        except Exception as exception:
            self._print_error("Failed to load project info", [str(exception)])

    def run(self) -> None:
        """Main CLI entry point."""
        parser = argparse.ArgumentParser(
            description="PyNexe - Python to Native Executable Builder",
            add_help=False,
        )
        parser.add_argument(
            "command",
            nargs="?",
            choices=["run", "info", "help"],
            help="Command to execute",
        )
        parser.add_argument(
            "--config",
            "-c",
            default="config.yaml",
            help="Config file (default: config.yaml)",
        )
        parser.add_argument("--help", "-h", action="store_true", help="Show help")

        args = parser.parse_args()

        if args.help or args.command == "help" or not args.command:
            self.print_help()
            return

        self.print_banner()

        config_path = Path(args.config)
        if not config_path.exists():
            self._print_error(
                "Config file not found",
                [str(config_path)],
                "Create a config.yaml file in your project root.",
            )
            sys.exit(1)

        if args.command == "run":
            self.build_project(args.config)
        elif args.command == "info":
            self.show_info(args.config)

    def _validate_build_files(self, config: BuilderConfig) -> list[str]:
        issues = []

        if not Path(config.main_file).exists():
            issues.append(f"Main file not found: {config.main_file}")

        if config.icon_file and not Path(config.icon_file).exists():
            issues.append(f"Icon file not found: {config.icon_file}")

        for data_dir in config.include_data_dirs:
            source_path, _ = parse_data_dir_entry(data_dir)
            if not Path(source_path).exists():
                issues.append(f"Data directory not found: {source_path}")

        return issues


def main():
    """Entry point."""
    cli = PyNexeCLI()
    cli.run()


if __name__ == "__main__":
    main()
