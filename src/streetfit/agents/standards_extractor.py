"""Extract carriageway/lane width values from pages of a design manual, including values printed in drawings.

Why: design manuals put the numbers that matter in cross-section drawings, which are often raster images with
no text layer (the Lisbon manual's two-way profile, p. 152, is one). Text extraction alone misses them.

Three independent readings per page:
  1. the PDF text layer (pypdf),
  2. OCR of the rendered page (Tesseract, if installed),
  3. a vision reading by Claude of the page (as PDF and as a high-resolution image), returning structured values.
Each value from (3) is then checked against (1) and (2): ``text_layer``, ``ocr`` or ``vision_only``. Sums the
model derives are re-computed. Nothing is written to the standards catalogue: the output is a review file with
the rendered page images, for a human to confirm before adding an entry.
"""

from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..textmatch import value_in_text
from .common import check_stop, client, report_usage, request_kwargs


class WidthValue(BaseModel):
    value_m: float
    printed: str = Field(description="The value exactly as printed on the page, e.g. '3.00 m' or '2,75 m'")
    measures: str = Field(description="What the value measures, e.g. 'traffic lane', 'parking strip', 'extra width (sobrelargura)'")
    applies_to: str = Field(description="Street type the value is for, as the page states it")
    conditions: str = Field(description="Conditions or scope stated on the page (traffic volume, buses, exceptions); empty if none")
    location: Literal["text", "drawing", "table", "caption"]
    page_quote: str = Field(description="The sentence or label around the value, copied from the page")


class DerivedTotal(BaseModel):
    label: str = Field(description="What the total is, e.g. 'carriageway between the parking strips'")
    components_m: list[float]
    total_m: float


class PageReading(BaseModel):
    page_title: str
    values: list[WidthValue]
    totals: list[DerivedTotal]


PROMPT = """This is one page of a street design manual. List every width value in metres that concerns the street
cross-section (traffic lanes, carriageway, parking strips, extra widths, bus lanes, cycle lanes, sidewalks),
including values printed inside drawings and dimension lines. Copy each value exactly as printed. State what it
measures, the street type it applies to and any condition the page attaches to it (traffic volume, presence of
buses, exceptions). If a drawing gives components across the carriageway between the parking strips, add a
total with its components. Do not add values that are not on this page."""


def page_pdf_bytes(pdf: Path, page: int) -> bytes:
    from pypdf import PdfReader, PdfWriter

    w = PdfWriter()
    w.add_page(PdfReader(pdf).pages[page - 1])
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def render_png(pdf: Path, page: int, scale: float = 3.0) -> bytes:
    import pypdfium2 as pdfium

    img = pdfium.PdfDocument(str(pdf))[page - 1].render(scale=scale).to_pil()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def text_layer(pdf: Path, page: int) -> str:
    from pypdf import PdfReader

    return PdfReader(pdf).pages[page - 1].extract_text() or ""


# Dimension labels in drawings are small and often rotated: OCR an 8x render, upright and turned 90 degrees, in
# two sparse-text modes, and pool the text. On the Lisbon manual's p. 152 this recovers 3.00 m that a single
# 3x pass misses (0.40 m still needs a human look).
OCR_PASSES = [(0, "11"), (0, "12"), (90, "11"), (90, "12")]


def ocr(pdf: Path, page: int, scale: float = 8.0) -> str | None:
    """Pooled Tesseract OCR of a page. None if Tesseract is not installed."""
    exe = shutil.which("tesseract")
    if not exe:
        return None
    from PIL import Image

    img = Image.open(io.BytesIO(render_png(pdf, page, scale=scale))).convert("L")
    texts = []
    for rot, psm in OCR_PASSES:
        with tempfile.NamedTemporaryFile(suffix=".png") as f:
            img.rotate(rot, expand=True).save(f.name)
            texts.append(subprocess.run([exe, f.name, "stdout", "--psm", psm], capture_output=True, text=True, timeout=900).stdout)
    return "\n".join(texts)


def as_jpeg(png: bytes, quality: int = 88) -> bytes:
    """A compact copy for the API (lossless PNG stays on disk for OCR and human review)."""
    from PIL import Image

    buf = io.BytesIO()
    Image.open(io.BytesIO(png)).convert("RGB").save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def read_page(pdf: Path, page: int, png: bytes) -> tuple[PageReading, object]:
    b64 = lambda b: base64.standard_b64encode(b).decode()  # noqa: E731
    msg = client().beta.messages.parse(
        **request_kwargs(),
        output_format=PageReading,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": b64(page_pdf_bytes(pdf, page))},
                    },
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(as_jpeg(png))}},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )
    check_stop(msg)
    return msg.parsed_output, msg


def check(reading: PageReading, text: str, ocr_text: str | None) -> dict:
    vals = []
    for v in reading.values:
        status = (
            "text_layer"
            if value_in_text(v.value_m, text)
            else ("ocr" if ocr_text and value_in_text(v.value_m, ocr_text) else "vision_only")
        )
        vals.append(v.model_dump() | {"verified_by": status})
    totals = []
    for t in reading.totals:
        ok = abs(sum(t.components_m) - t.total_m) < 0.005
        comp = [
            ("text_layer" if value_in_text(c, text) else "ocr" if ocr_text and value_in_text(c, ocr_text) else "vision_only")
            for c in t.components_m
        ]
        totals.append(t.model_dump() | {"sum_checks": ok, "components_verified_by": comp})
    return {"page_title": reading.page_title, "values": vals, "totals": totals}


def main(pdf: Path, pages: list[int], out: Path | None) -> int:
    out_dir = (out.parent if out else Path.cwd()) / f"{pdf.stem}_review"
    out_dir.mkdir(parents=True, exist_ok=True)
    results, msgs = {}, []
    for p in pages:
        png = render_png(pdf, p)
        (out_dir / f"page_{p}.png").write_bytes(png)
        text, ocr_text = text_layer(pdf, p), ocr(pdf, p)
        reading, msg = read_page(pdf, p, png)
        msgs.append(msg)
        results[p] = check(reading, text, ocr_text) | {"ocr_available": ocr_text is not None, "image": f"page_{p}.png"}
        n = {s: sum(v["verified_by"] == s for v in results[p]["values"]) for s in ("text_layer", "ocr", "vision_only")}
        print(
            f"page {p}: {len(reading.values)} values ({n}); totals: "
            + ", ".join(f"{t['label']} = {t['total_m']} m (sum {'ok' if t['sum_checks'] else 'WRONG'})" for t in results[p]["totals"])
        )
    report_usage(msgs)
    dest = out or out_dir / "extraction.json"
    dest.write_text(json.dumps({"pdf": str(pdf), "pages": results}, ensure_ascii=False, indent=2) + "\n")
    print(f"review file: {dest}  (values marked vision_only need a human look at the page image)")
    return 0
