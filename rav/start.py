import pathlib

import yaml
from rich import print as rich_print
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def verify_project_empty(path=".", project_file="rav.yaml"):
    """Verify that the current directory contains a rav.yaml file"""
    rav_yaml_path = pathlib.Path(path).resolve() / project_file
    if rav_yaml_path.exists():
        return False
    return True


sample_shortcuts = {
    "server": "python manage.py runserver --settings=cfehome.settings.dev 8881",
    "installs": "venv/bin/python -m pip install pip --upgrade && venv/bin/python -m pip install -r requirements.txt",
    "rollout": "KUBECONFIG=~/.kube/config kubectl rollout restart deployment/cfehome-web",
}


def confirm_or_exit(prompt_text, *args, **kwargs):
    try:
        return Confirm.ask(prompt_text, console=console, *args, **kwargs)
    except KeyboardInterrupt:
        return False
    except EOFError:
        return False


def start_project_wizard(path="."):
    default = pathlib.Path(path).resolve().name
    project_name = Prompt.ask(
        "Enter your project name", default=default, console=console
    )
    # project_type = Prompt.ask("Enter a shortcut")
    project_details = {
        "name": project_name,
        "scripts": {},
    }
    keep_going = True
    rich_print("Let's generate a few shortcut commands. Here are some ideas: \n")
    for k, v in sample_shortcuts.items():
        rich_print(f"[bold]Shortcut[/bold]\t[cyan]{k}[/cyan]")
        rich_print(f"[bold]Command [/bold]\t[green]{v}[/green]")
        print("")

    while keep_going:
        shortcut_name = Prompt.ask("Your [cyan]shortcut[/cyan]", console=console)
        if not shortcut_name:
            continue
        script = Prompt.ask(
            "The [green]command[/green]",
            console=console,
        )
        if not script:
            keep_going = False
            break
        print("")
        # rich_print(f"[bold]New shortcut[/bold]\t[cyan]{shortcut_name}[/cyan]")
        rich_print(f"[green]{script}[/green]")
        rich_print("[italic]is now also[/italic]")
        rich_print(f"[bold][blue]rav run {shortcut_name}[/blue][/bold]")
        print("")
        command_ready = Confirm.ask("Add shortcut?", default=True, console=console)
        if not command_ready:
            continue
        project_details["scripts"][shortcut_name] = script
        keep_going = confirm_or_exit("Add another?", default=False)
        # keep_going = input_or_exit("Enter another command? (y/n): ").lower() == "y"
    return project_details


def start_new(path=".", overwrite=False, project_file="rav.yaml"):
    dest = pathlib.Path(path).resolve()
    output_path = dest / project_file
    rich_print(
        ":rocket: Starting new [bold][italic]rav[/italic][/bold] project at:\n\n",
        output_path,
        "\n",
    )
    is_empty = verify_project_empty(path, project_file=project_file)
    if not is_empty and not overwrite:
        """
        Rav project already exists here.
        If force re-create, use the --overwrite flag.
        """
        rich_print(
            f":warning: Existing [bold][italic]rav[/italic][/bold] project ([cyan]{project_file}[/cyan]) found."
        )
        rich_print(":warning: Use the --overwrite flag to re-create the project.")
        return

    """Create a sample rav.yaml file"""
    project_details = start_project_wizard(path=path)
    new_output = yaml.dump(project_details)
    rich_print("Here is your new Rav project:\n")
    rich_print(new_output)
    final_confirm = "Save project?"
    if overwrite:
        final_confirm = "Save and overwrite?"
    ready_to_go = confirm_or_exit(final_confirm)
    if not ready_to_go:
        rich_print("Exiting...")
        return
    output_path.write_text(new_output)
