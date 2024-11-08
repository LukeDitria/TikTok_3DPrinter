# TikTok 3D Printer Controller

Control your 3D printer through TikTok live comments and gifts! Let your viewers interact with your 3D printer in real-time.

## Requirements

- Raspberry Pi (any model with WiFi)
- Python >= 3.10
- 3D printer that connects via USB to recieve GCode
- USB cable to connect printer to Raspberry Pi
- TikTok account

## Quick Start Guide

1. Clone this project to your Raspberry Pi
   ```commandline
   git clone https://github.com/LukeDitria/TikTok_3DPrinter.git
   ```
2. Connect your 3D printer to the Raspberry Pi via USB
3. Open a terminal and navigate to the project folder
4. Run the installation script:ls
   ```bash
   chmod +x install.sh 
   ./install.sh
   ```
5. Follow the prompts to enter your TikTok username and printer port
6. Start the program:
   ```bash
    ./run.sh start   # Start in background
    ./run.sh stop    # Stop the program
    ./run.sh status  # Check if running
    ./run.sh logs    # View logs
    ```

## How It Works

### Viewer Commands
Viewers can control the printer using these commands in TikTok live chat:
- `forward` - Move printer forward
- `back` - Move printer backward
- `left` - Move printer left
- `right` - Move printer right
- `up` - Move print head up
- `down` - Move print head down

### Gifts
When viewers send gifts, they contribute to the "filament count"! The more valuable the gift, the more filament gets added.<br>
A fixed amount of filament is extruded whenever the printer moves as long as the filament count is above zero!


## Safety Features

- Temperature limits prevent overheating
- Movement boundaries keep the printer safe
- Command queue prevents overflow
- Simulation mode for testing

## Troubleshooting

### Common Issues

1. **Can't find printer port?**
   - Make sure your printer is connected and powered on
   - Try unplugging and reconnecting the USB cable
   - Common ports are `/dev/ttyUSB0` or `/dev/ttyACM0`

2. **TikTok connection issues?**
   - Verify your internet connection
   - Make sure your TikTok username is correct in config.json
   - Check that you're logged into TikTok and have permissions to go live

3. **Printer not responding?**
   - Check if your printer is turned on
   - Verify the USB connection
   - Make sure the correct port is set in config.json

### Getting Help

If you run into problems:
1. Check the `printer_stream.log` file in the logs directory
2. Make sure your printer firmware is up to date
3. Try running in simulation mode by setting `"enabled": true` under "simulation" in config.json

## Configuration

The `config.json` file contains all settings:

- Printer settings (speed, temperatures, etc.)
- TikTok connection settings
- Safety limits
- Logging preferences

## Advanced Settings

For advanced users who want to modify the behavior:

1. **Adjust Movement Speed**
   - Edit `"feed_rate"` in config.json

2. **Change Temperature Limits**
   - Modify `"max_extrude_temp"` and `"min_extrude_temp"` under "safety"

3. **Adjust the amount of filament added per gift amount**
   - Change `"extrude_amount"` under "tiktok" > "commands"

## Warning ⚠️

Always monitor your printer during operation. While safety features are built-in, your 3D printer may become damaged. 
TikTok may also disable your live if it detects that you are not there and will give you a "Captcha - like" problem to solve to keep your live active.