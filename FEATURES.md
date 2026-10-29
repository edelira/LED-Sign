# LED Sign: features and decisions

Living list of what the sign should do. Items marked *later* are ideas parked
for when we get there.

## Hardware (current plan)
- Display: 3× 64×64 P3 HUB75 panels (xicoolee, FM6124 driver chips) = 192×64,
  576 × 192 mm (22.7" × 7.6"). One panel tested OK on an ESP32-WROOM via ESPHome.
- Controller: Raspberry Pi (owner has a Pi 5 to find). Pi 5 needs Adafruit's
  PIO-based matrix driver; the Adafruit Triple LED Matrix Bonnet (#6358) drives
  3 panels on separate outputs and has an E-line switch (no soldering).
  Fallback: Adafruit Matrix Portal S3 (`esphome/led-sign-matrixportal.yaml`).
- Power: MEAN WELL LRS-100-5 (5V 18A).
- Frame: 3D printed on a Bambu P1S, black PLA, smoked acrylic front
  (`enclosure/`, to be resized for 3× 64×64 P3).
- ESP32-WROOM: spare, planned as a train microphone sensor.

## Architecture
- The Pi runs the logic and all rendering/animation (smooth animations are a goal).
- Home Assistant pushes home things to the Pi over MQTT (Mosquitto add-on);
  the Pi reports sign controls and events back to HA.

## Screens, by priority
1. **Kitchen timer** (Google Home kitchen speaker or display, via the HACS
   `ha-google-home` integration). Big countdown, then "TIME'S UP". Can share
   the screen with a passing train.
2. **Train passing** (Metra BNSF, Amtrak, freight). Shown as it passes, not as
   an "approaching" countdown. ~30 s on screen. Several trains get one row each.
   - Metra: GTFS-Realtime (needs free API key, not requested yet).
   - Amtrak: Amtraker API (Southwest Chief, California Zephyr, Illinois Zephyr,
     Carl Sandburg).
   - Freight: no public data; local detection (camera, later microphone) when no
     Metra/Amtrak train is due.
   - Home is on the BNSF "Racetrack" between Harlem Ave and Riverside.
3. **Leave-by alert**: next Google Calendar event with an address, drive time via
   Waze Travel Time, "LEAVE IN x MIN" then "LEAVE NOW". Calendar choice and
   buffer: owner to decide later.
4. **Plane overhead**: adsb.lol (free) + adsbdb routes. Closest plane within a
   radius/altitude limit. Mini-radar layout on the left panel.
5. *later* **Now playing**: when the kitchen speaker is playing music, show
   title, artist and album art. HA pushes it from the speaker's media_player.
6. **Idle**: clock + weather.

Dropped: Metra service alerts.

## Calibration test (before trusting pass timing)
- HA/Pi predicts each pass; Pixel notification with an "I SEE IT" button;
  owner taps when the front of the train is behind the house. Log predicted vs
  actual to CSV, then compute average offset and spread per direction and
  express/local.
- Goal: show the train ~5 s before it passes. If the feed alone is off by more
  than ~10 s, add the microphone or camera for timing.

## Open decisions (owner)
- Calendar(s) to watch and travel buffer.
- Night behaviour (decide after real-world testing).
- Final layouts (mock-ups A–G for 192×64).
