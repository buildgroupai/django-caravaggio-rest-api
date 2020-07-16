r"""
  _____                                  _
 / ______ ________ __  _____ ____ ____ _(____
/ /__/ _ `/ __/ _ `| |/ / _ `/ _ `/ _ `/ / _ \
\___/\_,_/_/  \_,_/|___/\_,_/\_, /\_, /_/\___/
                            /___//___/
"""

__title__ = "Django Caravaggio REST API for Big Data"
__version__ = "0.1.7-SNAPSHOT"
__author__ = "Javier Alperte"
__license__ = "MIT"
__copyright__ = "Copyright 2019 BuildGroup Data Services Inc."

# Version synonym
VERSION = __version__

# Header encoding (see RFC5987)
HTTP_HEADER_ENCODING = "iso-8859-1"

# Default datetime input and output formats
ISO_8601 = "iso-8601"

default_app_config = "caravaggio_rest_api.apps.CaravaggioRESTAPIConfig"
