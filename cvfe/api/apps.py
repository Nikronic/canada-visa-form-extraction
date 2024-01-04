import logging
import os
from typing import Callable, ClassVar

from gunicorn.app.base import BaseApplication
from pydantic_settings import BaseSettings

# config logger
logger = logging.getLogger(__name__)


class StandaloneApplication(BaseApplication):
    """A runner to help us parse ``argparse`` next to ``gunicorn`` args

    For options, you can visit https://docs.gunicorn.org/en/latest/settings.html
    """

    def __init__(self, app: Callable, options: dict = None):
        """Initialize runner

        Args:
            app (Callable): A callable as the ASGI/WSGI application
            options (dict, optional): A dictionary were keys are command line
                args and values are their corresponding values.
                Defaults to None.
        """
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        """Loads only those options that are valid"""
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def init_webhooks(base_url):
    # Update inbound traffic via APIs to use the public-facing ngrok URL
    pass


class Settings(BaseSettings):
    BASE_URL: ClassVar[str] = ""
    USE_NGROK: ClassVar[bool] = os.environ.get("USE_NGROK", "False") == "True"


def init_ngrok(host: str, port: int):
    # pyngrok should only ever be installed or initialized in a dev environment when this flag is set
    from pyngrok import ngrok

    # Open a ngrok tunnel to the dev server
    public_url = ngrok.connect(port).public_url
    logger.info(f'ngrok tunnel "{public_url}" -> "http://{host}:{port}"')

    # Update any base URLs or webhooks to use the public ngrok URL
    Settings.BASE_URL = public_url
    init_webhooks(public_url)
