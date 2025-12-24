"""Setup configuration for walletkit."""
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
    install_requires=[
        "websockets>=11.0.0",
        "cryptography>=41.0.0",
        "aiohttp>=3.9.0",
        "msgpack>=1.0.0",
        "base58>=2.1.0",
    ],
)

