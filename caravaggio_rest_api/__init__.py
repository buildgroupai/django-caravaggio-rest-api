
r"""
  _____                                  _        ___  ______________  ___   ___  ____
 / ______ ________ __  _____ ____ ____ _(____    / _ \/ __/ __/_  __/ / _ | / _ \/  _/
/ /__/ _ `/ __/ _ `| |/ / _ `/ _ `/ _ `/ / _ \  / , _/ _/_\ \  / /   / __ |/ ____/ /
\___/\_,_/_/  \_,_/|___/\_,_/\_, /\_, /_/\___/ /_/|_/___/___/ /_/   /_/ |_/_/  /___/
                            /___//___/
"""

__title__ = 'Django Caravaggio REST API for Big Data'
__version__ = '1.0.0'
__author__ = 'Javier Alperte'
__license__ = 'BSD 2-Clause'
__copyright__ = 'Copyright 2018-2019 PreSeries Tech S.L.'

# Version synonym
VERSION = __version__

# Header encoding (see RFC5987)
HTTP_HEADER_ENCODING = 'iso-8859-1'

# Default datetime input and output formats
ISO_8601 = 'iso-8601'

default_app_config = 'caravaggio_rest_api.apps.CaravaggioRESTAPIConfig'
