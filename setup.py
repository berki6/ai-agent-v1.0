"""
CodeForge AI - Unified Modular AI Agent for Software Development
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


# Read requirements
def read_requirements(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Core requirements
install_requires = read_requirements("requirements.txt")

# Development requirements
dev_requires = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=22.0.0",
    "isort>=5.10.0",
    "flake8>=4.0.0",
    "mypy>=0.950",
]

setup(
    name="codeforge-ai",
    version="1.0.0",
    author="CodeForge AI Team",
    author_email="admin@codeforge.ai",
    description="Unified Modular AI Agent for Software Development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/berki6/ai-agent",
    project_urls={
        "Bug Tracker": "https://github.com/berki6/ai-agent/issues",
        "Documentation": "https://github.com/berki6/ai-agent#readme",
        "Source Code": "https://github.com/berki6/ai-agent",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities",
    ],
    keywords="ai, agent, development, automation, code, generation, analysis",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
        "web": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
            "jinja2>=3.0.0",
            "slowapi>=0.1.0",
            "langdetect>=1.0.0",
            "reportlab>=4.0.0",
        ],
        "all": install_requires + dev_requires,
    },
    entry_points={
        "console_scripts": [
            "codeforge=src.cli:main",
            "codeforge-ai=src.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
