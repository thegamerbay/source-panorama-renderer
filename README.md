# 🎮 Source Engine Panorama Renderer

> [!CAUTION]
> **WORK IN PROGRESS**: This project is currently in active development. Features may be unstable, and the workflow requires some manual intervention.

> **Convert Half-Life 2 (and other Source) demos into immersive 8K 360° videos.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-green?style=for-the-badge&logo=ffmpeg)
![Source Engine](https://img.shields.io/badge/Engine-Source-orange?style=for-the-badge&logo=steam)

## ✨ Overview

This project provides a professional, automated workflow to render high-resolution panoramic videos from `.dem` files created in Valve's Source Engine games (Half-Life 2, Portal, etc.).

It automates the tedious process of:
1.  Launching the game and rendering 6 separate angles (cubemap faces).
2.  Stitching those angles into a perfect Equirectangular generic projection using FFmpeg.
3.  Producing a YouTube-ready 360° video file.

## 🚀 Features

-   **Automation**: Handles game launching, console commands, and rendering automatically.
-   **High Resolution**: Supports 8K output (e.g., 3840x3840 per face).
-   **Hardware Acceleration**: Uses NVIDIA `hevc_nvenc` for lightning-fast stitching on RTX cards.
-   **Configurable**: Easily managed via `.env` configuration.
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
    ```

> [!WARNING]
> Your `.dem` file must reside inside the game/mod directory (e.g., `hl2/`). The script cannot access files outside the game's sandbox.

## 🎥 Recording Demos

To us this tool, you first need a Source Engine demo file (`.dem`).

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

To start the render process, simply run:

```bash
python main.py
```

### The Process
1.  **Render Phase**: The script will launch the game 6 times (once for each face).
    *   **IMPORTANT**: The automation requires you to **Manually Close the Game Window** after the demo playback has finished for each face. The script will wait until the window is closed to proceed to the next angle.
    *   *Do not interact with the computer while the game window is active*, as keyboard inputs are simulated.
    *   The script uses `sv_cheats 1` and `thirdperson` to lock the camera angle for each face.
2.  **Stitch Phase**: FFmpeg will process the thousands of generated TGA images.
    *   This step uses your GPU (NVENC) for performance.
3.  **Result**: The final video will be saved in the `output/` directory.

## 🔧 Technical Details

The tool works by recording 6 synchronous passes of the same demo file. For each pass, it sets the camera to a specific orthogonal angle:
-   **Front** (0°)
-   **Left** (90°)
-   **Back** (180°)
-   **Right** (270°)
-   **Up** (-90°)
-   **Down** (90°)

It then uses FFmpeg's `v360` filter to reproject these 6 inputs (Cubemap) into a single Equirectangular video stream.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.