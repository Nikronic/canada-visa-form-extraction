__all__ = [
    "dict_summarizer",
    "dict_to_csv",
    "column_dropper",
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
from fnmatch import fnmatch
from typing import Any, Callable, Iterable, Optional, cast

import numpy as np
import pandas as pd
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
    d: dict,
    cutoff_term: str,
    KEY_ABBREVIATION_DICT: dict = None,
    VALUE_ABBREVIATION_DICT: dict = None,
) -> dict:
    """Takes a flattened dictionary and shortens its keys

    Args:
        d (dict): The dictionary to be shortened
        cutoff_term (str): The string that used to find in keys and remove anything behind it
        KEY_ABBREVIATION_DICT (dict, optional): A dictionary containing abbreviation
            mapping for keys. Defaults to None.
        VALUE_ABBREVIATION_DICT (dict, optional): A dictionary containing abbreviation
            mapping for values. Defaults to None.

    Returns:
        dict:
            A dict with shortened keys by throwing away some part and using a
            abbreviation dictionary for both keys and values.
    """

    new_keys = {}
    new_values = {}
    for k, v in d.items():
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
        new_keys = dict((key, key) for (key, _) in d.items())
    if VALUE_ABBREVIATION_DICT is None:
        new_values = dict((value, value) for (_, value) in d.items())
    return dict((new_keys[key], new_values[value]) for (key, value) in d.items())


def dict_to_csv(d: dict, path: str) -> None:
    """Takes a flattened dictionary and writes it to a CSV file.

    Args:
        d (dict): A dictionary
        path (str): Path to the output file (will be created if not exist)
    """

    with open(path, "w") as f:
        w = csv.DictWriter(f, d.keys())
        w.writeheader()
        w.writerow(d)


def column_dropper(
    dataframe: pd.DataFrame,
    string: str,
    exclude: Optional[str] = None,
    regex: bool = False,
    inplace: bool = True,
) -> Optional[pd.DataFrame]:
    """Takes a Pandas Dataframe and drops columns matching a pattern

    Args:
        dataframe (:class:`pandas.DataFrame`): Pandas dataframe to be processed
        string (str): string to look for in ``dataframe`` columns
        exclude (Optional[str], optional): string to exclude a subset of columns from
            being dropped. Defaults to None.
        regex (bool, optional): compile ``string`` as regex. Defaults to False.
        inplace (bool, optional): whether or not use and inplace
            operation. Defaults to True.

    Returns:
        Optional[:class:`pandas.DataFrame`]:
            Takes a Pandas Dataframe and searches for
            columns *containing* ``string`` in them either raw string or
            regex (in latter case, use ``regex=True``) and after ``exclude`` ing a
            subset of them, drops the remaining *in-place*.
    """

    if regex:
        r = re.compile(string)
        col_to_drop = list(filter(r.match, dataframe.columns.values))
    else:
        col_to_drop = [col for col in dataframe.columns.values if string in col]

    if exclude is not None:
        col_to_drop = [col for col in col_to_drop if exclude not in col]

    if inplace:
        dataframe.drop(col_to_drop, axis=1, inplace=inplace)
    else:
        dataframe = dataframe.drop(col_to_drop, axis=1, inplace=inplace)

    return None if inplace else dataframe


def fillna_datetime(
    dataframe: pd.DataFrame,
    col_base_name: str,
    date: str,
    type: DocTypes,
    one_sided: str | bool = False,
    inplace: bool = False,
) -> Optional[pd.DataFrame]:
    """Takes names of two columns of dates (start, end) and fills them with a predefined value

    Args:
        dataframe (:class:`pandas.DataFrame`): Pandas Dataframe to be processed
        col_base_name (str): Base column name that accepts ``'From'`` and ``'To'`` for
            extracting dates of same category
        date (str): The desired date
        type (DocTypes): Different ways of filling empty date columns:

            1. ``'right'``: Uses the ``current_date`` as the final time
            2. ``'left'``: Uses the ``reference_date`` as the starting time

        one_sided (str | bool, optional): whether or not use an inplace
            operation. Defaults to False.
        inplace (bool, optional): :class:`DocTypes <cvfe.data.constant.DocTypes>`
            used to use rules for matching tags and filling appropriately.
            Defaults to False.

    Note:
        In transformation operations such as :func:`aggregate_datetime` function,
        this would be converted to period of zero. It is useful for filling periods of
        non existing items (e.g. age of children for single person).

    Returns:
        :class:`pandas.DataFrame`:
            A Pandas Dataframe that two columns of dates that had no value (None)
            which was filled to the same date via ``date``.
    """

    if not one_sided:
        r = re.compile(tag_to_regex_compatible(string=col_base_name, type=type))
    else:
        r = re.compile(
            tag_to_regex_compatible(string=col_base_name, type=type) + "\.(From|To).+"
        )
    columns_to_fillna_names = list(filter(r.match, dataframe.columns.values))
    for col in dataframe[columns_to_fillna_names]:
        if inplace:
            dataframe[col].fillna(date, inplace=inplace)
        else:
            dataframe[col] = dataframe[col].fillna(date, inplace=inplace)
    return None if inplace else dataframe


def aggregate_datetime(
    dataframe: pd.DataFrame,
    col_base_name: str,
    new_col_name: str,
    type: DocTypes,
    if_nan: Optional[str | Callable] = "skip",
    one_sided: Optional[str] = None,
    reference_date: Optional[str] = None,
    current_date: Optional[str] = None,
    **kwargs,
) -> pd.DataFrame:
    """Takes two columns of dates in string form and calculates the period of them

    Args:
        dataframe (:class:`pandas.DataFrame`): Pandas dataframe to be processed
        col_base_name (str): Base column name that accepts ``'From'`` and ``'To'`` for
            extracting dates of same category
        new_col_name (str): The column name that extends ``col_base_name`` and will be
            the final column containing the period.
        type (DocTypes): document type used to use rules for matching tags and
            filling appropriately. See :class:`DocTypes <cvfe.data.constant.DocTypes>`.
        if_nan (Optional[str | Callable], optional): What to do with None s (NaN).
            Could be a function or predefined states as follow:

            1. ``'skip'``: do nothing (i.e. ignore ``None``s). Defaults to ``'skip'``.

        one_sided (Optional[str], optional): Different ways of filling empty date columns.
            Defaults to None. Could be one of the following:

            1. ``'right'``: Uses the ``current_date`` as the final time
            2. ``'left'``: Uses the ``reference_date`` as the starting time

        reference_date (Optional[str], optional): Assumed ``reference_date`` (t0<t1). Defaults to None.
        current_date (Optional[str], optional): Assumed ``current_date`` (t1>t0). Defaults to None.
        default_datetime: accepts datetime.datetime_ to set default date
            for dateutil.parser.parse_.

    Returns:
        :class:`pandas.DataFrame`:
            A Pandas Dataframe calculate the period of two columns of dates
            and represent it in integer form. The two columns used will be dropped.

    .. _datetime.datetime: https://docs.python.org/3/library/datetime.html
    .. _dateutil.parser.parse: https://dateutil.readthedocs.io/en/stable/parser.html
    """

    default_datetime = datetime.datetime(
        year=DATEUTIL_DEFAULT_DATETIME["year"],
        month=DATEUTIL_DEFAULT_DATETIME["month"],
        day=DATEUTIL_DEFAULT_DATETIME["day"],
    )
    default_datetime = kwargs.get("default_datetime", default_datetime)

    aggregated_column_name = None
    if one_sided is None:
        aggregated_column_name = col_base_name + "." + new_col_name
        r = re.compile(
            tag_to_regex_compatible(string=col_base_name, type=type) + "\.(From|To).+"
        )
    else:  # when one_sided, we no longer have *From* or *To*
        aggregated_column_name = col_base_name + "." + new_col_name
        r = re.compile(tag_to_regex_compatible(string=col_base_name, type=type))
    columns_to_aggregate_names = list(filter(r.match, dataframe.columns.values))

    # *.FromDate and *.ToDate --> *.Period
    column_from_date = reference_date
    column_to_date = current_date
    if one_sided == "left":
        column_from_date = reference_date
        to_date = columns_to_aggregate_names[0]
    elif one_sided == "right":
        column_to_date = current_date
        from_date = columns_to_aggregate_names[0]
    else:
        from_date = [col for col in columns_to_aggregate_names if "From" in col][0]
        to_date = [col for col in columns_to_aggregate_names if "To" in col][0]

    if isinstance(column_to_date, str):
        column_to_date = parser.parse(
            column_to_date, default=default_datetime
        )  # type: ignore

    if column_from_date is None:  # ignore reference_date if from_date exists
        # to able to use already parsed data from fillna
        if not dataframe[from_date].dtypes == "<M8[ns]":
            dataframe[from_date] = dataframe[from_date].apply(
                lambda x: parser.parse(x, default=default_datetime)
                if x is not None
                else x
            )
        column_from_date = dataframe[from_date]
    else:
        if isinstance(column_from_date, str):
            column_from_date = parser.parse(
                column_from_date, default=default_datetime
            )  # type: ignore

    if column_to_date is None:  # ignore current_date if to_date exists
        # to able to use already parsed data from fillna
        if not dataframe[to_date].dtypes == "<M8[ns]":
            dataframe[to_date] = dataframe[to_date].apply(
                lambda x: parser.parse(x, default=default_datetime)
                if x is not None
                else x
            )
        column_to_date = dataframe[to_date]
    else:
        if isinstance(column_to_date, str):
            column_to_date = parser.parse(
                column_to_date, default=default_datetime
            )  # type: ignore

    if if_nan is not None:
        if if_nan == "skip":
            if column_from_date.isna().all() or column_to_date.isna().all():  # type: ignore
                return dataframe

    dataframe[aggregated_column_name] = np.nan  # combination of dates
    dataframe[aggregated_column_name].fillna(  # period
        column_to_date - column_from_date, inplace=True
    )  # type: ignore
    dataframe[aggregated_column_name] = dataframe[
        aggregated_column_name
    ].dt.days.astype(
        "int32"
    )  # change to int of days

    dataframe.drop(
        columns_to_aggregate_names, axis=1, inplace=True
    )  # drop from/to columns
    return dataframe


def tag_to_regex_compatible(string: str, type: DocTypes) -> str:
    """Takes a string and makes it regex compatible for XML parsed string

    Note:
        This is specialized method and it may be better to override it for
        your own case.

    Args:
        string (str): input string to get manipulated
        type (DocTypes): specified :class:`DocTypes <cvfe.data.constant.DocTypes>`
            to determine regex rules

    Returns:
        str: A modified string
    """

    if (
        type == DocTypes.CANADA_5257E
        or type == DocTypes.CANADA_5645E
        or type == DocTypes.CANADA
    ):
        string = string.replace(".", "\.").replace("[", "\[").replace("]", "\]")

    return string


def change_dtype(
    dataframe: pd.DataFrame,
    col_name: str,
    dtype: Callable,
    if_nan: str | Callable = "skip",
    **kwargs,
) -> pd.DataFrame:
    """Changes the data type of a column with ability to fill ``None`` s

    Args:
        dataframe (:class:`pandas.DataFrame`): Dataframe that ``column_name`` will be searched on
        col_name (str): Desired column name of the dataframe
        dtype (Callable): target data type as a function e.g. ``np.float32``
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
        :class:`pandas.DataFrame`:
            A Pandas Dataframe calculate the period of two columns of dates
            and represent it in integer form. The two columns used will be dropped.
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
            return dtype(x, default=default_datetime)
        return dtype(x)

    # apply the rules and data type change
    dataframe[col_name] = dataframe[col_name].apply(
        lambda x: apply_dtype(standardize(x)) if x is not None else func(x)
    )

    return dataframe





def flatten_dict(d: dict) -> dict:
    """Takes a (nested) multilevel dictionary and flattens it

    Args:
        d (dict): A dictionary (could be multilevel)

    References:
        1. https://stackoverflow.com/a/67744709/18971263

    Returns:
        dict: Flattened dictionary where keys and values of returned dict are:

            * ``new_keys[i] = f'{old_leys[level]}.{old_leys[level+1]}.[...].{old_leys[level+n]}'``
            * ``new_value = old_value``

    """

    def items():
        if isinstance(d, dict):
            for key, value in d.items():
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


