# RpiSimpleNDI

A Raspberry Pi project for simple NDI (Network Device Interface) functionality with LED screen testing capabilities.

## Project Overview

This repository contains tools and utilities for Raspberry Pi projects, including:

- **LED Test Pattern Generator**: A comprehensive test pattern generator for 320x320 LED screens
- **NDI Integration**: Simple NDI functionality for network video streaming
- **Display Management**: Tools for handling various display configurations on Raspberry Pi

## Features

### LED Test Pattern Generator
- Multiple test patterns optimized for 320x320 LED screens
- Automatic video driver detection (KMSDRM, DirectFB, X11)
- Position and rotation controls for display alignment
- Text-based orientation verification
- Real-time pattern cycling

### NDI Functionality
- Simple NDI sender/receiver implementation
- Network video streaming capabilities
- Raspberry Pi optimized performance

## Requirements

- Raspberry Pi (tested on Raspberry Pi OS)
- Python 3
- Pygame library
- HDMI display or LED screen
- Network connectivity (for NDI features)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd RpiSimpleNDI

# Install dependencies
sudo apt update
sudo apt install python3-pygame python3-pip

# Install additional NDI dependencies (if needed)
pip3 install ndi-python
```

## Usage

🎯 **For Studio Setup**: See [STUDIO_SETUP.md](STUDIO_SETUP.md) for complete instructions.

### LED Test Patterns
```bash
python3 led_test_pattern.py
```

**Controls:**
- **ESC**: Exit
- **SPACE**: Cycle patterns
- **P**: Cycle LED screen positions
- **R**: Cycle rotation angles

### NDI Receiver (Main Application)
```bash
python3 ndi_receiver_native_display.py
```

Receives 320x320 video from NDI source "catatumbo_led" and displays on LED screen.

## Project Structure

```
RpiSimpleNDI/
├── README.md                          # This file
├── STUDIO_SETUP.md                    # Quick setup guide for studio
├── led_test_pattern.py                # LED screen test pattern generator
├── ndi_receiver_native_display.py     # Main NDI receiver application
├── requirements.txt                   # Python dependencies
├── venv/                              # Virtual environment
└── docs/                              # Additional documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### LED Display Issues
- Use the text orientation pattern to verify screen alignment
- Cycle through positions with the P key to find your LED screen
- Use rotation controls (R key) for upside-down displays

### NDI Issues
- Ensure network connectivity
- Check firewall settings
- Verify NDI discovery is working

## Support

For issues and questions:
- Create an issue in this repository
- Check the documentation in the `docs/` folder
- Review troubleshooting guides

## Changelog

### v1.0.0
- Initial release
- LED test pattern generator with orientation testing
- Basic NDI functionality
- Raspberry Pi optimized display handling