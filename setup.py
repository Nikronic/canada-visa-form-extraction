from setuptools import find_packages
from setuptools import setup
from pathlib import Path
from typing import Dict


this_directory = Path(__file__).parent
long_description = (this_directory / 'README.md').read_text()

with open('requirements.txt') as f:
    required = f.read().splitlines()

# version.py defines the VERSION and VERSION_SHORT variables
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
    url='https://github.com/Nikronic/canada-visa-form-extraction',
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: YOUR_LICENSE_HERE",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11.0',
    install_requires=required,
    include_package_data = True,
    package_data={
        'cvfe.configs': ['**/*.csv'],
      },
      keywords=['visa', 'extraction', 'canada', 'form'],
)
