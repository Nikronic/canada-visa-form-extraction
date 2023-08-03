# Ours: API
from cvfe.api import models as api_models
from cvfe.api import apps as api_apps
from cvfe.api.convert.adobe_xfa import router as adobe_xfa_router
# API
import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
# helpers
import argparse
import logging


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

# configure logging
logger = logging.getLogger(__name__)
logger.setLevel(VERBOSE)


# instantiate FastAPI app and NGROK (optional)
app = fastapi.FastAPI()
settings = api_apps.Settings()

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
    api_apps.init_ngrok(
        host=args.bind,
        port=args.port)


app.include_router(adobe_xfa_router)

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
        workers=args.workers,
    )
