import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

import fastapi
import requests
from fastapi.encoders import jsonable_encoder

from cvfe.api.convert import BASE_SOURCE_DIR
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


# FastAPI router to be used by the FastAPI app
router = fastapi.APIRouter(prefix="/cvfe/v1/convert/adobe_xfa", tags=["adobe_xfa"])


def process(src_dir: Path):
    # path to the output decrypted pdf
    dst_dir: Path = src_dir.parts[0] / Path("decrypted/")
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
    data_dict = {}
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
            data_dict.update(data_dict_applicant)
            data_dict.update(data_dict_family)
        # logging
        logger.info(f"Processed the data point")
    logger.info("↑↑↑ Finished data loading ↑↑↑")
    return data_dict


@router.post("/", status_code=fastapi.status.HTTP_200_OK, tags=["adobe_xfa"])
async def convert(
    form_5257: fastapi.UploadFile,
    form_5645: fastapi.UploadFile,
    post_url: Optional[str] = None,
):
    try:
        # save files to disk
        input_path: Path = BASE_SOURCE_DIR / Path("x/")
        # create the path if does not exist
        input_path.mkdir(parents=True, exist_ok=True)
        with open(input_path / Path("5257.pdf"), "wb") as f:
            contents_form_5257 = await form_5257.read()
            f.write(contents_form_5257)
        with open(input_path / Path("5645.pdf"), "wb") as f:
            contents_form_5645 = await form_5645.read()
            f.write(contents_form_5645)
    except Exception as error:
        logger.exception(error)
        e = sys.exc_info()[1]
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e)
        )
    try:
        data_dict: dict[str, Any] = process(src_dir=BASE_SOURCE_DIR)

        logger.info("Process finished")
        response = [data_dict]

    except Exception as error:
        logger.exception(error)
        e = sys.exc_info()[1]
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    try:
        response_status_code: int = -1
        # if third-party url is provided, send post request to that
        if post_url:
            # make response jsonable
            jsonable_response = jsonable_encoder(response)
            # send the response to create the item in DB
            post_response = requests.post(url=post_url, json=jsonable_response)
            response_status_code = post_response.status_code
            logger.info(f"post response code {post_response.status_code}")

            # raise exception if bad status code
            if not post_response.ok:
                raise fastapi.HTTPException(
                    status_code=post_response.status_code, detail=post_response.text
                )
        return response

    except Exception as error:
        logger.exception(error)
        e = sys.exc_info()[1]
        raise fastapi.HTTPException(
            status_code=response_status_code,
            detail=str(e) if type(e) == str else str(e.detail),
        )
