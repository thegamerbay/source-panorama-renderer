import argparse
from src.ffmpeg_worker import FFmpegStitcher
from src.utils import logger, install_player_model
from config import cfg, PANORAMA_FACES

def main():
    parser = argparse.ArgumentParser(description="Source Engine Panorama Renderer")
    parser.add_argument("--stitch-only", action="store_true", help="Skip rendering and only perform stitching")
    args = parser.parse_args()

    logger.info(f"=== Source Panorama Renderer (FOV {cfg.RIG_FOV}) ===")
    logger.info(f"Total Angles to Render: {len(PANORAMA_FACES)}")
    
    if not cfg.GAME_EXE.exists():
        logger.error(f"HL2 Executable not found at: {cfg.GAME_EXE}")
        return

    try:
        stitcher = FFmpegStitcher()
    except Exception as e:
        logger.error(f"Stitcher Init failed: {e}")
        return

    if not args.stitch_only:
        try:
            # Install/Verify player model to prevent player rendering
            install_player_model(cfg.GAME_ROOT, cfg.MOD_DIR)

            if cfg.ENGINE_TYPE == "portal2":
                from src.engine_control_portal2 import EngineController
                logger.info("Loaded Portal 2 Engine Controller")
            else:
                from src.engine_control import EngineController
                logger.info("Loaded HL2 Engine Controller")

            engine = EngineController()
            # 1. Render Phase
            logger.info("Phase 1: Rendering Panorama Faces...")
            sorted_faces = sorted(list(PANORAMA_FACES.keys()))
            for i, face in enumerate(sorted_faces):
                logger.info(f"Progress: {i+1}/{len(sorted_faces)} ({face})")
                engine.render_face(face)
        except Exception as e:
            logger.error(f"Render Phase failed: {e}")
            return
    else:
        logger.info("Skipping Render Phase (--stitch-only active)")

    try:
        # 2. Stitch Phase
        logger.info("Phase 2: Stitching Video...")
        stitcher.stitch()
        
    except KeyboardInterrupt:
        logger.warning("Interrupted.")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
