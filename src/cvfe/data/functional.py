__all__ = [
    "dict_summarizer",
    "dict_to_csv",
    "key_dropper",
    "fillna_datetime",
    "aggregate_datetime",
    "tag_to_regex_compatible",
    "change_dtype",
    "flatten_dict",
    "xml_to_flattened_dict",
    "process_directory",
]

"""
Contains implementation of functions that could be used for processing data everywhere and
    are not necessarily bounded to a class.

"""

import csv
import datetime
import logging
import os
import re
from copy import deepcopy
from fnmatch import fnmatch
from typing import Any, Callable, Iterable, Optional, cast

import xmltodict
from dateutil import parser

from cvfe.data.constant import *
from cvfe.data.preprocessor import FileTransformCompose

# set logger
logger = logging.getLogger(__name__)


def drop(dictionary: dict[str, Any], keys: Iterable[str]) -> None:
    """Takes a dictionary and removes ``keys`` from it

    Args:
        dictionary (dict[str, Any]): The dictionary to be processed
        keys (Iterable[str]): An iterable of string as subset of keys.
            If an item in ``keys`` is none existent in the dictionary,
            it will just skip it.
    """

    for k in keys:
        dictionary.pop(k, None)


def fillna(original: Any, new: Any) -> Any:
    """Replaces an ``original`` value with a ``new`` if None

    Args:
        original (Any): Original value to be replaced if None
        new (Any): The new value as replacement of ``original``

    Returns:
        Any: The new value
    """

    return new if original is None else original


def dict_summarizer(
    data_dict: dict[str, Any],
    cutoff_term: str,
    KEY_ABBREVIATION_DICT: dict = None,
    VALUE_ABBREVIATION_DICT: dict = None,
) -> dict[str, Any]:
    """Takes a flattened dictionary and shortens its keys

    Args:
        data_dict (dict[str, Any]): The dictionary to be shortened
        cutoff_term (str): The string that used to find in keys and remove anything behind it
        KEY_ABBREVIATION_DICT (dict, optional): A dictionary containing abbreviation
            mapping for keys. Defaults to None.
        VALUE_ABBREVIATION_DICT (dict, optional): A dictionary containing abbreviation
            mapping for values. Defaults to None.

    Returns:
        dict[str, Any]:
            A dict with shortened keys by throwing away some part and using a
            abbreviation dictionary for both keys and values.
    """

    new_keys = {}
    new_values = {}
    for k, v in data_dict.items():
        if KEY_ABBREVIATION_DICT is not None:
            new_k = k
            if cutoff_term in k:  # FIXME: cutoff part should be outside of abbreviation
                new_k = k[k.index(cutoff_term) + len(cutoff_term) + 1 :]

            # add any filtering over keys here
            # abbreviation
            for word, abbr in KEY_ABBREVIATION_DICT.items():
                new_k = re.sub(word, abbr, new_k)
            new_keys[k] = new_k

        if VALUE_ABBREVIATION_DICT is not None:
            # values can be None
            if v is not None:
                new_v = v
                if (
                    cutoff_term in v
                ):  # FIXME: cutoff part should be outside of abbreviation
                    new_v = v[v.index(cutoff_term) + len(cutoff_term) + 1 :]

                # add any filtering over values here
                # abbreviation
                for word, abbr in VALUE_ABBREVIATION_DICT.items():
                    new_v = re.sub(word, abbr, new_v)
                new_values[v] = new_v
            else:
                new_values[v] = v

    # return a new dictionary with updated values
    if KEY_ABBREVIATION_DICT is None:
        new_keys = dict((key, key) for (key, _) in data_dict.items())
    if VALUE_ABBREVIATION_DICT is None:
        new_values = dict((value, value) for (_, value) in data_dict.items())
    return dict(
        (new_keys[key], new_values[value]) for (key, value) in data_dict.items()
    )


def dict_to_csv(data_dict: dict[str, Any], path: str) -> None:
    """Takes a flattened dictionary and writes it to a CSV file.

    Args:
        data_dict (dict[str, Any]): A dictionary to be saved
        path (str): Path to the output file (will be created if not exist)
    """

    with open(path, "w") as f:
        w = csv.DictWriter(f, data_dict.keys())
        w.writeheader()
        w.writerow(data_dict)


def key_dropper(
    data_dict: dict[str, Any],
    string: str,
    exclude: Optional[str] = None,
    regex: bool = False,
    inplace: bool = True,
) -> Optional[dict[str, Any]]:
    """Takes a dictionary and drops keys matching a pattern

    Args:
        data_dict (dict[str, Any]): Dictionary to be processed
        string (str): string to look for in ``data_dict`` keys
        exclude (Optional[str], optional): string to exclude a subset of keys from
            being dropped. Defaults to None.
        regex (bool, optional): compile ``string`` as regex. Defaults to False.
        inplace (bool, optional): whether or not use and inplace
            operation. Defaults to True.

    Returns:
        Optional[dict[str, Any]]:
            Takes a dictionary and searches for keys *containing* ``string``
            in them either raw string or regex (in latter case, use ``regex=True``)
            and after ``exclude`` ing a subset of them, drops the remaining *in-place*.
    """

    if regex:
        r = re.compile(string)
        key_to_drop = list(filter(r.match, list(data_dict.keys())))
    else:
        key_to_drop = [key for key in list(data_dict.keys()) if string in key]

    if exclude is not None:
        key_to_drop = [key for key in key_to_drop if exclude not in key]

    if inplace:
        drop(dictionary=data_dict, keys=key_to_drop)
    else:
        data_dict_copy = deepcopy(data_dict)
        drop(dictionary=data_dict_copy, keys=key_to_drop)

    return None if inplace else data_dict_copy


def fillna_datetime(
    data_dict: dict[str, Any],
    key_base_name: str,
    date: str,
    doc_type: DocTypes,
    one_sided: str | bool = False,
    inplace: bool = False,
) -> Optional[dict[str, Any]]:
    """Takes names of two keys with dates value (start, end) and fills them with a predefined value

    Args:
        data_dict (dict[str, Any]): A dictionary to be processed
        key_base_name (str): Base key name that accepts ``'From'`` and ``'To'`` for
            extracting dates of same category
        date (str): The desired date
        doc_type (DocTypes): :class:`DocTypes <cvfe.data.constant.DocTypes>`
            used to use rules for matching tags and filling appropriately.
            Defaults to False.

        one_sided (str | bool, optional): Different ways of filling empty date keys:

            1. ``'right'``: Uses the ``current_date`` as the final time
            2. ``'left'``: Uses the ``reference_date`` as the starting time

        inplace (bool, optional): whether or not use an inplace
            operation. Defaults to False.

    Note:
        In transformation operations such as :func:`aggregate_datetime` function,
        this would be converted to period of zero. It is useful for filling periods of
        non existing items (e.g. age of children for single person).

    Returns:
        dict[str, Any]:
            A dictionary that two keys with dates types that had no value (None)
            which was filled to the exact same date via ``date``.
    """

    if not one_sided:
        r = re.compile(tag_to_regex_compatible(string=key_base_name, doc_type=doc_type))
    else:
        r = re.compile(
            tag_to_regex_compatible(string=key_base_name, doc_type=doc_type)
            + "\.(From|To).+"
        )
    keys_to_fillna_names = list(filter(r.match, list(data_dict.keys())))
    for key in data_dict[keys_to_fillna_names]:
        if inplace:
            data_dict[key] = fillna(original=data_dict[key], new=date)
        else:
            data_dict_copy = deepcopy(data_dict_copy)
            data_dict_copy[key] = fillna(original=data_dict_copy[key], new=date)
    return None if inplace else data_dict


def aggregate_datetime(
    data_dict: dict[str, Any],
    key_base_name: str,
    new_key_name: str,
    doc_type: DocTypes,
    if_nan: str | Callable = "skip",
    one_sided: Optional[str] = None,
    reference_date: Optional[str] = None,
    current_date: Optional[str] = None,
    **kwargs,
) -> dict[str, Any]:
    """Takes two keys of dates in string form and calculates the period of them

    Args:
        data_dict (dict[str, Any]): A dictionary to be processed
        key_base_name (str): Base key name that accepts ``'From'`` and ``'To'`` for
            extracting dates of same category
        new_key_name (str): The key name that extends ``key_base_name`` and will be
            the final key containing the period.
        doc_type (DocTypes): document type used to use rules for matching tags and
            filling appropriately. See :class:`DocTypes <cvfe.data.constant.DocTypes>`.
        if_nan (str | Callable, optional): What to do with None s (NaN).
            Could be a function or predefined states as follow:

            1. ``'skip'``: do nothing (i.e. ignore ``None``s). Defaults to ``'skip'``.

        one_sided (Optional[str], optional): Different ways of filling empty date keys.
            Defaults to None. Could be one of the following:

            1. ``'right'``: Uses the ``current_date`` as the final time
            2. ``'left'``: Uses the ``reference_date`` as the starting time

        reference_date (Optional[str], optional): Assumed ``reference_date`` (t0<t1). Defaults to None.
        current_date (Optional[str], optional): Assumed ``current_date`` (t1>t0). Defaults to None.
        default_datetime: accepts datetime.datetime_ to set default date
            for dateutil.parser.parse_.

    Returns:
        dict[str, Any]:
            A new dictionary that contains a key with result of calculation of the period
            of two keys with values of dates and represent it in integer form.
            The two keys used for this are dropped.

    .. _datetime.datetime: https://docs.python.org/3/library/datetime.html
    .. _dateutil.parser.parse: https://dateutil.readthedocs.io/en/stable/parser.html
    """

    default_datetime = datetime.datetime(
        year=DATEUTIL_DEFAULT_DATETIME["year"],
        month=DATEUTIL_DEFAULT_DATETIME["month"],
        day=DATEUTIL_DEFAULT_DATETIME["day"],
    )
    default_datetime = kwargs.get("default_datetime", default_datetime)

    aggregated_key_name = None
    if one_sided is None:
        aggregated_key_name = key_base_name + "." + new_key_name
        r = re.compile(
            tag_to_regex_compatible(string=key_base_name, doc_type=doc_type)
            + "\.(From|To).+"
        )
    else:  # when one_sided, we no longer have *From* or *To*
        aggregated_key_name = key_base_name + "." + new_key_name
        r = re.compile(tag_to_regex_compatible(string=key_base_name, doc_type=doc_type))
    keys_to_aggregate_names = list(filter(r.match, list(data_dict.keys())))

    # *.FromDate and *.ToDate --> *.Period
    key_from_date = reference_date
    key_to_date = current_date
    if one_sided == "left":
        key_from_date = reference_date
        to_date = keys_to_aggregate_names[0]
    elif one_sided == "right":
        key_to_date = current_date
        from_date = keys_to_aggregate_names[0]
    else:
        from_date = [col for col in keys_to_aggregate_names if "From" in col][0]
        to_date = [col for col in keys_to_aggregate_names if "To" in col][0]

    if isinstance(key_to_date, str):
        key_to_date = parser.parse(key_to_date, default=default_datetime)

    if key_from_date is None:
        # ignore reference_date if from_date exists
        #   to able to use already parsed data from fillna
        if not isinstance(data_dict[from_date], datetime.datetime):
            data_dict[from_date] = (
                parser.parse(data_dict[from_date], default=default_datetime)
                if data_dict[from_date] is not None
                else data_dict[from_date]
            )
        key_from_date = data_dict[from_date]
    else:
        if isinstance(key_from_date, str):
            key_from_date = parser.parse(key_from_date, default=default_datetime)

    if key_to_date is None:
        # ignore current_date if to_date exists
        #   to able to use already parsed data from fillna
        if not isinstance(data_dict[to_date], datetime.datetime):
            data_dict[to_date] = (
                parser.parse(data_dict[to_date], default=default_datetime)
                if data_dict[to_date] is not None
                else data_dict[to_date]
            )

        key_to_date = data_dict[to_date]
    else:
        if isinstance(key_to_date, str):
            key_to_date = parser.parse(key_to_date, default=default_datetime)

    if if_nan is not None:
        if if_nan == "skip":
            if key_from_date is None or key_to_date is None:
                return data_dict

    data_dict[aggregated_key_name] = None  # combination of dates
    data_dict[aggregated_key_name] = fillna(
        original=data_dict[aggregated_key_name], new=(key_to_date - key_from_date).days
    )

    assert isinstance(data_dict[aggregated_key_name], int)  # days must be int

    # drop start and end date keys
    drop(dictionary=data_dict, keys=keys_to_aggregate_names)
    return data_dict


def tag_to_regex_compatible(string: str, doc_type: DocTypes) -> str:
    """Takes a string and makes it regex compatible for XML parsed string

    Note:
        This is specialized method and it may be better to override it for
        your own case.

    Args:
        string (str): input string to get manipulated
        doc_type (DocTypes): specified :class:`DocTypes <cvfe.data.constant.DocTypes>`
            to determine regex rules

    Returns:
        str: A modified string
    """

    if (
        doc_type == DocTypes.CANADA_5257E
        or doc_type == DocTypes.CANADA_5645E
        or doc_type == DocTypes.CANADA
    ):
        string = string.replace(".", "\.").replace("[", "\[").replace("]", "\]")

    return string


def change_dtype(
    data_dict: dict[str, Any],
    key_name: str,
    dtype: Callable,
    if_nan: str | Callable = "skip",
    **kwargs,
) -> dict[str, Any]:
    """Changes the data type of a key with ability to fill ``None`` s (fillna)

    Args:
        data_dict (dict[str, Any]): A dictionary that ``key_name`` will be searched on
        key_name (str): Desired key name of the dictionary
        dtype (Callable): target data type as a function e.g. ``float``
        if_nan (str, Callable, optional): What to do with None s (NaN).
            Defaults to ``'skip'``. Could be a function or predefined states as follow:

            1. ``'skip'``: do nothing (i.e. ignore ``None`` s)
            2. ``'value'``: fill the None with ``value`` argument via ``kwargs``

        default_datetime(optional): accepts datetime.datetime_ to set default date
            for dateutil.parser.parse_

    Raises:
        ValueError: if string mode passed to ``if_nan`` does not exist. It won't
            raise if ``if_nan`` is ``Callable``.

    Returns:
        dict[str, Any]:
            A dictionary that contains the calculation of the period of two keys with
            values of type dates and represent it in number of days. The two keys used
            for the calculation of period are dropped.
    """

    default_datetime = datetime.datetime(
        year=DATEUTIL_DEFAULT_DATETIME["year"],
        month=DATEUTIL_DEFAULT_DATETIME["month"],
        day=DATEUTIL_DEFAULT_DATETIME["day"],
    )
    default_datetime = kwargs.get("default_datetime", default_datetime)

    # define `func` for different cases of predefined logics
    if isinstance(if_nan, str):  # predefined `if_nan` cases
        if if_nan == "skip":
            # the function to be used in `.apply` method of dataframe
            def func(x):
                return x

        elif if_nan == "fill":
            value = kwargs["value"]

            # the function to be used in `.apply` method of dataframe
            def func(x):
                return value

        else:
            raise ValueError(f'Unknown mode "{if_nan}".')
    else:
        pass

    def standardize(value: Any) -> Any:
        """Takes a value and make it standard for the target function that is going to parse it

        Args:
            value (Any): the input value that need to be standardized

        Note:
            This is mostly hardcoded and cannot be written better (I think!). So, you can
            remove it entirely, and see what errors you get, and change this accordingly to
            errors and exceptions you get.

        Returns:
            Any: Standardized value
        """
        if dtype == parser.parse:  # datetime parser
            try:
                parser.parse(value)
            except ValueError:  # bad input format for `parser.parse`
                value = cast(str, value)
                # we want YYYY-MM-DD
                # MMDDYYYY format (Canada Common Forms)
                if len(value) == 8 and value.isnumeric():
                    value = f"{value[4:]}-{value[2:4]}-{value[0:2]}"
                # fix values
                if value[5:7] == "02" and value[8:10] == "30":
                    # using >28 for February
                    value = "28".join(value.rsplit("30", 1))
        return value

    def apply_dtype(x: Any) -> Any:
        """Handles the default ``datetime.datetime`` for ``dateutil.parser.parse`` during casting dtypes

        Note:
            This function is only used to handle for a specific case of
            casting it is hardcoded

        Args:
            x (Any): Any value that its dtype going to be casted

        Returns:
            Any: ``x`` that is casted to a new type
        """
        if dtype == parser.parse:
            return dtype(x, default=default_datetime).isoformat()
        return dtype(x)

    # apply the rules and data type change
    data_dict[key_name] = data_dict[key_name]
    data_dict[key_name] = (
        apply_dtype(standardize(data_dict[key_name]))
        if data_dict[key_name] is not None
        else func(data_dict[key_name])
    )

    return data_dict


def flatten_dict(dictionary: dict[str, Any]) -> dict[str, Any]:
    """Takes a (nested) multilevel dictionary and flattens it

    Args:
        dictionary (dict[str, Any]): A dictionary (could be multilevel)

    References:
        1. https://stackoverflow.com/a/67744709/18971263

    Returns:
        dict[str, Any]: Flattened dictionary where keys and values of returned dict are:

            * ``new_keys[i] = f'{old_leys[level]}.{old_leys[level+1]}.[...].{old_leys[level+n]}'``
            * ``new_value = old_value``

    """

    def items():
        if isinstance(dictionary, dict):
            for key, value in dictionary.items():
                # nested subtree
                if isinstance(value, dict):
                    for subkey, subvalue in flatten_dict(value).items():
                        yield f"{key}.{subkey}", subvalue
                # nested list
                elif isinstance(value, list):
                    for num, elem in enumerate(value):
                        for subkey, subvalue in flatten_dict(elem).items():
                            yield f"{key}.[{num}].{subkey}", subvalue
                # everything else (only leafs should remain)
                else:
                    yield key, value

    return dict(items())


def xml_to_flattened_dict(xml: str) -> dict:
    """Takes a (nested) XML and flattens it to a dict via :func:`flatten_dict`

    Args:
        xml (str): A XML string

    Returns:
        dict: A flattened dictionary of given XML
    """
    flattened_dict = xmltodict.parse(xml)  # XML to dict
    flattened_dict = flatten_dict(flattened_dict)
    return flattened_dict


def process_directory(
    src_dir: str,
    dst_dir: str,
    compose: FileTransformCompose,
    file_pattern: str = "*",
) -> None:
    """Transforms all files that match pattern in given dir and saves new files preserving dir structure

    Note:
        A methods used for handling files from manually processed dataset to raw-dataset
        see :class:`FileTransform <cvfe.data.preprocessor.FileTransform>` for more information.

    References:
        1. https://stackoverflow.com/a/24041933/18971263

    Args:
        src_dir (str): Source directory to be processed
        dst_dir (str): Destination directory to write processed files
        compose (FileTransformCompose): An instance of transform composer.
            see :class:`Compose <cvfe.data.preprocessor.FileTransformCompose>`.
        file_pattern (str, optional): pattern to match files, default to ``'*'`` for
            all files. Defaults to ``'*'``.
    """

    assert src_dir != dst_dir, "Source and destination dir must differ."
    if src_dir[-1] != "/":
        src_dir += "/"

    # process directories
    for dirpath, _, all_filenames in os.walk(src_dir):
        # filter out files that match pattern only
        filenames = filter(lambda fname: fnmatch(fname, file_pattern), all_filenames)
        dirname = dirpath[len(dirpath) - dirpath[::-1].find("/") :]
        logger.info(f'Processing directory="{dirname}"...')
        if filenames:
            dir_ = os.path.join(dst_dir, dirpath.replace(src_dir, ""))
            os.makedirs(dir_, exist_ok=True)
            for fname in filenames:
                in_fname = os.path.join(dirpath, fname)  # original path
                out_fname = os.path.join(dir_, fname)  # processed path
                compose(in_fname, out_fname)  # composition of transforms
                logger.info(f'Processed file="{fname}"')
        logger.info(f"Processed the data entry.")


def extended_dict_get(
    string: str, dic: dict, if_nan: str, condition: Optional[Callable | bool] = None
):
    """Takes a string and looks for it inside a dictionary with default value if condition is satisfied

    Args:
        string (str): the ``string`` to look for inside dictionary ``dic``
        dic (dict): the dictionary that ``string`` is expected to be
        if_nan (str): the value returned if ``string`` could not be found in ``dic``
        condition (Optional[Callable | bool], optional): look for ``string`` in ``dic`` only
            if ``condition`` is True. Defaults to None.

    Examples:
        >>> d = {'1': 'a', '2': 'b', '3': 'c'}
        >>> extended_dict_get('1', d, 'z', str.isnumeric)
        'a'
        >>> extended_dict_get('x', d, 'z', str.isnumeric)
        'x'

    Returns:
        Any: Substituted value instead of `string`
    """

    condition = (lambda x: True) if condition is None else condition
    condition = cast(Callable, condition)

    # check given `condition` is true or not
    if condition(string):
        return dic.get(string, if_nan)  # look for `string` if not use `if_nan`
    else:
        logger.info(
            (
                f'"{string}" is not True for the given `condition`',
                "==> `false_condition_value` will be applied.",
            )
        )
        return string
