"""Setup configuration for walletkit."""
from setuptools import find_packages, setup

setup(
    name="walletkit",
    version="0.1.0",
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

