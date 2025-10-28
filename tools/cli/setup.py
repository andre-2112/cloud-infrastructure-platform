"""Setup script for Cloud CLI"""
from setuptools import setup, find_packages

setup(
    name="cloud-cli",
    version="0.7.0",
    description="Cloud Platform CLI Tool",
    author="Cloud Platform Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "cloud-core>=0.7.0",  # Shared business logic
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cloud=cloud_cli.main:app",
        ],
    },
)
