"""Convert a source clip to 1080x1920 9:16 (blurred-background pad).

Same recipe as the manual conversions used for AI World Clips: the frame is
scaled to fill 1080x1920, a blurred copy fills the background, and the full
frame is overlaid centred — nothing is cropped out of the picture itself.
Audio is kept. Output is verified with ffprobe before it is used.
"""
import json
import subprocess


def probe(path):
    r = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", path,
        ],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(r.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if video is None:
        raise RuntimeError(f"No video stream in {path}")
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration": float(data["format"].get("duration", 0) or 0),
        "has_audio": audio is not None,
    }


def convert_to_9x16(src, dst):
    """Convert src to a 1080x1920 MP4 at dst. Returns probe info of the output."""
    info = probe(src)
    filt = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=20[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
    )
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", src,
        "-filter_complex", filt,
        "-map", "[v]",
    ]
    if info["has_audio"]:
        cmd += ["-map", "0:a", "-c:a", "aac", "-b:a", "128k"]
    cmd += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        dst,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {src}:\n{r.stderr[-2000:]}")
    out = probe(dst)
    if (out["width"], out["height"]) != (1080, 1920):
        raise RuntimeError(
            f"Converted file is {out['width']}x{out['height']}, expected 1080x1920"
        )
    return out
