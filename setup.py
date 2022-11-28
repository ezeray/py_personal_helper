"""
Setuptools setup script.
"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="personal_helper",
    version="0.1.0",
    description="Ezequiel Raigorodsky's personal helper package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ezeray/py_personal_helper",
    author="Ezequiel Raigorodsky",
    author_email="ezequielraigorodsky@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Helper",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="development, helper, utils",
    # package_dir={"": "personal_helper"},
    # packages=find_packages(where="personal_helper"),
    python_requires=">=3.9, <4",
    # install_requires=[],
)
