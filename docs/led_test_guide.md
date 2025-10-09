# LED Test Guide

This guide explains how to use the LED test pattern generator for 320x320 LED screens on Raspberry Pi.

## Quick Start

1. Run the test pattern generator:
   ```bash
   python3 led_test_pattern.py
   ```

2. Use the text orientation pattern to verify screen alignment
3. Use P key to find the correct position of your LED screen
4. Use R key to rotate if the display is upside down

## Pattern Types

### Text Orientation
Shows "TOP", "BOTTOM", "LEFT", "RIGHT" labels around the screen edges. This is the first pattern and helps verify correct orientation.

### Arrow Pattern
Colored arrows pointing in cardinal directions:
- Red arrow pointing up
- Green arrow pointing down  
- Blue arrow pointing left
- Yellow arrow pointing right

### Color Bars
Horizontal bars in primary colors for color testing.

### Grid Pattern
16x16 grid pattern for pixel alignment testing.

### Gradient Circle
Radial gradient from red to blue for smoothness testing.

### Checkerboard
Black and white checkerboard for contrast testing.

### Concentric Circles
Multiple colored circles for geometric testing.

### All Patterns
Combined view showing multiple patterns in quadrants.

## Controls

- **ESC**: Exit the program
- **SPACE**: Manually cycle through patterns
- **P**: Cycle through LED screen positions (corners and center)
- **R**: Cycle through rotation angles (0°, 90°, 180°, 270°)

## Troubleshooting

### Screen Appears Upside Down
Use the R key to cycle through rotations until text is readable.

### Can't Find LED Screen
Use the P key to cycle through different positions on the 800x800 display.

### Display Not Working
The script automatically handles video driver selection. Check HDMI connection and power.
