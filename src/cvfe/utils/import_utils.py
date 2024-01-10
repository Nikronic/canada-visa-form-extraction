import importlib


def safe_import(import_path: str, classname: str, dep_group: str):
    """Method that allows the import of nodes that depend on missing dependencies.

    These nodes can be installed one by one with project.optional-dependencies
    (see ``pyproject.toml``) but they need to be all imported in their respective
    package's ``__init__`` module.

    Therefore, in case of an :class:`ImportError`, the class to import is replaced by
    a hollow ``MissingDependency`` function, which will throw an error when initialized.
    """

    try:
        module = importlib.import_module(import_path)
        retrieved_class = vars(module).get(classname)
        if retrieved_class is None:
            raise ImportError(f"Failed to import '{classname}' from '{import_path}'")
    except ImportError as ie:
        retrieved_class = _missing_dependency_stub_factory(classname, dep_group, ie)
    return retrieved_class


def _missing_dependency_stub_factory(
    classname: str, dep_group: str, import_error: Exception
):
    """Create custom versions of ``MissingDependency`` using the given parameters

    See :func:`cvfe.utils.import_utils.safe_import`
    """

    class MissingDependency:
        def __init__(self, *args, **kwargs):
            optional_component_not_installed(classname, dep_group, import_error)

        def __getattr__(self, *a, **k):
            return None

    return MissingDependency


def optional_component_not_installed(
    component: str, dep_group: str, source_error: Exception
):
    """Throws an :class:`ImportError` dependency group

    Args:
        component (str): The class name
        dep_group (str): The group that the ``component`` belongs too
        source_error (Exception): The original exception raised when importing

    Raises:
        ImportError: With a description of ways of installing.
    """
    raise ImportError(
        f"Failed to import '{component}', "
        "which is an optional component in CVFE.\n"
        f"Run 'pip install 'cvfe[{dep_group}]'' "
        "to install the required dependencies and make this component available.\n"
        f"(Original error: {str(source_error)})"
    ) from source_error
