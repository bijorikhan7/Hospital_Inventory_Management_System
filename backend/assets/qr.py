from io import BytesIO

import qrcode
from django.http import HttpResponse


def build_qr_png(payload: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def qr_png_response(payload: str, filename: str) -> HttpResponse:
    response = HttpResponse(build_qr_png(payload), content_type="image/png")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
