import os
import pathlib
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass

import requests
import yaml
from rich import print as rich_print
from rich.pretty import pprint as rich_pprint
from rich.table import Table

from .integrity import IntegrityVerifier


@dataclass
class Project:
    """
    A rav project in the current directory.
    """

    join_arg: str = " && "
    _file: pathlib.Path = None
    _project: dict = None
    verbose: bool = False
    traceback: bool = False

    def __init__(self, project_file: pathlib.Path, join_arg: str = " && ", verbose: bool = False, traceback: bool = False):
        super().__init__()
        self.join_arg = join_arg
        self.verbose = verbose
        self.traceback = traceback
        self._file = project_file
        # Use pathlib to get current working directory
        self.cwd = pathlib.Path.cwd()

        # Open project file and load YAML
        if self._file.exists():
            yaml_data = self._file.read_text()
            self._project = yaml.safe_load(yaml_data)

    def detail(self):
        rich_pprint(self._project)

    def scripts(self):
        return (
            self._project.get("rav")
            or self._project.get("scripts")
            or self._project.get("commands")
            or {}
        )

    def get_variables(self):
        """Get variables from YAML config, with environment variables as fallback.

        Variables defined in YAML take precedence over environment variables.
        Supports both 'vars' and 'variables' as the key name.
        """
        variables = dict(os.environ)  # Start with env vars
        yaml_vars = self._project.get("vars") or self._project.get("variables") or {}
        if yaml_vars:
            # Convert all values to strings and update
            variables.update({k: str(v) for k, v in yaml_vars.items()})
        return variables

    def substitute_variables(self, value):
        """Substitute ${{ vars.NAME }} patterns in a string.

        Returns the string with all variable references replaced.
        Raises an error if a referenced variable is not defined.
        """
        if not isinstance(value, str):
            return value

        pattern = r'\$\{\{\s*vars\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        variables = self.get_variables()

        def replace_var(match):
            var_name = match.group(1)
            if var_name not in variables:
                raise ValueError(f"Undefined variable: {var_name}")
            return variables[var_name]

        return re.sub(pattern, replace_var, value)

    def is_group_definition(self, value):
        """Check if a script entry is a group definition.

        A group definition is a dict that has at least one of:
        prefix, working_dir, or cmd keys.
        """
        if not isinstance(value, dict):
            return False
        group_keys = {"prefix", "working_dir", "cmd"}
        return bool(group_keys & set(value.keys()))

    def get_group_name(self, cmd):
        """Extract group name from a command.

        'backend:migrate' -> 'backend'
        'backend:env:overwrite' -> 'backend'
        'echo' -> None
        """
        if ":" not in cmd:
            return None
        return cmd.split(":")[0]

    def get_group_config(self, group_name):
        """Get the configuration for a group if it exists.

        Group definitions can be either 'groupname' or 'groupname:' in YAML.
        Returns dict with prefix, working_dir, or None if group doesn't exist.
        """
        if not group_name:
            return None
        scripts = self.scripts()
        # Try both 'groupname' and 'groupname:' as valid group definition keys
        group_value = scripts.get(group_name) or scripts.get(f"{group_name}:")
        if not group_value:
            return None
        if not self.is_group_definition(group_value):
            return None
        return group_value

    def resolve_command_config(self, cmd):
        """Resolve the full configuration for a command, including inheritance.

        Returns a dict with:
        - commands: list of command strings to run
        - working_dir: directory to run in (or None)
        - prefix: prefix to prepend (or None)
        """
        scripts = self.scripts()
        value = scripts.get(cmd)

        # Get group config if applicable
        group_name = self.get_group_name(cmd)
        group_config = self.get_group_config(group_name)

        # Start with group defaults
        working_dir = group_config.get("working_dir") if group_config else None
        prefix = group_config.get("prefix") if group_config else None

        # Determine the actual commands
        if isinstance(value, str):
            # Simple string command
            commands = [value]
        elif isinstance(value, list):
            # List of commands - extract cmd from any dict items
            commands = []
            for item in value:
                if isinstance(item, dict):
                    cmd_val = item.get("cmd")
                    if isinstance(cmd_val, list):
                        commands.extend(cmd_val)
                    elif cmd_val:
                        commands.append(cmd_val)
                else:
                    commands.append(item)
        elif isinstance(value, dict):
            # Dict format - may override group settings
            # Check for prefix override (empty string means no prefix)
            if "prefix" in value:
                prefix = value.get("prefix") or None
            # Check for working_dir override
            if "working_dir" in value:
                working_dir = value.get("working_dir")
            # Get the command(s)
            cmd_value = value.get("cmd")
            if isinstance(cmd_value, str):
                commands = [cmd_value]
            elif isinstance(cmd_value, list):
                commands = cmd_value
            else:
                commands = []
        else:
            commands = []

        return {
            "commands": commands,
            "working_dir": working_dir,
            "prefix": prefix,
        }

    def apply_prefix_and_working_dir(self, commands, prefix=None, working_dir=None):
        """Apply prefix and working_dir to a list of commands.

        Returns a single command string ready for execution.
        Variables are substituted using ${{ vars.NAME }} syntax.
        """
        processed = []
        for cmd in commands:
            # Substitute variables in the command
            cmd = self.substitute_variables(cmd)
            if prefix:
                # Substitute variables in the prefix too
                prefix = self.substitute_variables(prefix)
                cmd = f"{prefix} {cmd}"
            processed.append(cmd)

        # Join commands
        joined = self.join_commands(processed)

        # Prepend working_dir change if specified
        if working_dir:
            # Substitute variables in working_dir
            working_dir = self.substitute_variables(working_dir)
            joined = f"cd {working_dir} && {joined}"

        return joined

    def get_download_config(self):
        return self._project.get("downloads", {})

    def list_download_config(self):
        download_config = self.get_download_config()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan")
        table.add_column("Script")
        for cmd, value in download_config.items():
            table.add_row(f"{cmd}", value)
        rich_print()
        rich_print(table)

    def join_commands(self, commands):
        return f"{self.join_arg}".join(commands)

    def list(self, expanded=False):
        rich_print("Viewing available commands via [cyan]rav list[/cyan]")
        scripts = self.scripts()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan")
        table.add_column("Script")
        for cmd, value in scripts.items():
            if expanded:
                # Show fully resolved command with prefix and working_dir
                config = self.resolve_command_config(cmd)
                resolved = self.apply_prefix_and_working_dir(
                    config["commands"],
                    prefix=config["prefix"],
                    working_dir=config["working_dir"],
                )
                table.add_row(f"{cmd}", resolved)
            elif self.is_group_definition(value):
                # Show group definition info
                parts = []
                if value.get("working_dir"):
                    parts.append(f"[dim]cd {value['working_dir']}[/dim]")
                if value.get("prefix"):
                    parts.append(f"[dim]{value['prefix']}[/dim]")
                if value.get("cmd"):
                    cmd_val = value["cmd"]
                    if isinstance(cmd_val, list):
                        parts.append(self.join_commands(cmd_val))
                    else:
                        parts.append(cmd_val)
                table.add_row(f"{cmd}", " → ".join(parts) if parts else "[dim](group)[/dim]")
            elif isinstance(value, list):
                # Handle lists that may contain dict items
                display_items = []
                for item in value:
                    if isinstance(item, dict):
                        # Dict item - show cmd value or repr
                        if "cmd" in item:
                            cmd_val = item["cmd"]
                            if isinstance(cmd_val, list):
                                display_items.append(self.join_commands(cmd_val))
                            else:
                                display_items.append(str(cmd_val))
                        else:
                            display_items.append(str(item))
                    else:
                        display_items.append(str(item))
                table.add_row(f"{cmd}", self.join_commands(display_items))
            elif isinstance(value, dict) and "cmd" in value:
                # Dict with cmd key
                cmd_val = value["cmd"]
                if isinstance(cmd_val, list):
                    table.add_row(f"{cmd}", self.join_commands(cmd_val))
                else:
                    table.add_row(f"{cmd}", str(cmd_val))
            else:
                table.add_row(f"{cmd}", str(value) if value else "")
        rich_print()
        rich_print(table)

    def run(self, cmd, *args, **kwargs):
        scripts = self.scripts()
        if cmd not in scripts:
            self.list()
            rich_print(
                "\n----------------:warning: Error----------------\n",
                f"[bold red]'{cmd}'[/bold red] is not a valid script. Review the valid ones above. or use [cyan]rav list[/cyan].",
            )
            rich_print("---------------------------------------\n")
            return

        # Resolve command config with group inheritance
        config = self.resolve_command_config(cmd)
        command_list = config["commands"]
        working_dir = config["working_dir"]
        prefix = config["prefix"]

        # Append any extra args to the last command
        if args:
            args_str = " ".join(args)
            if command_list:
                command_list[-1] = f"{command_list[-1]} {args_str}"

        # Apply prefix and working_dir
        commands = self.apply_prefix_and_working_dir(
            command_list, prefix=prefix, working_dir=working_dir
        )

        if self.verbose:
            rich_print("------------------[bold cyan]rav[/bold cyan]------------------")
            rich_print(f"Using: [bold green]{self._file}[/bold green]")
            if working_dir:
                rich_print(f"Working dir: [bold blue]{working_dir}[/bold blue]")
            if prefix:
                rich_print(f"Prefix: [bold blue]{prefix}[/bold blue]")
            rich_print(f"Running: [bold green]{commands}[/bold green]\n")

        try:
            subprocess.run(commands, shell=True, check=True)

            if self.verbose:
                rich_print("\n[bold green]✓ Command completed successfully[/bold green]")
        except KeyboardInterrupt:
            # User pressed Ctrl+C to stop the process
            rich_print("\n\n[yellow]⏸  Stopped by user (Ctrl+C)[/yellow]")
            sys.exit(130)  # Standard exit code for SIGINT
        except subprocess.CalledProcessError as e:
            # Error output has already been printed by the command
            if self.verbose:
                rich_print(f"\n[bold red]✗ Error: Command failed with exit code {e.returncode}[/bold red]")
                if not self.traceback:
                    rich_print(f"[dim]Tip: Use --traceback to see full Python traceback[/dim]")
            else:
                rich_print(f"\n[bold red]✗ Command failed with exit code {e.returncode}[/bold red]")

            if self.traceback:
                rich_print("\n[dim]Python traceback:[/dim]")
                raise
            else:
                sys.exit(e.returncode if e.returncode else 1)

    def download(self, cmd, *args, **kwargs):
        download_config = self.get_download_config()
        if cmd not in download_config:
            self.list_download_config()
            rich_print(
                "\n----------------:warning: Error----------------\n",
                f"[bold red]'{cmd}'[/bold red] is not a valid download config. Review the valid ones above. or use [cyan]rav list[/cyan].",
            )
            rich_print("---------------------------------------\n")
            return

        download_item = download_config[cmd]
        overwrite = download_item.get("overwrite", False)
        verbose = download_item.get(
            "verbose", True
        )  # Default to True for backward compatibility
        raise_on_error = download_item.get(
            "raise_on_error", False
        )  # Default to False for backward compatibility
        destination = download_item.get("destination")
        destination_path = pathlib.Path(destination)
        destination_path.mkdir(parents=True, exist_ok=True)
        files = download_item.get("files", [])

        # Header message
        rich_print(
            f"\n[bold cyan]📥 Starting download:[/bold cyan] [yellow]{cmd}[/yellow]"
        )
        if verbose:
            rich_print(f"[dim]Destination:[/dim] [green]{destination}[/green]")
            rich_print(f"[dim]Files to download:[/dim] [cyan]{len(files)}[/cyan]")
            rich_print(
                f"[dim]Overwrite existing:[/dim] [{'yellow' if overwrite else 'red'}]{overwrite}[/{'yellow' if overwrite else 'red'}]"
            )
            rich_print(f"[dim]Verbose mode:[/dim] [cyan]{verbose}[/cyan]")
            rich_print(
                f"[dim]Raise on error:[/dim] [{'red' if raise_on_error else 'yellow'}]{raise_on_error}[/{'red' if raise_on_error else 'yellow'}]\n"
            )
        else:
            rich_print(f"[dim]Downloading {len(files)} files...[/dim]\n")

        downloaded_count = 0
        skipped_count = 0

        for i, file in enumerate(files, 1):
            url = file.get("url")
            filename = file.get("filename") or file.get("name")
            destination_override = file.get("destination")
            overwrite_override = file.get("overwrite")
            integrity = file.get("integrity") or None
            if destination_override:
                destination_path = pathlib.Path(destination_override)
                destination_path.mkdir(parents=True, exist_ok=True)
                if verbose:
                    rich_print(
                        f"[dim]   → Using destination from file config:[/dim] [cyan]{destination_path}[/cyan]"
                    )
            if overwrite_override:
                overwrite = overwrite_override
                if verbose:
                    rich_print(
                        f"[dim]   → Using overwrite from file config:[/dim] [cyan]{overwrite}[/cyan]"
                    )

            if not filename:
                if verbose:
                    rich_print(
                        f"[yellow]⚠️  No filename found for:[/yellow] [dim]{url}[/dim]"
                    )
                filename = pathlib.Path(url).name
                if verbose:
                    rich_print(
                        f"[dim]   → Using filename from URL:[/dim] [cyan]{filename}[/cyan]"
                    )

            final_download_path = destination_path / filename

            if verbose:
                rich_print(f"[bold cyan][{i}/{len(files)}][/bold cyan] ", end="")

            if final_download_path.exists() and not overwrite:
                if verbose:
                    rich_print(
                        f"[yellow]⏭️  Skipping existing file:[/yellow] [dim]{filename}[/dim]"
                    )
                else:
                    rich_print(f"[yellow]⏭️  Skipping:[/yellow] [cyan]{filename}[/cyan]")
                skipped_count += 1
                continue

            try:
                if verbose:
                    rich_print(f"[blue]⬇️  Downloading:[/blue] [cyan]{filename}[/cyan]")
                    rich_print(f"[dim]   → From:[/dim] [dim]{url}[/dim]")
                else:
                    rich_print(f"[blue]⬇️[/blue] [cyan]{filename}[/cyan]")

                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad status codes

                # Determine download path: temp if integrity check needed, final otherwise
                if integrity:
                    # Download to temporary file for integrity verification
                    temp_dir = pathlib.Path(tempfile.gettempdir()) / "rav_downloads"
                    temp_dir.mkdir(exist_ok=True)
                    download_path = temp_dir / filename
                    if verbose:
                        rich_print(
                            f"[dim]   → Downloading to temp for verification:[/dim] [dim]{download_path}[/dim]"
                        )
                else:
                    download_path = final_download_path

                # Write the downloaded content
                with open(download_path, "wb") as f:
                    f.write(response.content)

                # Verify integrity if specified
                if integrity:
                    if verbose:
                        rich_print(
                            f"[dim]   → Integrity:[/dim] [cyan]{integrity}[/cyan]"
                        )
                    try:
                        integrity_info = IntegrityVerifier.get_integrity_info(
                            download_path, integrity
                        )
                        if "error" in integrity_info:
                            error_msg = f"[red]   ❌ Integrity error:[/red] [dim]{integrity_info['error']}[/dim]"
                            if verbose:
                                rich_print(error_msg)
                            else:
                                rich_print(
                                    f"[red]❌ Integrity error:[/red] [cyan]{filename}[/cyan]"
                                )
                            # Clean up temp file on error
                            try:
                                download_path.unlink()
                            except FileNotFoundError:
                                pass
                            if raise_on_error:
                                raise ValueError(
                                    f"Integrity error for {filename}: {integrity_info['error']}"
                                )
                            continue
                        elif not integrity_info["is_valid"]:
                            error_msg = f"[red]   ❌ Integrity check failed:[/red] [dim]{integrity_info['actual_hash']}[/dim] != [dim]{integrity_info['expected_hash']}[/dim]"
                            if verbose:
                                rich_print(error_msg)
                            else:
                                rich_print(
                                    f"[red]❌ Integrity failed:[/red] [cyan]{filename}[/cyan]"
                                )
                            # Clean up temp file on failure
                            try:
                                download_path.unlink()
                            except FileNotFoundError:
                                pass
                            if raise_on_error:
                                raise ValueError(
                                    f"Integrity check failed for {filename}: {integrity_info['actual_hash']} != {integrity_info['expected_hash']}"
                                )
                            continue
                        else:
                            if verbose:
                                rich_print(
                                    f"[green]   ✅ Integrity verified[/green] [dim]({integrity_info['algorithm']})[/dim]"
                                )
                                # Move verified file to final destination
                                rich_print(
                                    f"[dim]   → Downloaded to final destination:[/dim] [green]{final_download_path}[/green]"
                                )
                            if final_download_path.exists():
                                final_download_path.unlink()  # Remove existing file if overwrite is true
                            download_path.replace(final_download_path)
                            download_path = final_download_path  # Update path for file size reporting
                    except Exception as e:
                        error_msg = f"[red]   ❌ Integrity verification failed:[/red] [dim]{str(e)}[/dim]"
                        if verbose:
                            rich_print(error_msg)
                        else:
                            rich_print(
                                f"[red]❌ Verification failed:[/red] [cyan]{filename}[/cyan]"
                            )
                        # Clean up temp file on exception
                        try:
                            download_path.unlink()
                        except FileNotFoundError:
                            pass
                        if raise_on_error:
                            raise ValueError(
                                f"Integrity verification failed for {filename}: {str(e)}"
                            )
                        continue

                file_size = download_path.stat().st_size
                if verbose:
                    rich_print(
                        f"[green]   ✅ Success![/green] [dim]({file_size:,} bytes)[/dim]"
                    )
                else:
                    rich_print(
                        f"[green]✅[/green] [cyan]{filename}[/cyan] [dim]({file_size:,} bytes)[/dim]"
                    )
                downloaded_count += 1

            except requests.exceptions.RequestException as e:
                error_msg = f"[red]   ❌ Failed to download:[/red] [dim]{str(e)}[/dim]"
                if verbose:
                    rich_print(error_msg)
                else:
                    rich_print(
                        f"[red]❌ Download failed:[/red] [cyan]{filename}[/cyan]"
                    )
                if raise_on_error:
                    raise requests.exceptions.RequestException(
                        f"Failed to download {filename}: {str(e)}"
                    )
            except Exception as e:
                error_msg = f"[red]   ❌ Error saving file:[/red] [dim]{str(e)}[/dim]"
                if verbose:
                    rich_print(error_msg)
                else:
                    rich_print(f"[red]❌ Save error:[/red] [cyan]{filename}[/cyan]")
                if raise_on_error:
                    raise Exception(f"Error saving file {filename}: {str(e)}")

        # Summary
        rich_print("\n---------------------------------------")
        rich_print("[bold green]📊 Download Summary:[/bold green]")
        rich_print(
            f"[green]   ✅ Downloaded:[/green] [bold]{downloaded_count}[/bold] files"
        )
        if skipped_count > 0:
            rich_print(
                f"[yellow]   ⏭️  Skipped:[/yellow] [bold]{skipped_count}[/bold] files"
            )
        rich_print("---------------------------------------\n")

        # Clean up any remaining temp files
        try:
            temp_dir = pathlib.Path(tempfile.gettempdir()) / "rav_downloads"
            if temp_dir.exists():
                # Only remove files, not the directory itself
                for temp_file in temp_dir.iterdir():
                    if temp_file.is_file():
                        try:
                            temp_file.unlink()
                        except FileNotFoundError:
                            pass
        except Exception:
            pass  # Ignore cleanup errors
