# 🎮 Source Engine Panorama Renderer

> [!NOTE]
> **Status**: Beta. The workflow is now fully automated but requires correct configuration of demo files.

> **Convert Half-Life 2 (and other Source) demos into immersive 8K 360° videos.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-green?style=for-the-badge&logo=ffmpeg)
![Source Engine](https://img.shields.io/badge/Engine-Source-orange?style=for-the-badge&logo=steam)

## ✨ Overview

This project provides a professional, automated workflow to render high-resolution panoramic videos from `.dem` files created in Valve's Source Engine games (Half-Life 2, Portal, etc.).

It automates the tedious process of:
1.  Launching the game and rendering **22 separate angles** (Spherical Rig) to ensure perfect coverage with a 60° FOV.
2.  Stitching those angles into a perfect Equirectangular generic projection using FFmpeg with advanced blending.
3.  Producing a YouTube-ready 360° video file.

## 🚀 Features

-   **Fully Automated**: Handles game launching, recording, and *exit* automatically. No manual intervention required.
-   **Robust 22-Angle Capture**: Uses a spherical rig layout (Equator, Upper/Lower Rings, Caps) to eliminate distortion and gaps.
-   **Smart Monitoring**: Detects when the demo finishes by analyzing the rendered frames for static content (e.g., game menu).
-   **High Resolution**: Supports 8K output.
-   **Hardware Acceleration**: Uses NVIDIA `hevc_nvenc` for lightning-fast stitching on RTX cards.
-   **Skip Rendering**: Support for `--stitch-only` to re-stitch existing frames without re-rendering.
-   **Audio Support**: Automatically extracts and includes game audio.

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python 3.8+**
2.  **FFmpeg** (Must be added to system PATH or specified in config).
3.  **Source Engine Game** (Half-Life 2, HL2: Episode 1/2, etc.).
4.  **Disk Space**: Rendering uncompressed TGA frames requires significant space (approx. 50-100GB for long demos).

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
    Copy the example environment file and configure your paths.
    ```bash
    cp .env.example .env
    ```
    
    Open `.env` in a text editor and update the variables:
    ```ini
    # Path to the game folder containing hl2.exe
    GAME_ROOT=C:\Games\Steam\steamapps\common\Half-Life 2
    
    # Name of the demo file inside the game folder (without .dem)
    DEMO_FILE=my_epic_gameplay
    
    # Resolution of ONE face (2048 = ~6K result, 4096 = 8K result)
    CUBE_FACE_SIZE=2048

    # Camera Field of View (Matches the capture rig settings)
    RIG_FOV=60.0
    
    # Blending width for stitching (0.0 to 1.0)
    BLEND_WIDTH=0.05
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
1.  **Render Phase**: The script will launch the game **22 times** (once for each angle).
    *   **Automation**: The script injects keypresses (F8-F12) to control the game.
    *   **Automated Exit**: Monitors rendered frames for static content (menu) to determine when the demo ends.
    *   *Do not interact with the computer while the game window is active*, as keyboard inputs are simulated.
2.  **Stitch Phase**: FFmpeg processes all 22 input streams at once.
    *   This step uses your GPU (NVENC) for performance.
3.  **Result**: The final video will be saved in the `output/` directory.

## 🔧 Technical Details

The tool uses a **Spherical Rig** capture method instead of a simple Cubemap. This provides better quality and overlap for stitching.

**Capture Geometry (22 Angles):**
-   **Ring 0 (Equator)**: 8 shots at Pitch 0° (every 45°)
-   **Ring 1 (Upper)**: 6 shots at Pitch +45° (every 60°)
-   **Ring 2 (Lower)**: 6 shots at Pitch -45° (every 60°)
-   **Zenith**: 1 shot at Pitch +90°
-   **Nadir**: 1 shot at Pitch -90°

It uses FFmpeg's `v360` filter with `input=tiles` (Rig Mode) to project these inputs into a single Equirectangular video stream.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.