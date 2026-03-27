#!/usr/bin/env python3
"""
JARVIS - Autonomous AI Employee System
Setup configuration for pip installation.
"""

from setuptools import setup, find_packages

setup(
    name="jarvis",
    version="2.0.0",
    description="Autonomous AI Employee System with MCP integration",
    author="OpenCode Team",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "websockets>=12.0",
        "watchdog>=4.0.0",
        "pyyaml>=6.0",
        "aiohttp>=3.9.0",
        "python-telegram-bot>=20.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black>=23.0", "mypy>=1.0"],
        "ml": ["sentence-transformers>=2.2", "numpy>=1.24"],
    },
    entry_points={
        "console_scripts": [
            "jarvis=jarvis.cli.main:main",
        ],
    },
)