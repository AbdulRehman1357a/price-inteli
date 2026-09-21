from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

_ERROR_CORRECTION = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def render_qr_png(
    text: str,
    *,
    box_size: int = 6,
    border: int = 1,
    error_correction: str = "M",
) -> bytes:
    """Generate a QR code for *text* as PNG bytes.

    Shared by the QR output adapter (app/outputs/qr_code.py) and the PDF
    label adapter (app/outputs/pdf_label.py) so both embed the exact same
    style of code. text is always treated as a string; empty string produces
    a valid (blank) QR.
    """
    qr = qrcode.QRCode(
        box_size=box_size,
        border=border,
        error_correction=_ERROR_CORRECTION.get(error_correction, ERROR_CORRECT_M),
    )
    qr.add_data(text or "")
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()