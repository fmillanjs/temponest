"""Setup configuration for TempoNest shared modules."""

from setuptools import setup, find_packages

setup(
    name="temponest-shared",
    version="0.1.0",
    description="Shared modules for TempoNest services",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "redis[hiredis]>=5.0.0,<6.0.0",
    ],
)
