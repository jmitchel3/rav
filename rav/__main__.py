import sys

import fire

from rav import __version__
from rav.cli import RavCLI


def main():
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"rav {__version__}")
        return
    fire.Fire(RavCLI)


if __name__ == "__main__":
    main()
