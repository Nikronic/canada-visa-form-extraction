# Core
import pandas as pd
# Ours: Data
from cvfe.data import functional
from cvfe.data.preprocessor import (
    MakeContentCopyProtectedMachineReadable,
    CanadaDataframePreprocessor,
    FileTransformCompose,
    CopyFile
)
from cvfe.data.constant import DocTypes
# Ours: API
from cvfe.api import models as api_models
from cvfe.api import apps as api_apps
from pydantic_settings import BaseSettings
# API
import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
# helpers
from typing import ClassVar
from pathlib import Path
import argparse
import logging
import sys
import os


# argparse
parser = argparse.ArgumentParser()
parser.add_argument(
    '-v',
    '--verbose',
    type=str,
    help='logging verbosity level.',
    choices=['debug', 'info'],
    default='info',
    required=False)
parser.add_argument(
    '-b',
    '--bind',
    type=str,
    help='ip address of host',
    default='0.0.0.0',
    required=True)
parser.add_argument(
    '-p',
    '--port',
    type=int,
    help='port used for creating the gunicorn server',
    default=8000,
    required=True)
parser.add_argument(
    '-w',
    '--workers',
    type=int,
    help='number of works used by gunicorn',
    default=1,
    required=False)
args = parser.parse_args()

# globals
VERBOSE = logging.DEBUG
# all files will be saved here (temporary)
BASE_SOURCE_DIR: Path = Path('temp/encrypted/')

# configure logging
logger = logging.getLogger(__name__)
logger.setLevel(VERBOSE)

class Settings(BaseSettings):
    BASE_URL: ClassVar[str] = f'http://{args.bind}:{args.port}'
    USE_NGROK: ClassVar[bool] = os.environ.get('USE_NGROK', 'False') == 'True'

# instantiate fast api app
app = fastapi.FastAPI()
settings = Settings()

# fastapi cross origin
origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

if settings.USE_NGROK:
    # pyngrok should only ever be installed or initialized in a dev environment when this flag is set
    from pyngrok import ngrok

    # Open a ngrok tunnel to the dev server
    public_url = ngrok.connect(args.port).public_url
    logger.info(f'ngrok tunnel \"{public_url}\" -> \"http://{args.bind}:{args.port}\"')

    # Update any base URLs or webhooks to use the public ngrok URL
    Settings.BASE_URL = public_url
    api_apps.init_webhooks(public_url)


def _process(src_dir: Path):
    # path to the output decrypted pdf
    dst_dir: Path = BASE_SOURCE_DIR.parts[0] / Path('decrypted/')
    # main code
    logger.info('↓↓↓ Starting data extraction ↓↓↓')
    # Canada protected PDF to make machine readable and skip other files
    compose = {
        CopyFile(mode='cf'): '.csv',
        CopyFile(mode='cf'): '.txt',
        MakeContentCopyProtectedMachineReadable(): '.pdf'
    }
    file_transform_compose = FileTransformCompose(transforms=compose)
    functional.process_directory(
        src_dir=src_dir.as_posix(),
        dst_dir=dst_dir.as_posix(),
        compose=file_transform_compose,
        file_pattern='*')
    logger.info('↑↑↑ Finished data extraction ↑↑↑')

    logger.info('↓↓↓ Starting data loading ↓↓↓')
    # convert PDFs to pandas dataframes
    src_dir = dst_dir.as_posix()
    dataframe = pd.DataFrame()
    for dirpath, dirnames, all_filenames in os.walk(src_dir):

        # filter all_filenames
        filenames = all_filenames
        if filenames:
            files = [os.path.join(dirpath, fname) for fname in filenames]
            # applicant form
            logger.info('↓↓↓ Starting to process 5257E ↓↓↓')
            in_fname = [f for f in files if '5257' in f][0]
            df_preprocessor = CanadaDataframePreprocessor()
            if len(in_fname) != 0:
                dataframe_applicant = df_preprocessor.file_specific_basic_transform(
                    path=in_fname,
                    type=DocTypes.canada_5257e)
            logger.info('↑↑↑ Finished processing 5257E ↑↑↑')
            # applicant family info
            logger.info('↓↓↓ Starting to process 5645E ↓↓↓')
            in_fname = [f for f in files if '5645' in f][0]
            if len(in_fname) != 0:
                dataframe_family = df_preprocessor.file_specific_basic_transform(
                    path=in_fname,
                    type=DocTypes.canada_5645e)
            logger.info('↑↑↑ Finished processing 5645E ↑↑↑')

            # final dataframe: concatenate common forms and label column wise
            dataframe = pd.concat(
                objs=[
                    dataframe_applicant,
                    dataframe_family],
                axis=1,
                verify_integrity=True)
        # logging
        logger.info(f'Processed the data point')
    logger.info('↑↑↑ Finished data loading ↑↑↑')
    return dataframe


@app.post(
    '/cvfe/v1/convert/adobe-xfa/',
    status_code=fastapi.status.HTTP_200_OK)
    # response_model=api_models.ConvertedXFAContentResponse)
async def process(
    form_5257: fastapi.UploadFile,
    form_5645: fastapi.UploadFile):
    try:
        # save files to disk
        input_path: Path = BASE_SOURCE_DIR / Path('x/')
        with open(input_path / Path('5257.pdf'), 'wb') as f:
            # read files
            contents_form_5257 = await form_5257.read()
            f.write(contents_form_5257)
        with open(input_path / Path('5645.pdf'), 'wb') as f:
            contents_form_5645 = await form_5645.read()
            f.write(contents_form_5645)
    except Exception as error:
        logger.exception(error)
        e = sys.exc_info()[1]
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e))
    try:
        
        data: pd.DataFrame = _process(BASE_SOURCE_DIR)

        logger.info('Process finished')
        return data.iloc[0].to_dict()
    
    except Exception as error:
        logger.exception(error)
        e = sys.exc_info()[1]
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=str(e))


if __name__ == '__main__':
    options = {
        'bind': f'{args.bind}:{args.port}',
        'workers': args.workers,
        'worker_class': 'uvicorn.workers.UvicornWorker'
    }
    # api_apps.StandaloneApplication(app=app, options=options).run()
    uvicorn.run(
        app=app,
        host=args.bind,
        port=args.port,
    )
