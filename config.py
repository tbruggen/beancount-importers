import sys

sys.path.append('.')

from importers.comdirect import ComdirectImporter

CONFIG = [ComdirectImporter('Assets:Comdirect:Checking', 'DE17200411110853623700')]


