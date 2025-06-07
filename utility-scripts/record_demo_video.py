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
from typing import Callable, Awaitable

from pyppeteer import launch

# Example files used to populate the forms during the demo. If you have your own
# files you would like to showcase simply replace these paths.
EXAMPLE_SET = Path("examples/Sets/808.abl")
EXAMPLE_SAMPLE = Path("examples/Samples/organ.wav")
EXAMPLE_CHORD_SAMPLE = Path("examples/Samples/010 Pizz Str.wav")
EXAMPLE_MIDI = Path("examples/Midi/I Need Your Love.mid")



async def _screenshot(page, out_dir: Path, name: str) -> None:
    """Helper to save a screenshot with a consistent name."""
    await page.screenshot({"path": str(out_dir / f"{name}.png")})


async def demo_restore(page, base_url: str, out_dir: Path) -> None:
    await page.goto(f"{base_url}/restore")
    await page.waitForSelector("input[name=ablbundle]")
    input_el = await page.querySelector("input[name=ablbundle]")
    await input_el.uploadFile(str(EXAMPLE_SET))
    # select the first pad
    await page.waitForSelector("label.pad-cell")
    await page.click("label.pad-cell")
    await asyncio.sleep(1)
    await _screenshot(page, out_dir, "restore")


async def demo_reverse(page, base_url: str, out_dir: Path) -> None:
    await page.goto(f"{base_url}/reverse")
    await page.waitForSelector(".file-entry button")
    await asyncio.gather(page.waitForNavigation(), page.click(".file-entry button"))
    await page.waitForSelector("form[method='post'] button")
    await asyncio.sleep(1)
    await _screenshot(page, out_dir, "reverse")


async def demo_drum_rack(page, base_url: str, out_dir: Path) -> None:
    await page.goto(f"{base_url}/drum-rack-inspector")
    await page.waitForSelector(".file-entry button")
    await asyncio.gather(page.waitForNavigation(), page.click(".file-entry button"))
    await page.waitForSelector(".drum-grid")
    await asyncio.sleep(1)
    await _screenshot(page, out_dir, "drum_rack_inspector")


async def demo_synth_macros(page, base_url: str, out_dir: Path) -> None:
    await page.goto(f"{base_url}/synth-macros")
    await page.waitForSelector(".file-entry button")
    await asyncio.gather(page.waitForNavigation(), page.click(".file-entry button"))
    await page.waitForSelector(".macro-display")
    await asyncio.sleep(1)
    await _screenshot(page, out_dir, "synth_macros")


async def demo_midi_upload(page, base_url: str, out_dir: Path) -> None:
    await page.goto(f"{base_url}/midi-upload")
    await page.waitForSelector("input#midi_file")
    input_el = await page.querySelector("input#midi_file")
    await input_el.uploadFile(str(EXAMPLE_MIDI))
    await page.type("#set_name", "Demo Set")
    # select a pad
    await page.waitForSelector("label.pad-cell")
    await page.click("label.pad-cell")
    await asyncio.sleep(1)
    await _screenshot(page, out_dir, "midi_upload")


async def demo_chord(page, base_url: str, out_dir: Path) -> None:
    await page.goto(f"{base_url}/chord")
    await page.waitForSelector("#wavFileInput")
    input_el = await page.querySelector("#wavFileInput")
    await input_el.uploadFile(str(EXAMPLE_CHORD_SAMPLE))
    await page.evaluate("document.getElementById('wavFileInput').dispatchEvent(new Event('change'))")
    await asyncio.sleep(2)
    await _screenshot(page, out_dir, "chord")


async def demo_slice(page, base_url: str, out_dir: Path) -> None:
    await page.goto(f"{base_url}/slice")
    await page.waitForSelector("input#file")
    input_el = await page.querySelector("input#file")
    await input_el.uploadFile(str(EXAMPLE_SAMPLE))
    await page.evaluate("document.getElementById('file').dispatchEvent(new Event('change'))")
    await asyncio.sleep(2)
    await _screenshot(page, out_dir, "slice")


async def capture_pages(base_url: str, out_dir: Path) -> None:
    """Capture screenshots for each main page with example data loaded."""
    browser = await launch(headless=True, args=["--no-sandbox"])
    out_dir.mkdir(parents=True, exist_ok=True)

    steps: list[Callable[[any, str, Path], Awaitable[None]]] = [
        demo_restore,
        demo_reverse,
        demo_drum_rack,
        demo_synth_macros,
        demo_midi_upload,
        demo_chord,
        demo_slice,
    ]

    for step in steps:
        page = await browser.newPage()
        await page.setViewport({"width": 1280, "height": 720})
        try:
            await step(page, base_url, out_dir)
        except Exception as e:  # noqa: BLE001
            print(f"Warning: step {step.__name__} failed: {e}")
        finally:
            if not page.isClosed():
                try:
                    await page.close()
                except Exception:  # noqa: BLE001
                    pass

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
    asyncio.run(capture_pages(base_url, screenshots))
    create_video(screenshots, Path(output))
    print(f"Demo video saved to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record a demo video of the Move web interface")
    parser.add_argument("--base-url", default="http://localhost:909", help="Base URL of the running server")
    parser.add_argument("--output", default="demo.mp4", help="Output video file path")
    args = parser.parse_args()
    main(args.base_url, args.output)

