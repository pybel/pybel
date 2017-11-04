# -*- coding: utf-8 -*-

import re

BELFRAMEWORK_DOMAIN = 'http://resource.belframework.org'
OPENBEL_DOMAIN = 'http://resources.openbel.org'

METADATA_LINE_RE = re.compile("(SET\s+DOCUMENT|DEFINE\s+NAMESPACE|DEFINE\s+ANNOTATION)")
