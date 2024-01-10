import logging
import os
from pathlib import Path
from typing import Any

from cvfe.data import functional
from cvfe.data.constant import DocTypes
from cvfe.data.preprocessor import (
    CanadaDataDictPreprocessor,
    CopyFile,
    FileTransformCompose,
    MakeContentCopyProtectedMachineReadable,
)

# config logger
logger = logging.getLogger(__name__)


def process(src_dir: Path | str) -> dict[str, dict[str, Any]]:
    """Converts a directory of 5257E and 5645E Canada visa forms to python dict

    Note:
        The structure of the src_dir must be::

        some/path/
            └── src_dir
                ├── *5257*.pdf
                └── *5645*.pdf

    Note:
        For more information about the details of implementation, please see
        other modules such as:

            - :mod:`cvfe.api`: for API requests if using one
            - :mod:`cvfe.configs`: Contains external data
            - :mod:`cvfe.data`: contains all reading/preprocessing and so on

    Note:
        If you are using the API endpoints, you can find this function on
        ``/cvfe/v1/convert/adobe_xfa``

    Args:
        src_dir (Path): The path to the directory containing a set of 5257E and
            5645E forms. This forms must be the official forms (Adobe protected).
            Also, the files must contain ``5257`` or ``5645`` in their name to be
            recognized.

    Returns:
        dict[str, Any]:
            A dictionary where keys are the fields on the form and
            values are the values non-transformed from the fields of the forms.
    """
    # convert str to Path
    if isinstance(src_dir, str):
        src_dir = Path(src_dir)

    # path to the output decrypted pdf
    dst_dir: Path = src_dir.parent / Path("decrypted/")
    # main code
    logger.info("↓↓↓ Starting data extraction ↓↓↓")
    # Canada protected PDF to make machine readable and skip other files
    compose = {
        CopyFile(mode="cf"): ".csv",
        CopyFile(mode="cf"): ".txt",
        MakeContentCopyProtectedMachineReadable(): ".pdf",
    }
    file_transform_compose = FileTransformCompose(transforms=compose)
    functional.process_directory(
        src_dir=src_dir.as_posix(),
        dst_dir=dst_dir.as_posix(),
        compose=file_transform_compose,
        file_pattern="*",
    )
    logger.info("↑↑↑ Finished data extraction ↑↑↑")

    logger.info("↓↓↓ Starting data loading ↓↓↓")
    # convert PDFs to dictionaries
    src_dir = dst_dir.as_posix()
    form_data_dict: dict[str, dict[str, Any]] = {}
    for dirpath, dirnames, all_filenames in os.walk(src_dir):
        # filter all_filenames
        filenames = all_filenames
        if filenames:
            files = [os.path.join(dirpath, fname) for fname in filenames]
            # applicant form
            logger.info("↓↓↓ Starting to process 5257E ↓↓↓")
            in_fname = [f for f in files if "5257" in f][0]
            data_dict_preprocessor = CanadaDataDictPreprocessor()
            if len(in_fname) != 0:
                data_dict_applicant = (
                    data_dict_preprocessor.file_specific_basic_transform(
                        path=in_fname, doc_type=DocTypes.CANADA_5257E
                    )
                )
            logger.info("↑↑↑ Finished processing 5257E ↑↑↑")
            # applicant family info
            logger.info("↓↓↓ Starting to process 5645E ↓↓↓")
            in_fname = [f for f in files if "5645" in f][0]
            if len(in_fname) != 0:
                data_dict_family = data_dict_preprocessor.file_specific_basic_transform(
                    path=in_fname, doc_type=DocTypes.CANADA_5645E
                )
            logger.info("↑↑↑ Finished processing 5645E ↑↑↑")

            # final dictionary: concatenate 5257 and 5645 dicts
            form_data_dict[DocTypes.CANADA_5257E.name] = data_dict_applicant
            form_data_dict[DocTypes.CANADA_5645E.name] = data_dict_family
        # logging
        logger.info(f"Processed the data point")
    logger.info("↑↑↑ Finished data loading ↑↑↑")
    return form_data_dict
