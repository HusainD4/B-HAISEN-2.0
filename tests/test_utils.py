"""
Unit Tests: Utils — Formatters & Generators
Tests pure functions, tidak memerlukan DB atau HTTP client.
"""
import time
import pytest

from src.utils.formatters import (
    format_rupiah,
    format_rupiah_decimal,
    format_date_id,
    format_phone_wa,
    slugify,
    truncate_text,
    mask_email,
    mask_phone,
    sanitize_filename,
)
from src.utils.generators import (
    generate_uuid,
    generate_order_code,
    generate_otp,
    generate_secure_token,
    generate_upload_filename,
    generate_signed_download_url,
    verify_signed_download_url,
    generate_invoice_number,
    generate_payment_reference,
)


# ── Formatters ────────────────────────────────────────────────────────────────

class TestFormatRupiah:
    def test_integer(self):
        assert format_rupiah(150000) == "Rp 150.000"

    def test_float(self):
        assert format_rupiah(75500.0) == "Rp 75.500"

    def test_zero(self):
        assert format_rupiah(0) == "Rp 0"

    def test_without_prefix(self):
        assert format_rupiah(10000, with_prefix=False) == "10.000"

    def test_none_returns_zero(self):
        assert format_rupiah(None) == "Rp 0"

    def test_decimal(self):
        result = format_rupiah_decimal(150000.50)
        assert "150.000" in result
        assert ",50" in result


class TestFormatDateId:
    def test_basic_date(self):
        from datetime import datetime
        dt = datetime(2024, 5, 1)
        result = format_date_id(dt, long_format=False)
        assert "1 Mei 2024" in result

    def test_long_format_includes_day(self):
        from datetime import datetime
        dt = datetime(2024, 5, 1)  # Rabu
        result = format_date_id(dt, long_format=True)
        assert "Rabu" in result

    def test_show_time(self):
        from datetime import datetime
        dt = datetime(2024, 5, 1, 14, 30)
        result = format_date_id(dt, show_time=True)
        assert "14:30" in result

    def test_iso_string_input(self):
        result = format_date_id("2024-05-01T00:00:00")
        assert "Mei" in result


class TestFormatPhoneWa:
    def test_local_format(self):
        assert format_phone_wa("08123456789") == "628123456789"

    def test_plus_format(self):
        assert format_phone_wa("+628123456789") == "628123456789"

    def test_already_62(self):
        assert format_phone_wa("628123456789") == "628123456789"


class TestSlugify:
    def test_basic(self):
        assert slugify("Produk Terbaru 2024") == "produk-terbaru-2024"

    def test_special_chars(self):
        result = slugify("Kaos & Celana (Sale!)")
        assert " " not in result
        assert "&" not in result

    def test_multiple_spaces(self):
        assert "--" not in slugify("  double  space  ")


class TestTruncateText:
    def test_short_text_unchanged(self):
        assert truncate_text("Pendek", 100) == "Pendek"

    def test_long_text_truncated(self):
        result = truncate_text("A" * 200, 50)
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")


class TestMasking:
    def test_mask_email(self):
        result = mask_email("johndoe@gmail.com")
        assert result.startswith("jo")
        assert "@gmail.com" in result
        assert "johndoe" not in result

    def test_mask_phone(self):
        result = mask_phone("628123456789")
        assert result.startswith("6281")
        assert result.endswith("6789")
        assert "*" in result

    def test_sanitize_filename(self):
        result = sanitize_filename("my file (1).exe")
        assert " " not in result
        assert "(" not in result


# ── Generators ────────────────────────────────────────────────────────────────

class TestGenerators:
    def test_uuid_format(self):
        uid = generate_uuid()
        assert len(uid) == 32  # hex tanpa tanda hubung
        assert uid.isalnum()

    def test_uuid_unique(self):
        assert generate_uuid() != generate_uuid()

    def test_order_code_format(self):
        code = generate_order_code()
        parts = code.split("-")
        assert len(parts) == 3
        assert parts[0] == "HSO"
        assert len(parts[1]) == 8   # YYYYMMDD
        assert len(parts[2]) == 6   # Random

    def test_order_code_custom_prefix(self):
        code = generate_order_code(prefix="TST")
        assert code.startswith("TST-")

    def test_order_code_unique(self):
        codes = {generate_order_code() for _ in range(20)}
        assert len(codes) == 20

    def test_otp_length(self):
        otp = generate_otp(6)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_otp_custom_length(self):
        assert len(generate_otp(4)) == 4

    def test_secure_token_length(self):
        token = generate_secure_token(32)
        assert len(token) >= 40  # URL-safe base64 lebih panjang dari byte count

    def test_upload_filename_format(self):
        name = generate_upload_filename("my product.jpg", folder="products")
        assert name.startswith("products/")
        assert "my_product.jpg" in name
        assert len(name.split("/")[1].split("_")) >= 3

    def test_invoice_number_format(self):
        inv = generate_invoice_number()
        assert inv.startswith("INV/")
        parts = inv.split("/")
        assert len(parts) == 4

    def test_payment_reference_format(self):
        ref = generate_payment_reference("HSO-20241001-A3BX9Z")
        assert ref.startswith("PAY-HSO-")


class TestSignedDownloadUrl:
    SECRET = "test-secret-key-ultra-secure"

    def test_generate_and_verify_valid(self):
        url, expires_at = generate_signed_download_url(
            base_url="https://api.haisen.com/download",
            file_path="digital/product.zip",
            secret_key=self.SECRET,
            expires_in_hours=24,
        )
        assert "file=" in url
        assert "expires=" in url
        assert "sig=" in url

        # Parse params dan verifikasi
        from urllib.parse import urlparse, parse_qs
        params = parse_qs(urlparse(url).query)
        file_path = params["file"][0]
        expires_ts = int(params["expires"][0])
        signature  = params["sig"][0]

        assert verify_signed_download_url(file_path, expires_ts, signature, self.SECRET)

    def test_verify_expired_url_fails(self):
        """URL dengan expires di masa lalu harus gagal verifikasi."""
        expired_ts = int(time.time()) - 3600  # 1 jam lalu
        # Signature valid tapi sudah expired
        import hashlib, hmac as hmac_mod
        payload = f"test/file.zip:{expired_ts}"
        sig = hmac_mod.new(self.SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        assert not verify_signed_download_url("test/file.zip", expired_ts, sig, self.SECRET)

    def test_verify_tampered_signature_fails(self):
        """Signature yang dimodifikasi harus gagal verifikasi."""
        expires_ts = int(time.time()) + 3600
        assert not verify_signed_download_url(
            "test/file.zip", expires_ts, "signature-palsu-dimanipulasi", self.SECRET
        )
