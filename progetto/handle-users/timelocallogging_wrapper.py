import logging
from datetime import datetime, timedelta

class LocalTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Crea un oggetto datetime dal timestamp del log e aggiungi un'ora
        ct = datetime.fromtimestamp(record.created) + timedelta(hours=1)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            try:
                s = ct.isoformat(timespec='milliseconds')
            except TypeError:
                s = ct.isoformat()
        return s




