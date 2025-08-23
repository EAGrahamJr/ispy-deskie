# Yet Another Desktop Thingie

This one has an SH1106 and uses the ESP32's built-in WiFi to set the RTC to NTP time and also retrieve the local weather.

Example `settings.toml`:
```toml
WIFI_SSID="WIFI"
WIFI_PASSWORD="PASSWORD"

# defaults - pauses are in **MINUTES**
WEATHER_PAUSE=15
WEATHER_STATION="kbfi"

NTP_PAUSE=60

```

This is stuffed into a https://www.printables.com/model/125366-adafruit-qtpy-case -- the latest addition has an
`adafruit_ahtx0` also included for getting the local environment.
