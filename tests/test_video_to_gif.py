from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "video_to_gif.py"


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg and ffprobe are required")
class VideoToGifTest(unittest.TestCase):
    def test_creates_animated_gif_within_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.mp4"
            output = tmp_path / "clip.gif"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=size=640x360:rate=24",
                    "-t",
                    "2",
                    "-pix_fmt",
                    "yuv420p",
                    str(source),
                ],
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source),
                    str(output),
                    "--duration",
                    "1.5",
                    "--width",
                    "480",
                    "--fps",
                    "8",
                    "--max-bytes",
                    "1000000",
                ],
                check=True,
            )

            self.assertTrue(output.is_file())
            self.assertLessEqual(output.stat().st_size, 1_000_000)
            self.assertEqual(output.read_bytes()[:6], b"GIF89a")
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-count_frames",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=nb_read_frames",
                    "-of",
                    "default=nw=1:nk=1",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertGreater(int(probe.stdout.strip()), 1)


if __name__ == "__main__":
    unittest.main()
