"""Setup configuration for walletkit.

Note: Dependencies are defined in pyproject.toml, which is the single source of truth.
This setup.py is kept minimal for compatibility. Modern setuptools reads from pyproject.toml.
"""
from setuptools import find_packages, setup

setup(
    name="walletkit",
    version="0.1.0",
    description="WalletKit SDK for Python",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    # Dependencies are defined in pyproject.toml [project.dependencies]
    # This is the single source of truth for package dependencies
)

