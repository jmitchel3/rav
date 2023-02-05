import argparse
import pathlib
import subprocess

import yaml


def make_sample(force=False):
    
    sample_project = {
        "name": "rav",
        "scripts": {
            "server": "python3 -m http.server"
        }
    }
    rav_sample_path = pathlib.Path("rav.sample.yaml")
    if rav_sample_path.exists() and not force:
        print("Error: rav.sample.yaml already exists. Use --force to overwrite.")
        return
    if force:
        print("Forcing overwrite of rav.sample.yaml")
    print("Creating a sample project at:\n\n", rav_sample_path.absolute(), "\n")
    rav_sample_path.write_text(yaml.dump(sample_project))

def main():
    parser = argparse.ArgumentParser(description="Run scripts from a YAML file")
    parser.add_argument("mode", type=str, choices=["run", "sample"], help="The mode to run the script in")
    parser.add_argument("script", type=str, help="The script to run.")
    parser.add_argument("--verbose", type=bool, help="Print the command being run", default=False)
    parser.add_argument("--force", type=bool, help="Force action (not always possible)", default=False)
    args = parser.parse_args()
    cmd = args.script
    verbose = args.verbose
    if args.mode == "sample":
        make_sample(args.force)
        return
    if args.mode == 'run':
        if not cmd:
            print("Error: no script provided")
            return
        with open("rav.yaml", "r") as f:
            project = yaml.safe_load(f)
            scripts = project.get("scripts") or project.get("scripts") or {}
            # print(project)
        try:
            command = scripts[cmd]
        except KeyError:
            print(f"Error: script '{cmd}' not found")
            return
        if isinstance(command, list):
            command = " && ".join(command)
        if verbose:
            print(f"Running script: {command}")
        subprocess.run(command, shell=True)

if __name__ == "__main__":
    main()