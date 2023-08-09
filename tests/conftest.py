from pytest import Parser

def pytest_addoption(parser):
    """A hook to add custom command line options to pytest

    Args:
        parser (:class:`pytest.Parser`): 
    """
    parser.addoption('--bind', action='store', default='0.0.0.0')
    parser.addoption('--port', action='store', default='8000')
    