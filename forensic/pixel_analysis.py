import math
from typing import Dict, Any, List
import numpy as np
from PIL import Image


def calculate_entropy(histogram_counts: np.ndarray, total_pixels: int) -> float:
    """Calculate Shannon entropy (bits per pixel) from a 256-bin histogram."""
    if total_pixels <= 0:
        return 0.0
    probabilities = histogram_counts / total_pixels
    probabilities = probabilities[probabilities > 0]
    return float(-np.sum(probabilities * np.log2(probabilities)))


def analyze_pixels(img: Image.Image) -> Dict[str, Any]:
    """Compute channel histograms, dynamic range, clipping, and Shannon entropy using NumPy.
    
    Handles RGB, RGBA, Grayscale, and indexed modes accurately.
    Returns JSON-serializable numbers for HTML5 Canvas rendering.
    """
    mode = img.mode
    width, height = img.size
    total_pixels = width * height

    # Normalize image to RGB or Grayscale for standard radiometric analysis
    if mode in ("RGBA", "RGBa"):
        work_img = img.convert("RGBA")
        arr = np.asarray(work_img, dtype=np.uint8)
        has_alpha = True
    elif mode in ("L", "1"):
        work_img = img.convert("L")
        arr = np.asarray(work_img, dtype=np.uint8)
        has_alpha = False
    else:
        work_img = img.convert("RGB")
        arr = np.asarray(work_img, dtype=np.uint8)
        has_alpha = False

    histograms: Dict[str, List[int]] = {}
    channel_stats: Dict[str, Dict[str, float]] = {}

    if mode in ("L", "1"):
        # Grayscale single channel
        counts, _ = np.histogram(arr, bins=256, range=(0, 256))
        histograms["luminance"] = counts.tolist()
        histograms["red"] = counts.tolist()
        histograms["green"] = counts.tolist()
        histograms["blue"] = counts.tolist()

        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))
        min_val = int(np.min(arr))
        max_val = int(np.max(arr))
        shadow_clip = float(np.mean(arr <= 1) * 100.0)
        highlight_clip = float(np.mean(arr >= 254) * 100.0)
        entropy = calculate_entropy(counts, total_pixels)

        lum_stats = {
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "min": min_val,
            "max": max_val,
            "shadow_clipping_pct": round(shadow_clip, 2),
            "highlight_clipping_pct": round(highlight_clip, 2),
            "entropy_bits": round(entropy, 3),
        }
        channel_stats["luminance"] = lum_stats
        channel_stats["red"] = lum_stats
        channel_stats["green"] = lum_stats
        channel_stats["blue"] = lum_stats
    else:
        # Multi-channel color image
        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]

        r_counts, _ = np.histogram(r, bins=256, range=(0, 256))
        g_counts, _ = np.histogram(g, bins=256, range=(0, 256))
        b_counts, _ = np.histogram(b, bins=256, range=(0, 256))

        # ITU-R BT.601 standard luma weights
        luma = (0.299 * r.astype(np.float32) + 0.587 * g.astype(np.float32) + 0.114 * b.astype(np.float32)).clip(0, 255).astype(np.uint8)
        luma_counts, _ = np.histogram(luma, bins=256, range=(0, 256))

        histograms["red"] = r_counts.tolist()
        histograms["green"] = g_counts.tolist()
        histograms["blue"] = b_counts.tolist()
        histograms["luminance"] = luma_counts.tolist()

        channels_data = [("red", r), ("green", g), ("blue", b), ("luminance", luma)]
        if has_alpha and arr.shape[2] >= 4:
            a = arr[:, :, 3]
            a_counts, _ = np.histogram(a, bins=256, range=(0, 256))
            histograms["alpha"] = a_counts.tolist()
            channels_data.append(("alpha", a))

        for ch_name, ch_arr in channels_data:
            ch_mean = float(np.mean(ch_arr))
            ch_std = float(np.std(ch_arr))
            ch_min = int(np.min(ch_arr))
            ch_max = int(np.max(ch_arr))
            ch_shadow = float(np.mean(ch_arr <= 1) * 100.0)
            ch_highlight = float(np.mean(ch_arr >= 254) * 100.0)
            ch_entropy = calculate_entropy(
                np.array(histograms[ch_name]),
                total_pixels
            )

            channel_stats[ch_name] = {
                "mean": round(ch_mean, 2),
                "std": round(ch_std, 2),
                "min": ch_min,
                "max": ch_max,
                "shadow_clipping_pct": round(ch_shadow, 2),
                "highlight_clipping_pct": round(ch_highlight, 2),
                "entropy_bits": round(ch_entropy, 3),
            }

    # Summary radiometric metrics
    lum_stat = channel_stats.get("luminance", {})
    summary = {
        "total_pixels": total_pixels,
        "mode_analyzed": "Grayscale" if mode in ("L", "1") else ("RGBA" if has_alpha else "RGB"),
        "average_luminance": lum_stat.get("mean", 0.0),
        "luminance_std_dev": lum_stat.get("std", 0.0),
        "shadow_clipping_pct": lum_stat.get("shadow_clipping_pct", 0.0),
        "highlight_clipping_pct": lum_stat.get("highlight_clipping_pct", 0.0),
        "shannon_entropy_bits": lum_stat.get("entropy_bits", 0.0),
    }

    return {
        "histograms": histograms,
        "channel_statistics": channel_stats,
        "summary": summary,
        "forensic_context": (
            "Histograms display the radiometric distribution of pixel intensities across 256 levels. "
            "Unusual peaks, combs (spaced gaps caused by histogram stretching), or severe clipping at 0 or 255 "
            "provide clues regarding exposure levels, tonal adjustments, and dynamic range compression."
        ),
    }
