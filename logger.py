import rtc
import adafruit_logging as logging
from adafruit_logging import LogRecord, Logger

class LogHandler(logging.StreamHandler):
    def __init__(self) -> None:
        super().__init__()

    def format(self, rec: LogRecord) -> str:
        time = rtc.RTC().datetime
        return (
            f"[{time.tm_hour:02d}:{time.tm_min:02d}] {rec.name}: {rec.levelname} - {rec.msg}"
        )

def get_logger(name:str, level = logging.INFO)-> Logger:
    rtn = logging.getLogger(name)
    rtn.addHandler(LogHandler())
    rtn.setLevel(level)
    return rtn
