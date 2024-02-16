# add logging
import logging
import pathlib
from dataclasses import dataclass

import yaml
from rich import print as rich_print

from rav import start
from rav.project import Project

# Set log level
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)


@dataclass
class RavCLI:
    project_file = "rav.yaml"
    project = None
    join_arg = " && "
    verbose = False
    overwrite = False

    def __init__(
        self,
        project_file="rav.yaml",
        project=None,
        f=None,
        join_arg=" && ",
        verbose=False,
        overwrite=False,
    ):
        super().__init__()
        self.join_arg = join_arg
        self.verbose = verbose
        self.overwrite = overwrite
        self.project_file = f or project or project_file

    def setup_project(self, project_file):
        self.project_file = pathlib.Path(project_file)
        if not self.project_file.exists():
            raise Exception(f"Error: rav project file '{project_file}' not found.")
        self.project = Project(project_file=self.project_file, join_arg=self.join_arg)

    def version(
        self,
    ):
        import rav

        rich_print(f"[bold]Version[/bold] {rav.__version__}")

    def get_project(self):
        if self.project is None:
            self.setup_project(self.project_file)
        return self.project

    def run(self, cmd, *args, **kwargs):
        self.get_project().run(cmd, *args, **kwargs)

    def x(self, cmd, *args, **kwargs):
        """Shortcut for run"""
        self.run(cmd, *args, **kwargs)

    def list(
        self,
    ):
        self.get_project().list()

    def new(self, path="."):
        project_file = self.project_file
        start.start_new(path=path, overwrite=self.overwrite, project_file=project_file)

    def sample(self, overwrite=False):
        """Create a sample rav.yaml file"""
        _overwrite = overwrite or self.overwrite or False
        sample_project = {
            "name": "rav",
            "scripts": {
                "echo": "echo 'Hello World!\nrav is working!'",
                "server": "python3 -m http.server",
                "win-server": "python -m http.server",
            },
        }
        rav_sample_path = pathlib.Path("rav.sample.yaml")
        if rav_sample_path.exists() and not _overwrite:
            rich_print(
                "Error: rav.sample.yaml already exists. Use --overwrite to continue."
            )
            return
        if _overwrite:
            rich_print("Forcing overwrite of rav.sample.yaml")
        rich_print(
            "Creating a sample project at:\n\n", rav_sample_path.absolute(), "\n"
        )
        rav_sample_path.write_text(yaml.dump(sample_project))
