"""
Temponest CLI - Setup
"""
from setuptools import setup, find_packages

setup(
    name="temponest-cli",
    version="1.0.0",
    description="Command-line tool for the Temponest Agentic Platform",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "temponest-sdk>=1.0.0",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "temponest=temponest_cli.cli:cli",
        ],
    },
    python_requires=">=3.8",
)
