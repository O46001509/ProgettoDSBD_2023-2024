import logging
from datetime import datetime, timedelta

# Classe per impostare l'ora locale (ITA = ENG + 1).
class LocalTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Creo un oggetto datetime dal timestamp del log ed aggiungo un'ora
        ct = datetime.fromtimestamp(record.created) + timedelta(hours=1)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            try:
                s = ct.isoformat(timespec='milliseconds')
            except TypeError:
                s = ct.isoformat()
        return s




