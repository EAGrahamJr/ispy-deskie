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

The intent is to stuff it into https://www.thingiverse.com/thing:6683611 and just ignore the hole in the back.
