from financial_os.schemas.common import detect_mime_from_magic


def test_detects_heic_from_iso_base_media_brand() -> None:
    synthetic_header = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 12
    assert detect_mime_from_magic(synthetic_header) == "image/heic"


def test_detects_heif_compatible_brand_as_heic_family() -> None:
    synthetic_header = b"\x00\x00\x00\x18ftypmif1" + b"\x00" * 12
    assert detect_mime_from_magic(synthetic_header) == "image/heic"
