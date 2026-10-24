from setuptools import setup, find_packages

setup(
    name="dach-kredit",
    version="2026.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dach-kredit=kredit_dach.cli:main",
        ],
    },
)
