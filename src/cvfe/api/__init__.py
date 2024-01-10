import logging

from cvfe.utils.import_utils import safe_import

# set logger
logger = logging.getLogger(__name__)


convert = safe_import("cvfe.api.convert.adobe_xfa", "convert", "api")
