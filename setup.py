"""Setup configuration for VC Sentiment Podcast Generator."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="vc-sentiment-podcast",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated podcast generator for VC sentiment analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zaneinthebay/vc-sentiment-podcast",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vc-podcast=src.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
