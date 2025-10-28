"""
Setup script for cloud-core library - shared business logic
"""

from setuptools import setup, find_packages

setup(
    name="cloud-core",
    version="0.7.0",
    description="Cloud Platform Core Business Logic Library",
    author="Cloud Platform Team",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.0",
        "pyyaml>=6.0",
        "boto3>=1.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "mypy>=1.5.0",
        ],
    },
)
