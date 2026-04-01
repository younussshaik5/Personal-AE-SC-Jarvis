"""JARVIS MCP - Setup configuration"""

from setuptools import setup, find_packages

setup(
    name="jarvis-mcp",
    version="1.0.0",
    description="Production-ready MCP server with 24 sales intelligence skills",
    author="JARVIS Team",
    author_email="jarvis@example.com",
    url="https://github.com/your-org/jarvis-mcp",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "openai>=1.0.0",
        "pyyaml>=6.0",
        "aiohttp>=3.8.0",
        "pydantic>=2.0.0",
        "mcp>=0.7.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "autopep8>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "jarvis-mcp=jarvis_mcp.mcp_server:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
