from app.outputs.qr_render import render_qr_png

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_render_qr_png_empty_text_returns_valid_png() -> None:
    data = render_qr_png("")
    assert data.startswith(PNG_SIGNATURE)
    assert len(data) > 100


def test_render_qr_png_with_url_returns_valid_png() -> None:
    data = render_qr_png("https://example.com/item/1")
    assert data.startswith(PNG_SIGNATURE)
    assert data != render_qr_png("")