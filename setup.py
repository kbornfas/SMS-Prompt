#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="sms-prompt-cli",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A powerful CLI tool to send customized SMS prompts with variable interpolation, bulk sending, and analytics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kbornfas/SMS-Prompt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Telephony",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "sms-prompt=cli.main:main",
        ],
    },
    include_package_data=True,
    keywords="sms, cli, twilio, messaging, bulk-sms, templates",
    project_urls={
        "Bug Reports": "https://github.com/kbornfas/SMS-Prompt/issues",
        "Source": "https://github.com/kbornfas/SMS-Prompt",
    },
)
