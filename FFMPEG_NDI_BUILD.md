# Building FFmpeg with NDI Support on Raspberry Pi 5

This guide documents how to compile FFmpeg from source with NDI SDK support on Raspberry Pi OS.

## Why Build FFmpeg with NDI?

The standard FFmpeg package doesn't include NDI support. To use NDI with FFmpeg (for capturing, streaming, or converting NDI sources), you need to compile FFmpeg with the NDI SDK.

## Prerequisites

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install build dependencies
sudo apt install -y \
    build-essential \
    git \
    pkg-config \
    yasm \
    nasm \
    libx264-dev \
    libx265-dev \
    libnuma-dev \
    libvpx-dev \
    libfdk-aac-dev \
    libmp3lame-dev \
    libopus-dev \
    libass-dev \
    libfreetype6-dev \
    libgnutls28-dev \
    libsdl2-dev \
    libva-dev \
    libvdpau-dev \
    libvorbis-dev \
    libxcb1-dev \
    libxcb-shm0-dev \
    libxcb-xfixes0-dev \
    texinfo \
    wget \
    zlib1g-dev
```

## Step 1: Download NDI SDK

```bash
# Create build directory
mkdir -p ~/ffmpeg_build
cd ~/ffmpeg_build

# Download NDI SDK for Linux (ARM64)
# Visit: https://ndi.video/for-developers/ndi-sdk/download/
# Download the Linux ARM version (or use wget if direct link available)

# For this project, we used:
wget https://downloads.ndi.tv/SDK/NDI_SDK_Linux/Install_NDI_SDK_v6_Linux.tar.gz \
    -O ndi_sdk.tar.gz

# Extract the SDK
tar -xzf ndi_sdk.tar.gz
```

## Step 2: Install NDI Library

```bash
cd ~/ffmpeg_build

# Navigate to the extracted SDK directory
# (Directory name may vary based on SDK version)
cd "NDI SDK for Linux"

# The library is in lib/aarch64-rpi4-linux-gnueabi/ for Raspberry Pi
# Copy the NDI library to a system location
sudo cp lib/aarch64-rpi4-linux-gnueabi/libndi.so.6.* /usr/local/lib/

# Create a symlink
cd /usr/local/lib
sudo ln -sf libndi.so.6.* libndi.so.6
sudo ln -sf libndi.so.6 libndi.so

# Update library cache
sudo ldconfig

# Verify installation
ldconfig -p | grep ndi
# Should show: libndi.so.6 (libc6,AArch64) => /usr/local/lib/libndi.so.6
```

## Step 3: Copy NDI Headers

```bash
cd ~/ffmpeg_build/"NDI SDK for Linux"

# Copy NDI headers to system include directory
sudo mkdir -p /usr/local/include/ndi
sudo cp include/* /usr/local/include/ndi/

# Verify headers are installed
ls -la /usr/local/include/ndi/
```

## Step 4: Clone FFmpeg Source

```bash
cd ~/ffmpeg_build

# Clone FFmpeg repository
git clone https://git.ffmpeg.org/ffmpeg.git
cd ffmpeg

# Optional: Checkout a specific stable version
# git checkout release/6.1
# Or use latest from master branch (default)
```

## Step 5: Configure FFmpeg

```bash
cd ~/ffmpeg_build/ffmpeg

# Configure FFmpeg with NDI support
./configure \
    --prefix=/usr/local \
    --enable-gpl \
    --enable-nonfree \
    --enable-libx264 \
    --enable-libx265 \
    --enable-libvpx \
    --enable-libfdk-aac \
    --enable-libmp3lame \
    --enable-libopus \
    --enable-libass \
    --enable-libfreetype \
    --enable-gnutls \
    --enable-libndi_newtek \
    --extra-cflags="-I/usr/local/include/ndi" \
    --extra-ldflags="-L/usr/local/lib" \
    --extra-libs="-lndi" \
    --enable-shared

# Note: The configure script will check for dependencies
# If anything is missing, install it and run configure again
```

### Common Configure Issues

**Problem**: `libndi_newtek not found`
```bash
# Make sure library and headers are in the right place:
ls -la /usr/local/lib/libndi.so*
ls -la /usr/local/include/ndi/

# Update PKG_CONFIG_PATH if needed:
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
```

**Problem**: Missing dependencies
```bash
# Install whatever is reported as missing, for example:
sudo apt install libx264-dev
# Then re-run configure
```

## Step 6: Build FFmpeg

```bash
cd ~/ffmpeg_build/ffmpeg

# Build FFmpeg (this takes a LONG time on Raspberry Pi - 1-3 hours)
make -j4

# Use -j4 for Raspberry Pi 5 (4 cores)
# Expect this to take 60-180 minutes depending on Pi model
```

## Step 7: Install FFmpeg

```bash
cd ~/ffmpeg_build/ffmpeg

# Install FFmpeg system-wide
sudo make install

# Update library cache
sudo ldconfig
```

## Step 8: Verify Installation

```bash
# Check FFmpeg version and NDI support
ffmpeg -version

# List available input devices - should include libndi_newtek
ffmpeg -devices 2>&1 | grep ndi

# Expected output:
#  DE libndi_newtek    Network Device Interface (NDI) input/output

# Test NDI source discovery
ffmpeg -f libndi_newtek -find_sources 1 -i dummy -t 1 -f null -

# This should list available NDI sources on your network
```

## Troubleshooting

### FFmpeg Not Finding NDI Library

```bash
# Check library path
ldd /usr/local/bin/ffmpeg | grep ndi

# If not found, add library path:
echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/local.conf
sudo ldconfig
```

### Old FFmpeg Still Running

```bash
# Check which ffmpeg is being used
which ffmpeg
# Should show: /usr/local/bin/ffmpeg

# If it shows /usr/bin/ffmpeg, update PATH:
export PATH=/usr/local/bin:$PATH

# Make it permanent:
echo 'export PATH=/usr/local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Rebuild After Changes

```bash
cd ~/ffmpeg_build/ffmpeg

# Clean previous build
make clean

# Reconfigure and rebuild
./configure [options as above]
make -j4
sudo make install
```

## Using FFmpeg with NDI

### List NDI Sources
```bash
ffmpeg -f libndi_newtek -find_sources 1 -i dummy -t 1 -f null -
```

### Receive NDI Stream
```bash
ffmpeg -f libndi_newtek -i "SOURCE_NAME (IP_ADDRESS)" output.mp4
```

### Receive and Display
```bash
ffplay -f libndi_newtek -i "SOURCE_NAME (IP_ADDRESS)"
```

### Convert NDI to RTMP
```bash
ffmpeg -f libndi_newtek -i "SOURCE_NAME" \
    -c:v libx264 -preset veryfast -b:v 2500k \
    -c:a aac -b:a 128k \
    -f flv rtmp://server/live/stream
```

## Build Information

**Hardware**: Raspberry Pi 5 (4GB/8GB)  
**OS**: Raspberry Pi OS (Debian 12 - Bookworm/Trixie)  
**NDI SDK Version**: 6.x  
**FFmpeg Version**: Latest from git (or specify your version)  
**Build Time**: ~90-120 minutes on RPi 5  

## Alternative: Pre-built FFmpeg

If you need FFmpeg with NDI on multiple Raspberry Pis:

### Save Built FFmpeg
```bash
# After building, create a tarball
cd /usr/local
sudo tar -czf ~/ffmpeg-ndi-rpi5.tar.gz \
    bin/ffmpeg bin/ffprobe bin/ffplay \
    lib/libav*.so* lib/libsw*.so* lib/libpost*.so* \
    include/libav* include/libsw* include/libpost*
```

### Install on Another Pi
```bash
# Copy tarball to other Pi, then:
cd /usr/local
sudo tar -xzf ~/ffmpeg-ndi-rpi5.tar.gz

# Don't forget to install NDI library separately!
sudo cp libndi.so.6.* /usr/local/lib/
sudo ldconfig
```

## Cleanup

```bash
# After successful installation, you can remove build directory
# (Keep it if you might need to rebuild later)
rm -rf ~/ffmpeg_build

# This frees up ~2-3GB of space
```

## References

- FFmpeg Official: https://ffmpeg.org/
- NDI SDK: https://ndi.video/for-developers/ndi-sdk/
- FFmpeg Compilation Guide: https://trac.ffmpeg.org/wiki/CompilationGuide
- NDI Developer Documentation: https://docs.ndi.video/

---

**Last Updated**: October 10, 2025  
**Tested On**: Raspberry Pi 5, Raspberry Pi OS Bookworm/Trixie

