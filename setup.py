from setuptools import find_packages, setup

setup(
    name="rav",
    version="0.0.1",
    description="A simple way to shortcut calling your various scripts. Inspired by npm scripts and make but simpler.",
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