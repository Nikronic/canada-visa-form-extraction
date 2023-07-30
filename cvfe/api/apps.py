# core
from gunicorn.app.base import BaseApplication
# helpers
from typing import Callable


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
        """Loads only those options that are valid
        """
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def init_webhooks(base_url):
    # Update inbound traffic via APIs to use the public-facing ngrok URL
    pass
