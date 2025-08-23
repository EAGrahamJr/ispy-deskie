import asyncio
import os
import rtc

import wifi
import socketpool
import adafruit_ntp

from logger import get_logger

class EnvData:
    def __init__(self, t, g, h):
        self.temperature = t
        self.gas = g
        self.humidity = h
        self.air_quality = 0
        self.pressure = 0

class RadioHead:

    def __init__(self, env: EnvData):
        self.env = env
        pool = socketpool.SocketPool(wifi.radio) # type: ignore
        self.ntp = adafruit_ntp.NTP(pool,tz_offset=-7,cache_seconds=3600)
        self.logger = get_logger(__name__)

        # read ENV
        # pause in minutes between updates
        self._time_pause = int(
            os.getenv("NTP_PAUSE", "60")
        )
        self._ssid = os.getenv("WIFI_SSID")
        self._password = os.getenv("WIFI_PASSWORD")

    async def run_time(self):
        while True:
            if wifi.radio.connected: # type: ignore
                try:
                    rtc.RTC().datetime = self.ntp.datetime
                    self.logger.info("Got time")
                    await asyncio.sleep(self._time_pause)
                except Exception as e:
                    self.logger.error(f"Unable to get time: {str(e)}")
            else:
                self.logger.warning("time waiting on connection")
                await asyncio.sleep(15)


    async def connect_wifi(self):
        """
        (Re-)Connect to the network.
        """
        self.logger.debug("Checking WiFi")
        while not wifi.radio.connected:# type: ignore
            try:
                self.logger.info(f"Connecting to WiFi '{self._ssid}'")
                wifi.radio.connect(# type: ignore
                    ssid=self._ssid, password=self._password
                )
            except Exception as e:
                self.logger.error(f"Error connecting wifi to '{self._ssid}': {str(e)}")

            if not wifi.radio.connected:# type: ignore
                await asyncio.sleep(10)
            else:
                addr = wifi.radio.ipv4_address # type: ignore
                self.logger.warning(f"Connected to WiFi  - IP address: {addr}")
