"""
Setup configuration for Theodore v2 CLI application.
"""

from setuptools import setup, find_packages

setup(
    name="theodore-v2",
    version="2.0.0",
    description="AI Company Intelligence System",
    long_description="Theodore v2 - Advanced AI-powered company research and similarity discovery system with MCP integration",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
        "pydantic>=2.0",
        "aiohttp>=3.8",
        "colorama>=0.4"
    ],
    entry_points={
        'console_scripts': [
            'theodore=src.cli.main:cli',
        ],
    },
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-asyncio>=0.21',
            'black>=22.0',
            'mypy>=1.0'
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)