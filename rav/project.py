import pathlib
import subprocess
from dataclasses import dataclass

import yaml
from rich import print as rich_print
from rich.pretty import pprint as rich_pprint
from rich.table import Table


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
