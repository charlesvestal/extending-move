#!/usr/bin/env python3
"""Create a short demo video of the Move web interface.

The script uses pyppeteer to capture screenshots of each major page and then
assembles them into a video with ffmpeg. FFmpeg must be installed on the
system running this script.

Example:
    python record_demo_video.py --base-url http://move.local:909 --output demo.mp4
"""

import argparse
import asyncio
import subprocess
from pathlib import Path
from typing import Sequence, Tuple

from pyppeteer import launch

PAGES: Sequence[Tuple[str, int]] = [
    ("/restore", 2),
    ("/reverse", 2),
    ("/drum-rack-inspector", 2),
    ("/synth-macros", 2),
    ("/midi-upload", 2),
    ("/chord", 2),
]


async def capture_pages(base_url: str, out_dir: Path) -> None:
    """Capture screenshots for each page."""
    browser = await launch(headless=True, args=["--no-sandbox"])
    page = await browser.newPage()
    await page.setViewport({"width": 1280, "height": 720})
    out_dir.mkdir(parents=True, exist_ok=True)
    for path, wait in PAGES:
        await page.goto(base_url + path)
        await asyncio.sleep(wait)
        name = path.strip("/").replace("-", "_") or "index"
        await page.screenshot({"path": str(out_dir / f"{name}.png")})
    await browser.close()


def create_video(img_dir: Path, output: Path) -> None:
    """Combine screenshots into a video using ffmpeg."""
    images = sorted(img_dir.glob("*.png"))
    if not images:
        raise FileNotFoundError("No screenshots found to assemble")
    list_file = img_dir / "images.txt"
    with list_file.open("w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 2\n")
        # repeat last frame so video doesn't end abruptly
        f.write(f"file '{images[-1]}'\n")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-vsync",
        "vfr",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]
    subprocess.run(cmd, check=True)


def main(base_url: str, output: str) -> None:
    screenshots = Path("demo_screens")
    asyncio.get_event_loop().run_until_complete(capture_pages(base_url, screenshots))
    create_video(screenshots, Path(output))
    print(f"Demo video saved to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record a demo video of the Move web interface")
    parser.add_argument("--base-url", default="http://localhost:909", help="Base URL of the running server")
    parser.add_argument("--output", default="demo.mp4", help="Output video file path")
    args = parser.parse_args()
    main(args.base_url, args.output)

