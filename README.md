# Batocerai2c2OLED

Batocera OLED marquee daemon for **SSD1306 128x64 I2C displays** on Raspberry Pi.

This project adds a small OLED screen to Batocera systems that shows
system information in the menu and game marquee artwork while playing games.

---

## Features

### Menu Mode
Displayed when no game is running.

- BATOCERA banner in the yellow band (bicolor OLED)
- Rotating status pages (4 lines per page)
- Information shown:
  - IP address
  - CPU temperature
  - Memory usage
  - Raspberry Pi type and core count

## Game Mode

Displayed automatically when a game is launched.

-   Shows the game **marquee / wheel / logo artwork**
-   Automatically detected from:
    -   `<marquee>` entries in `gamelist.xml`
    -   `<image>` fallback entries
    -   `images/` directory
-   Cached rendering for performance
-   Falls back to text if no artwork is found

### Intelligent Rendering Engine

The marquee renderer uses a hybrid system:

-   Transparent PNG artwork → uses alpha mask (clean edges, no
    background square)
-   Opaque artwork → uses original 1-bit monow conversion (preserves
    interior details)
-   Combined mask + detail logic prevents:
    -   Solid blobs
    -   Background noise
    -   Loss of interior lettering

## Screenshots

### Main Menu Display
Shows system information when no game is running.

![Menu Mode OLED](screenshots/mainmenu1.jpg)
![Menu Mode OLED](screenshots/mainmenu2.jpg)

### Game Marquee Display
Shows the game marquee artwork while a game is running.

![Game Mode OLED](screenshots/game-mode.jpg)

---

## Wiring Diagram (SSD1306 I2C)

### Raspberry Pi 5 → SSD1306 128x64

| OLED Pin | Raspberry Pi Pin | Description |
|--------|------------------|-------------|
| GND    | GND              | Ground |
| VCC    | 3.3V             | Power |
| SDA    | GPIO 2 (Pin 3)   | I2C Data |
| SCL    | GPIO 3 (Pin 5)   | I2C Clock |

> ⚠️ **Important**
> - Use **3.3V**, not 5V.
> - Most SSD1306 modules default to I2C address `0x3C`.
> - I2C must be enabled in Batocera.

Example wiring reference:

![SSD1306 Wiring](screenshots/wiring.jpg)
![SSD1306 Wiring](screenshots/wiring-diagram.jpg)

---

## Tested Hardware

- Batocera ES **v41** (2024-11-28)
- Raspberry Pi 5
- SSD1306 128x64 I2C **bicolor (yellow / blue)**
- Framebuffer device: `/dev/fb1`

------------------------------------------------------------------------

# Installation (No Git)

Batocera does not include Git by default.

Installation is done using a release ZIP file.

## Step 1 --- Download

Download the latest release from:

https://github.com/jeborgesm/Batocerai2c2OLED/releases

Download:

Batocerai2c2OLED-vX.X.zip

------------------------------------------------------------------------

## Step 2 --- Extract

Extract the ZIP file on your computer.

You will see a folder named:

userdata/

------------------------------------------------------------------------

## Step 3 --- Copy to Batocera

### On Windows

1.  Open File Explorer

2.  In the address bar type:

    \\\\BATOCERA

    (or \\\\192.168.x.x)

3.  Open the `share` folder

4.  Drag the extracted `userdata` folder into `share`

5.  Allow overwrite if prompted

### On macOS

1.  Finder → Go → Connect to Server

2.  Enter:

    smb://batocera

3.  Open the `share` folder

4.  Drag the `userdata` folder into it

5.  Allow overwrite if prompted

------------------------------------------------------------------------

## Step 4 --- Enable the Service

On Batocera:

Main Menu → System Settings → Services → OLED_DAEMON → ON

Reboot recommended.

![Batocera Services Menu](screenshots/batocera-services.jpg)

------------------------------------------------------------------------

# Uninstall

Delete these folders from:

/userdata/system/

-   bin/oled_daemon.py
-   scripts/oled_state.sh
-   services/OLED_DAEMON

Then disable the service:

Main Menu → System Settings → Services → OLED_DAEMON → OFF

Reboot.

------------------------------------------------------------------------

## How It Works

- Batocera runs `/userdata/system/services/OLED_DAEMON` at boot.
- `oled_state.sh` is called by Batocera when games start or stop.
- Game state is written to:

```
/tmp/oled.state
```

- `oled_daemon.py` reads this state and:
  - Displays system metrics in menu mode
  - Displays game artwork in game mode
- Artwork is converted to 1-bit and written directly to
  `/dev/fb1`.

------------------------------------------------------------------------

# Artwork Recommendations

For best results:

-   Scrape artwork for your systems.
-   Prefer high-contrast PNG marquees.
-   Transparent background marquees give the cleanest output.

Supported sources:

-   `<marquee>` in `gamelist.xml` (highest priority)
-   `<image>` fallback
-   Files inside system `images/` folder

Supported naming examples:

-   romname-marquee.png
-   romname-wheel.png
-   romname-logo.png
-   romname.png

------------------------------------------------------------------------

# Technical Notes

-   Designed specifically for Batocera Linux
-   Uses Batocera's native service system
-   No RetroPie patches required
-   Minimal dependencies:
    -   Python
    -   ffmpeg
    -   Pillow (PIL)

------------------------------------------------------------------------

## Notes

- Designed specifically for **Batocera Linux**
- Does not rely on RetroPie scripts or patches
- Uses Batocera’s native service system
- Minimal dependencies (Python + ffmpeg)

---

## Credits

Inspired by RetroPie OLED projects,  
implemented natively for Batocera Linux.

---

## License

MIT License

Copyright (c) 2026 Jaime Borges

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
