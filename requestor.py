from abc import ABC
import asyncio
import adafruit_requests
import ssl
import socketpool
import wifi

from logger import get_logger
from radio import EnvData


class Requestor(ABC):
    def __init__(self, env_data:EnvData):
        self.logger = get_logger(__name__)
        self.pool = socketpool.SocketPool(wifi.radio) # type: ignore
        self.env_data = env_data

    async def _run_request(
            self,
            uri: str,
            what: str,
            parser,
            pause: int = 15,
            rqst_headers = None
    ):
        while True:
            if wifi.radio.connected: # type: ignore
                request = adafruit_requests.Session(
                    self.pool, ssl.create_default_context()
                )
                response = None

                try:
                    self.logger.info(f"Getting {what}")
                    response = request.get(uri, headers=rqst_headers)
                    parser(response)

                except Exception as e:
                    self.logger.error(f"Unable to get {what}: {str(e)}")
                finally:
                    if response is not None:
                        response.close()
                await asyncio.sleep(pause * 60)
            # otherwise wait for a connection
            else:
                self.logger.warning(f"{what} waiting on connection")
                await asyncio.sleep(15)
