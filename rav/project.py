import pathlib
import subprocess
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

    def __init__(self, project_file: pathlib.Path, join_arg: str = " && "):
        super().__init__()
        self.join_arg = join_arg
        self._file = project_file
        # Use pathlib to get current working directory
        self.cwd = pathlib.Path.cwd()

        # Log welcome message
        rich_print("------------------[bold cyan]rav[/bold cyan]------------------")
        rich_print(f"Using [bold green]{project_file}[/bold green]\n")

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
            if isinstance(value, list):
                table.add_row(f"{cmd}", self.join_commands(value))
            else:
                table.add_row(f"{cmd}", value)
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
        commands = scripts[cmd]
        if isinstance(commands, list):
            if isinstance(args, tuple):
                commands = [f'{cmd} {" ".join(args)}' for cmd in commands]
            commands = self.join_commands(commands)
        elif isinstance(commands, str):
            if isinstance(args, tuple):
                commands = f'{commands} {" ".join(args)}'
        rich_print(f"Running [bold green]{commands}[/bold green]")
        try:
            subprocess.run(commands, shell=True, check=True)
            rich_print("---------------------------------------")
            rich_print("Status: [bold green]Success![/bold green]")
            rich_print("---------------------------------------")
            # rich_print(f"{result}")
        except subprocess.CalledProcessError as e:
            rich_print("---------------------------------------")
            rich_print("Status: [bold red]Error[/bold red]")
            rich_print("---------------------------------------")
            rich_print(f"{e}")
            raise

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
