import cv2
import numpy as np
import pytest

from bot.services.video_analyzer import analyze_video, render_report


def make_video(path, w, h, frames=60, fps=30, black=False, moving=True):
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    rng = np.random.default_rng(1)
    for i in range(frames):
        if black:
            f = np.zeros((h, w, 3), np.uint8)
        elif moving:
            f = rng.integers(0, 255, (h, w, 3), dtype=np.uint8)
        else:
            f = np.full((h, w, 3), 120, np.uint8)
        vw.write(f)
    vw.release()


def test_vertical_good_video(tmp_path):
    p = tmp_path / "a.mp4"
    make_video(p, 720, 1280)
    r = analyze_video(p, "Kino")
    assert (r.width, r.height) == (720, 1280) and r.aspect == "9:16"
    assert r.duration == pytest.approx(2.0, abs=0.3)
    assert r.black_ratio == 0 and r.hook_motion > 2
    assert "Video analiz" in render_report(r, "Kino")


def test_horizontal_black_static_flagged(tmp_path):
    p = tmp_path / "b.mp4"
    make_video(p, 640, 360, black=True)
    r = analyze_video(p, "Kino")
    txt = " ".join(r.problems)
    assert "gorizontal" in txt and "Qora" in txt and r.score < 80


def test_broken_file_raises(tmp_path):
    p = tmp_path / "bad.mp4"
    p.write_bytes(b"not a video")
    with pytest.raises(ValueError):
        analyze_video(p)
