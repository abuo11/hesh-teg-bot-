from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoReport:
    duration: float = 0.0
    size_mb: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    has_audio: bool | None = None
    aspect: str = ""
    black_ratio: float = 0.0
    hook_motion: float = 0.0
    cuts_per_10s: float = 0.0
    text_hint: bool = False
    watermark_hint: bool = False
    problems: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    hook_score: int = 0
    score: int = 0


def _probe(path: Path) -> dict:
    """ffprobe bo'lsa undan, bo'lmasa None qaytaradi."""
    if not shutil.which("ffprobe"):
        return {}
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout
        return json.loads(out)
    except Exception:
        return {}


def _ratio(w: int, h: int) -> str:
    if not w or not h:
        return "—"
    from math import gcd
    g = gcd(w, h)
    return f"{w // g}:{h // g}"


def analyze_video(path: str | Path, direction: str = "") -> VideoReport:
    import cv2
    import numpy as np

    path = Path(path)
    r = VideoReport(size_mb=round(path.stat().st_size / 1048576, 2))
    info = _probe(path)
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and not r.width:
            r.width, r.height = int(s.get("width", 0)), int(s.get("height", 0))
            try:
                a, b = s.get("avg_frame_rate", "0/1").split("/")
                r.fps = round(float(a) / float(b), 2) if float(b) else 0.0
            except Exception:
                pass
        if s.get("codec_type") == "audio":
            r.has_audio = True
    if info:
        r.has_audio = bool(r.has_audio)
        try:
            r.duration = float(info["format"].get("duration", 0))
        except Exception:
            pass

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("Videoni ochib bo‘lmadi (format qo‘llab-quvvatlanmaydi yoki buzilgan).")
    r.width = r.width or int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    r.height = r.height or int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    r.fps = r.fps or round(cap.get(cv2.CAP_PROP_FPS) or 0.0, 2)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    r.duration = r.duration or (total / r.fps if r.fps else 0.0)
    r.aspect = _ratio(r.width, r.height)

    step_s = max(0.25, r.duration / 120) if r.duration else 0.5
    frames, times = [], []
    t = 0.0
    while t < max(r.duration, 0.5) and len(frames) < 130:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok:
            break
        frames.append(cv2.resize(fr, (160, 284)))
        times.append(t)
        t += step_s
    cap.release()
    if len(frames) < 2:
        raise ValueError("Videodan yetarli kadr o‘qib bo‘lmadi.")

    gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    bright = np.array([g.mean() for g in gray])
    r.black_ratio = float((bright < 14).mean())
    diffs = np.array([np.abs(gray[i].astype(int) - gray[i - 1].astype(int)).mean() for i in range(1, len(gray))])
    dt = np.array(times[1:])
    r.hook_motion = float(diffs[dt <= 3].mean()) if (dt <= 3).any() else float(diffs.mean())
    cuts = int((diffs > 28).sum())
    r.cuts_per_10s = round(cuts / max(r.duration, 1) * 10, 1)

    edges = [cv2.Canny(g, 80, 160) for g in gray[:: max(1, len(gray) // 12)]]
    h = edges[0].shape[0]
    band = np.mean([(e[int(h * .65):int(h * .85)] > 0).mean() for e in edges])
    r.text_hint = bool(band > 0.06)
    stack = np.stack(gray)
    corners = [stack[:, :36, :48], stack[:, :36, -48:], stack[:, -36:, :48], stack[:, -36:, -48:]]
    r.watermark_hint = any(c.std(axis=0).mean() < 4 and (cv2.Canny(c[0], 80, 160) > 0).mean() > 0.08
                           for c in corners)

    # --- baholash (evristik) ---
    score, hook = 100, 100
    if r.height and r.width and r.height < r.width:
        r.problems.append("Video gorizontal. Reels uchun 9:16 (vertikal) format tavsiya etiladi.")
        r.tips.append("Videoni 1080x1920 (9:16) ga moslang.")
        score -= 15
    if min(r.width, r.height) < 720:
        r.problems.append(f"Rezolyutsiya past ({r.width}x{r.height}).")
        r.tips.append("Kamida 720x1280, yaxshisi 1080x1920 da eksport qiling.")
        score -= 12
    if r.fps and r.fps < 24:
        r.problems.append(f"FPS past ({r.fps}).")
        score -= 8
    if r.has_audio is False:
        r.problems.append("Videoda audio yo‘q.")
        r.tips.append("Musiqa yoki ovoz qo‘shing.")
        score -= 10
    if r.duration > 90:
        r.problems.append("Davomiylik 90 soniyadan oshiq.")
        score -= 6
    if r.duration < 3:
        r.problems.append("Video juda qisqa.")
        score -= 6
    if r.black_ratio > 0.08:
        r.problems.append(f"Qora/bo‘sh kadrlar ulushi yuqori ({r.black_ratio:.0%}).")
        r.tips.append("Boshi va oxiridagi qora qismlarni kesib tashlang.")
        score -= 10
    if r.hook_motion < 2.0:
        r.problems.append("Dastlabki 3 soniyada harakat/o‘zgarish kam — hook sust bo‘lishi mumkin.")
        r.tips.append("Birinchi soniyada qiziqarli kadr yoki savol bilan boshlang.")
        hook -= 35
    if not r.text_hint:
        r.tips.append("Boshiga qisqa matn (hook sarlavha) qo‘shish e’tiborni oshirishi mumkin.")
        hook -= 10
    if r.cuts_per_10s < 1 and r.duration > 8:
        r.problems.append("Montaj tempi sekin (kesishlar kam).")
        r.tips.append("Har 2–4 soniyada kadr yoki rakursni almashtiring.")
        score -= 6
    if r.watermark_hint:
        r.problems.append("Burchakda suv belgisi bo‘lishi mumkin (taxminiy aniqlash).")
        score -= 5
    r.hook_score = max(0, min(100, hook))
    r.score = max(0, min(100, int(score * 0.8 + r.hook_score * 0.2)))
    return r


def render_report(r: VideoReport, direction: str) -> str:
    mark = "✅" if r.score >= 75 else "⚠️" if r.score >= 50 else "❌"
    audio = {True: "bor", False: "yo‘q", None: "tekshirilmadi (ffprobe yo‘q)"}[r.has_audio]
    lines = [
        f"🎬 <b>Video analiz</b> — {direction}",
        "",
        f"{mark} <b>Umumiy texnik baho:</b> {r.score}/100",
        f"🪝 <b>Hook bahosi:</b> {r.hook_score}/100",
        "",
        f"📐 Format: {r.width}x{r.height} ({r.aspect}), {r.fps} FPS",
        f"⏱ Davomiylik: {r.duration:.1f} s · 💾 {r.size_mb} MB",
        f"🔊 Audio: {audio}",
        f"🖤 Qora kadrlar: {r.black_ratio:.0%} · ✂️ Kesishlar: {r.cuts_per_10s}/10 s",
        f"🔤 Matn: {'ehtimol bor' if r.text_hint else 'aniqlanmadi'} · "
        f"💧 Suv belgisi: {'ehtimol bor' if r.watermark_hint else 'aniqlanmadi'}",
    ]
    if r.problems:
        lines += ["", "<b>Aniqlangan kamchiliklar:</b>"] + [f"• {p}" for p in r.problems]
    if r.tips:
        lines += ["", "<b>Tavsiyalar:</b>"] + [f"• {t}" for t in r.tips]
    lines += ["", "<i>Bu baho evristik taxmin. Instagram algoritmining ichki ishlashi noma’lum va "
                  "rekka chiqish ehtimoli kafolatlanmaydi.</i>"]
    return "\n".join(lines)
