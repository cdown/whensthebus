#!/usr/bin/env python

from setuptools import setup

with open("README.md") as readme_f:
    README = readme_f.read()

with open("requirements.txt") as requirements_f:
    REQUIREMENTS = requirements_f.readlines()


setup(
    name="whensthebus",
    version="1.0.0",
    description="Get live UK bus times on stdout",
    long_description=README,
    url="https://github.com/cdown/whensthebus",
    license="Public Domain",
    author="Chris Down",
    author_email="chris@chrisdown.name",
    py_modules=["whensthebus"],
    entry_points={"console_scripts": ["wtb=whensthebus:main"]},
    keywords="transport uk bus",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: Public Domain",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    install_requires=REQUIREMENTS,
)
