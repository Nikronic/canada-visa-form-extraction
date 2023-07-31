from setuptools import setup

with open('VERSION', 'r') as file:
    version = file.read().strip()

setup(
    version=version,
)
