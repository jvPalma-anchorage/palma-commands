from setuptools import setup, find_packages

setup(
    name="prs",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "nprs=prs.main:main",
        ],
    },
)
