import logging
import sys
from pathlib import Path
from typing import Any, Optional

from cvfe.api.convert import BASE_SOURCE_DIR
from cvfe.convert.adobe_xfa import process

# config logger
logger = logging.getLogger(__name__)

# check if dependencies are installed
try:
    import fastapi
    import requests
    from fastapi.encoders import jsonable_encoder

except ImportError as ie:
    from cvfe.utils.import_utils import optional_component_not_installed

    optional_component_not_installed(__name__, "api", ie)


# FastAPI router to be used by the FastAPI app
router = fastapi.APIRouter(prefix="/cvfe/v1/convert/adobe_xfa", tags=["adobe_xfa"])


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
            status_code=fastapi.status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e),
        )
    try:
        data_dict: dict[str, Any] = process(src_dir=BASE_SOURCE_DIR)

        logger.info("Process finished")
        response = data_dict

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
