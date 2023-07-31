__all__ = [
    'VERSION_SHORT', 'VERSION'
]

_MAJOR = '0'
_MINOR = '1'
_REVISION = '1'

VERSION_SHORT = f'{_MAJOR}.{_MINOR}'
"""Version of the package as ``major.minor``

Suggested usage for stable production where breaking updates
is not so common.
"""
VERSION = f'{_MAJOR}.{_MINOR}.{_REVISION}'
"""Version of the package as ``major.minor.revision``

Suggested usage for dev, alpha and beta where breaking updates
are frequent.
"""
