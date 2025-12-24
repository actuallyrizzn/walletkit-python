"""Setup configuration for walletkit.

Note: Dependencies are defined in pyproject.toml, which is the single source of truth.
This setup.py is kept minimal for compatibility. Modern setuptools reads from pyproject.toml.
"""
from setuptools import find_packages, setup

# Read version from package __init__.py
def get_version():
    """Read version from walletkit.__init__."""
    import os
    import re
    
    init_path = os.path.join(os.path.dirname(__file__), "src", "walletkit", "__init__.py")
    with open(init_path, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    raise RuntimeError("Unable to find version string")

setup(
    name="walletkit",
    version=get_version(),
    description="WalletKit SDK for Python",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    # Dependencies are defined in pyproject.toml [project.dependencies]
    # This is the single source of truth for package dependencies
)

