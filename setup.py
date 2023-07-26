from setuptools import find_packages
from setuptools import setup
from pathlib import Path
from typing import Dict


this_directory = Path(__file__).parent
long_description = (this_directory / 'README.md').read_text()

# version.py defines the VERSION and VERSION_SHORT variables.
# We use exec here so we don't import snorkel.
VERSION: Dict[str, str] = {}
with open('cvfe/version.py', 'r') as version_file:
    exec(version_file.read(), VERSION)

setup(
    name='cvfe',
    version=VERSION['VERSION'],
    packages=find_packages(),
    description='cvfe: Canada Visa Form Extraction!',
    author='Nikan Doosti',
    author_email='nikan.doosti@outlook.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data = True,
    package_data={
        # ref https://stackoverflow.com/a/73649552/18971263
        'cvfe.configs': ['**/*.csv'],
      }
)
