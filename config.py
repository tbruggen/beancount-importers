import sys

sys.path.append('.')

from importers.comdirect import ComdirectImporter

CONFIG = [ComdirectImporter('Assets:Comdirect:Gemeinschaftskonto', 'DE17200411110853623700')]


