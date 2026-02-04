# 🎮 Source Engine Panorama Renderer

A powerful, fully automated pipeline for preserving your favorite Source Engine moments in Virtual Reality. This tool captures game demos from titles like **Half-Life 2** and **Portal 2**, rendering them into **high-fidelity 8K 360° panoramic videos** suitable for VR headsets and YouTube VR. By leveraging custom FFmpeg filters and automated engine control, it seamlessly stitches multiple view angles into a perfect immersive experience.

> [!NOTE]
> **Status**: Beta. Development and debugging are in progress. Primary support for Half-Life 2 and Portal 2.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-green?style=for-the-badge&logo=ffmpeg)
![Source Engine](https://img.shields.io/badge/Engine-Source-orange?style=for-the-badge&logo=steam)

## ✨ Overview

This project provides a professional, automated workflow to render high-resolution panoramic videos from `.dem` files created in Valve's Source Engine games (Half-Life 2, Portal, etc.).

It automates the tedious process of:
1.  Launching the game and rendering **22 separate angles** (Spherical Rig) to ensure perfect coverage with a 60° FOV.
2.  Stitching those angles into a perfect Equirectangular generic projection using FFmpeg with advanced blending.
3.  Producing a YouTube-ready 360° video file.


## 🎞️ Examples

### Half-Life 2 RTX
![Half-Life 2 RTX Animation](assets/hl2rtx-example.gif)

### Portal 2
![Portal 2 Animation](assets/portal2-example.gif)

## 🚀 Features

-   **Fully Automated**: Handles game launching, recording, and *exit* automatically. No manual intervention required.
-   **Robust 22-Angle Capture**: Uses a spherical rig layout (Equator, Upper/Lower Rings, Caps) to eliminate distortion and gaps.
-   **Smart Monitoring**: Detects when the demo finishes by analyzing the rendered frames for static content (e.g., game menu).
-   **Smart Compression**: Automatically converts raw TGA screenshots to high-quality JPEGs on the fly, significantly reducing disk space requirements during large renders.
-   **High Resolution**: Supports 8K output.
-   **Hardware Acceleration**: Uses NVIDIA `hevc_nvenc` for lightning-fast stitching on RTX cards.
-   **Skip Rendering**: Support for `--stitch-only` to re-stitch existing frames without re-rendering.
-   **Audio Support**: Automatically extracts and includes game audio.
-   **Player Model Hiding**: Automatically replaces the player model with an unobtrusive "battery" model during rendering to prevent camera obstruction.
-   **Multi-Game Support**: Works with Half-Life 2, Portal 2, and other Source Engine games.
-   **Flexible Capture Modes**: Choose between high-quality "Sphere" mode (22 shots) or faster "Cube" mode (6 shots).

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python 3.8+**
2.  **FFmpeg** (Specific Custom Build Required - see below).
3.  **Source Engine Game** (Half-Life 2, HL2: Episode 1/2, etc.).
4.  **Disk Space**: Rendering uncompressed TGA frames requires significant space (approx. 50-100GB for long demos).

## ⚡ Custom FFmpeg Requirements

This project requires a **modified version of FFmpeg** powered by the [FFmpeg v360 Filter - Advanced Rig Mode](https://github.com/artryazanov/ffmpeg-v360-advanced) project. Standard FFmpeg builds **will not work** correctly because they lack the "Rig Mode" (`input=tiles`) feature required for our 22-angle stitching. This advanced extension introduces a robust solution for transforming multiple directional video inputs into a cohesive 360° panoramic output with high-quality blending.

### 📥 Download Recommended Build (Windows)
**[Download ffmpeg-n8.0.1-v360-advanced-v1.3-gpl-amd64-static.zip](https://github.com/artryazanov/ffmpeg-msvc-prebuilt/releases/download/n8.0.1-v360-advanced-v1.3/ffmpeg-n8.0.1-v360-advanced-v1.3-gpl-amd64-static.zip)**

*For other architectures (ARM, x86, Shared libraries), check the [Release Page](https://github.com/artryazanov/ffmpeg-msvc-prebuilt/releases/tag/n8.0.1-v360-advanced-v1.3).*

### ✨ Key Features of this Build
*   **Exclusive "Rig Mode"**: Designed for high-fidelity panoramic stitching from arbitrary multi-camera setups.
*   **Seamless Blending**: Uses weighted inverse projection to eliminate seams between the 22 angles.
*   **Performance**: Compiled with MSVC and optimized for Windows.

> [!IMPORTANT]
> Extract the `bin/ffmpeg.exe` from the zip and either add it to your system PATH or configure the path in your `.env` file.

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/thegamerbay/source-panorama-renderer.git
    cd source-panorama-renderer
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Configuration**:
    Copy the example environment file for your game and configure your paths.

    For **Half-Life 2**:
    ```bash
    cp .env.hl2.example .env
    ```

    For **Half-Life 2 RTX**:
    ```bash
    cp .env.hl2rtx.example .env
    ```

    For **Portal 2**:
    ```bash
    cp .env.portal2.example .env
    ```
    
    Open `.env` in a text editor and update the variables:
    ```ini
    # Path to your game folder (containing hl2.exe or portal2.exe)
    GAME_ROOT=C:\Program Files (x86)\Steam\steamapps\common\Portal 2
    ENGINE_TYPE=portal2
    MOD_DIR=portal2
    
    # Name of the demo file inside the game folder (without .dem)
    DEMO_FILE=test1_3
    
    # Panorama Mode: 'sphere' (22-shot, 60 FOV) or 'cube' (6-shot, 90 FOV)
    PANORAMA_MODE=cube
    
    # Resolution of ONE face
    # Sphere mode: 640 = 4K panorama, 1280 = 8K panorama
    # Cube mode: 1024 = 4K panorama, 2048 = 8K panorama
    CUBE_FACE_SIZE=1024
    
    # Path to FFmpeg executable
    FFMPEG_BIN=D:\Games\FFmpeg-v360-advanced\ffmpeg.exe
    ```

> [!WARNING]
> Your `.dem` file must reside inside the game/mod directory (e.g., `hl2/`). The script cannot access files outside the game's sandbox.

## 🎥 Recording Demos

To use this tool, you first need a Source Engine demo file (`.dem`).

1.  **Launch the Game** (Half-Life 2, etc.).
2.  **Enable Console**: Go to Options -> Keyboard -> Advanced -> Enable Developer Console.
3.  **Start Recording**:
    - Open the console (usually `~` key).
    - Type: `record my_epic_gameplay`
    - Play the game!
4.  **Stop Recording**:
    - Open console and type: `stop`
5.  **Verify**:
    - Type `playdemo my_epic_gameplay` to watch it back.
    - Use `Shift + F2` (or type `demoui`) to open playback controls.

## 🎬 Usage

To start the full render process (Render + Stitch):

```bash
python main.py
```

To skip the rendering phase and just re-stitch existing frames (useful for tweaking stitch settings):

```bash
python main.py --stitch-only
```

### The Process
1.  **Render Phase**: The script will launch the game **multiple times** (once for each angle).
    *   **Automation**: The script injects keypresses (F8-F12) to control the game.
    *   **Automated Exit**: Monitors rendered frames for static content (menu) to determine when the demo ends.
    *   **Player Model Replacement**: Before rendering, the script automatically copies a custom `player.mdl` (battery model) to the game's `models/` directory to ensure the player's view is not obstructed by the default weapon or character model.
    *   *Do not interact with the computer while the game window is active*, as keyboard inputs are simulated.
2.  **Stitch Phase**: FFmpeg processes all input streams at once.
    *   This step uses your GPU (NVENC) for performance.
3.  **Result**: The final video will be saved in the `output/` directory.

## 🔧 Technical Details

The tool supports two capture methods:

### 1. Sphere Mode (Recommended for Quality)
Uses a **Spherical Rig** with **22 angles** (FOV 60°) to ensure perfect coverage and overlap for high-quality stitching.

**Geometry:**
-   **Ring 0 (Equator)**: 8 shots at Pitch 0° (every 45°)
-   **Ring 1 (Upper)**: 6 shots at Pitch +45° (every 60°)
-   **Ring 2 (Lower)**: 6 shots at Pitch -45° (every 60°)
-   **Zenith**: 1 shot at Pitch +90°
-   **Nadir**: 1 shot at Pitch -90°

### 2. Cube Mode (Faster)
Uses a standard **Cubic** layout with **6 angles** (FOV 90°). This is faster to render but may have less overlap for blending.

**Geometry:**
-   Front, Back, Left, Right, Up, Down (standard box mapping)

Both modes use FFmpeg's `v360` filter with `input=tiles` (Rig Mode) to project these inputs into a single Equirectangular video stream.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.