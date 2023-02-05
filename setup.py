from setuptools import find_packages, setup

setup(
    name="rav",
    description="A cross-platform Python CLI to shortcut tp command-line commands. Inspired by Makefiles and npm scripts.",
    author="Justin Mitchel",
    author_email="hello@teamcfe.com",
    url="https://github.com/jmitchel3/rav",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "rav=rav.__main__:main"
        ]
    },
    install_requires=[
        "PyYAML"
    ],
    python_requires=">=3.7",
)