"""Setup script for BEQ - Lean Equivalence Checker."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="beq",
    version="0.1.0",
    author="BEQ Team",
    author_email="",
    description="Lean Equivalence Checker - Verify formal theorem equivalence using LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/...",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "beq-check=equivalence.beq_basic:main",
        ],
    },
    include_package_data=True,
    package_data={
        "beq": ["data/**/*"],
    },
    keywords="lean theorem-proving formal-verification llm mathematics",
    project_urls={
        "Bug Reports": "https://github.com/.../issues",
        "Source": "https://github.com/.../",
    },
)
