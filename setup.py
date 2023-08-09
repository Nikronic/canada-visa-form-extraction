from setuptools import setup

with open('VERSION', 'r') as file:
    version = file.read().strip()

test_deps = [
    'httpx>=0.24',
    'pytest>=7.3.0',
]
extras = {
    'test': test_deps,
}

setup(
    tests_require=test_deps,
    extras_require=extras,
    version=version
)
