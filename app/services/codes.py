from pathlib import Path
import os
import qrcode
import barcode
from barcode.writer import ImageWriter

BASE_DIR = Path(__file__).resolve().parents[2]
OUT = BASE_DIR / "static" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

def get_public_pass_url(code: str) -> str:
    base = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    return f"{base}/pass/view/{code}"

def generate_codes(code: str):
    payload = get_public_pass_url(code)
    qrcode.make(payload).save(OUT / f"{code}_qr.png")
    Code128 = barcode.get_barcode_class("code128")
    Code128(payload, writer=ImageWriter()).save(str(OUT / f"{code}_barcode"))
