import argparse
import pathlib
import subprocess
from dataclasses import dataclass
from enum import Enum

import fire
import yaml
from rich import print
from rich.console import Console
from rich.pretty import pprint
from rich.table import Table
from rich.text import Text


@dataclass
class Project:
    """
    A rav project in the current directory.
    """
    join_arg: str = " && "
    _file: pathlib.Path = None
    _project: dict = None

    def __init__(self, project_file:pathlib.Path, join_arg:str=" && "):
        super().__init__()
        self.join_arg = join_arg
        self._file = project_file
        cwd = pathlib.Path.cwd()
        print(f"------------------[bold cyan]rav[/bold cyan]------------------\nUsing [bold green]{project_file}[/bold green]")
        with open(self._file, "r") as f:
            self._project = yaml.safe_load(f)

    def detail(self):
        pprint(self._project)

    def scripts(self):
        return (
            self._project.get("rav") or 
            self._project.get("scripts") or 
            self._project.get('commands') or {}
        )
    
    def join_commands(self, commands):
        return f"{self.join_arg}".join(commands)

    def list(self, expanded=False):
        print("Viewing available commands via [cyan]rav list[/cyan]")
        scripts = self.scripts()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan")
        table.add_column("Script")
        for cmd, value in scripts.items():
            if isinstance(value, list):
                table.add_row(f"{cmd}", self.join_commands(value))
            else:
                table.add_row(f"{cmd}", value)
        print()
        print(table)

    def run(self, cmd, *args, **kwargs):
        scripts = self.scripts()
        if cmd not in scripts:
            self.list()
            print(f"\n----------------:warning: Error----------------\n", 
            f"[bold red]'{cmd}'[/bold red] is not a valid script. Review the valid ones above. or use [cyan]rav list[/cyan].")
            print(f"---------------------------------------\n")
            return
        commands = scripts[cmd]
        if isinstance(commands, list):
            if isinstance(args, tuple):
                commands = [f'{cmd} {" ".join(args)}' for cmd in commands]
            commands = self.join_commands(commands)
        elif isinstance(commands, str):
            if isinstance(args, tuple):
                commands =  f'{commands} {" ".join(args)}'
        print(f"Running [bold green]{commands}[/bold green]\n---------------------------------------")
        subprocess.run(commands, shell=True, check=True)


        
        


@dataclass
class RavCLI:
    project_file = "rav.yaml"
    project = None
    join_arg = " && "
    verbose = False
    overwrite = False


    def __init__(self, project_file="rav.yaml", f=None, join_arg=" && ", verbose=False, overwrite=False):
        super().__init__()
        self.join_arg = join_arg
        self.verbose = verbose
        self.overwrite = overwrite
        init_file = f or project_file
        self.setup_project(init_file)
    
    def setup_project(self, project_file):
        self.project_file = pathlib.Path(project_file)
        if not self.project_file.exists():
            raise Exception(f"Error: rav project file '{project_file}' not found.")
        self.project = Project(
                project_file=self.project_file, 
                join_arg=self.join_arg)

    def run(self, cmd, *args, **kwargs):
        self.project.run(cmd, *args, **kwargs)
    
    def list(self, ):
        self.project.list()
    
    def sample(self, overwrite=False):
        """Create a sample rav.yaml file"""
        _overwrite = overwrite or self.overwrite or False
        sample_project = {
            "name": "rav",
            "scripts": {
                "echo": "echo 'Hello World!\nrav is working!'",
                "server": "python3 -m http.server",
                "win-server": "python -m http.server",
            }
        }
        rav_sample_path = pathlib.Path("rav.sample.yaml")
        if rav_sample_path.exists() and not _overwrite:
            print("Error: rav.sample.yaml already exists. Use --overwrite to continue.")
            return
        if _overwrite:
            print("Forcing overwrite of rav.sample.yaml")
        print("Creating a sample project at:\n\n", rav_sample_path.absolute(), "\n")
        rav_sample_path.write_text(yaml.dump(sample_project))





def main():
    fire.Fire(RavCLI)

if __name__ == "__main__":
    main()