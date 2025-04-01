"""
ActivityWatch Procrastination Monitor installation configuration.
"""

from setuptools import setup, find_packages

setup(
    name="aw-watcher-procrastination",
    version="0.1.0",
    package_dir={"": "src"},  # Tell setuptools packages are under src/
    packages=find_packages(where="src"),  # Find packages under src/
    install_requires=[
        "aw-client>=0.5.13",
        "PyQt6>=6.6.1",
        "PyQt6-WebEngine>=6.6.0",
        "PyQt6-Charts>=6.6.0",
        "python-dateutil>=2.8.2",
        "typing-extensions>=4.5.0",
        "rich",  # For pretty printing
        "requests>=2.31.0",  # For GitHub API
    ],
    entry_points={
        "console_scripts": [
            "aw-watcher-procrastination=aw_watcher_procrastination.main:main",
        ],
    },
    author="Greg Schwartz",
    description="ActivityWatch Procrastination Monitor",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/gregschwartz/aw-procrastination-monitor",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
) 