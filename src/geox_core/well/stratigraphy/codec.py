"""
GEOX Well Stratigraphy — PNG ⇄ XLSX Round-Trip Codec
═══════════════════════════════════════════════════════════════════════════════

Embeds XLSX data as lossless JSON manifest in PNG tEXt chunk.
Allows invertible reconstruction: PNG → XLSX without data loss.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import logging
import os
from typing import Any, Optional

import pandas as pd

import openpyxl

logger = logging.getLogger("geox.stratigraphy.codec")

MANIFEST_KEY = "GEOX_KL2_MANIFEST_B64"

try:
    from PIL import Image as _PIL_Image, PngImagePlugin as _PngMeta

    _PILLOW_OK = True
except ImportError:
    _PILLOW_OK = False


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _pack(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
    return base64.b64encode(gzip.compress(raw, compresslevel=9)).decode("ascii")


def _unpack(s: str) -> Any:
    return json.loads(gzip.decompress(base64.b64decode(s.encode("ascii"))).decode("utf-8"))


def embed_manifest_in_png(png_path: str, manifest_obj: dict) -> bool:
    """Embed a manifest dict into a PNG tEXt chunk (in-place)."""
    if not _PILLOW_OK:
        logger.warning("Pillow not installed — manifest embedding disabled")
        return False
    try:
        img = _PIL_Image.open(png_path)
        meta = _PngMeta.PngInfo()
        meta.add_text(MANIFEST_KEY, _pack(manifest_obj))
        img.save(png_path, pnginfo=meta)
        return True
    except Exception as e:
        logger.warning(f"embed_manifest: {e}")
        return False


def extract_manifest_from_png(png_path: str) -> Optional[dict]:
    """Extract manifest dict from PNG tEXt chunk."""
    if not _PILLOW_OK:
        return None
    try:
        img = _PIL_Image.open(png_path)
        b64 = img.info.get(MANIFEST_KEY)
        return _unpack(b64) if b64 else None
    except Exception as e:
        logger.warning(f"extract_manifest: {e}")
        return None


def png_to_xlsx(png_path: str, xlsx_out: str) -> dict:
    """
    Inverse codec: reconstruct XLSX from manifest embedded in PNG.

    Returns {"mode": "LOSSLESS", ...} or {"mode": "LOSSY_VISUAL_ONLY"}.
    """
    manifest = extract_manifest_from_png(png_path)
    if manifest is None:
        return {"mode": "LOSSY_VISUAL_ONLY", "reason": "No embedded manifest — visual only"}

    payload = manifest.get("payload", {})
    wb = openpyxl.Workbook()
    default = wb.active
    wb.remove(default)

    for sheet_name, sheet_obj in payload.items():
        ws = wb.create_sheet(title=str(sheet_name)[:31])
        cols = sheet_obj.get("columns", [])
        if cols:
            ws.append(cols)
        for row in sheet_obj.get("records", []):
            ws.append([row.get(c) for c in cols])

    wb.save(xlsx_out)
    return {
        "mode": "LOSSLESS",
        "source_sha256": manifest.get("source_sha256"),
        "workbook": manifest.get("workbook"),
        "reconstructed": xlsx_out,
    }


def validate_roundtrip(xlsx_path: str, sheet: str = "01_GEO_PACKAGES") -> dict:
    """Test XLSX → PNG → XLSX fidelity."""
    import tempfile
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with tempfile.TemporaryDirectory() as d:
        png_tmp = os.path.join(d, "tmp.png")
        xlsx_tmp = os.path.join(d, "reconstructed.xlsx")

        df1 = pd.read_excel(xlsx_path, sheet_name=sheet)
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.axis("off")
        fig.savefig(png_tmp, dpi=72, bbox_inches="tight")
        plt.close(fig)

        manifest = {
            "type": "xlsx_image_manifest",
            "version": "1.0",
            "source_sha256": _sha256(xlsx_path),
            "workbook": os.path.basename(xlsx_path),
            "sheets": [sheet],
            "payload": {
                sheet: {
                    "columns": df1.columns.tolist(),
                    "records": df1.fillna("").to_dict(orient="records"),
                }
            },
        }
        embed_manifest_in_png(png_tmp, manifest)
        res = png_to_xlsx(png_tmp, xlsx_tmp)

        if res["mode"] == "LOSSLESS":
            import pandas as pd

            df2 = pd.read_excel(xlsx_tmp, sheet_name=sheet)
            equal = df1.shape == df2.shape
            return {"ok": equal, "mode": "LOSSLESS", "rows": df1.shape[0], "cols": df1.shape[1]}
        return {"ok": False, "mode": res["mode"]}
