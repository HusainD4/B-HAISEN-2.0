"""
Modul: Generators Helper
Fungsi utilitas untuk menghasilkan string unik:
kode pesanan, token, slug, OTP, signed download URL, dsb.
"""
import hashlib
import hmac
import secrets
import string
import time
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode


# ============================================================
# ID & TOKEN GENERATORS
# ============================================================

def generate_uuid() -> str:
    """Generate UUID4 sebagai string tanpa tanda hubung."""
    return uuid.uuid4().hex


def generate_order_code(prefix: str = "HSO") -> str:
    """
    Generate kode pesanan unik.
    Format: HSO-YYYYMMDD-XXXXXX (6 karakter random huruf besar + angka).
    Contoh: HSO-20241001-A3BX9Z
    """
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
    )
    return f"{prefix}-{date_part}-{random_part}"


def generate_otp(length: int = 6) -> str:
    """
    Generate OTP numerik (One-Time Password).
    Default 6 digit. Digunakan untuk verifikasi email/phone.
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))


def generate_secure_token(length: int = 32) -> str:
    """
    Generate token URL-safe untuk reset password, verifikasi email, dsb.
    Default 32 byte -> 64 karakter hex.
    """
    return secrets.token_urlsafe(length)


def generate_api_key(prefix: str = "hso") -> str:
    """
    Generate API Key dengan prefix.
    Format: hso_<64-char-hex>
    Contoh: hso_3f8a9b2c...
    """
    return f"{prefix}_{secrets.token_hex(32)}"


# ============================================================
# SLUG & FILENAME GENERATORS
# ============================================================

def generate_unique_slug(base_slug: str) -> str:
    """
    Tambahkan suffix random ke slug agar unik.
    Contoh: "kaos-polos" -> "kaos-polos-a3b9"
    """
    suffix = secrets.token_hex(2)  # 4 karakter hex
    return f"{base_slug}-{suffix}"


def generate_upload_filename(original_filename: str, folder: str = "") -> str:
    """
    Generate nama file unik untuk upload ke bucket.
    Format: {folder}/{timestamp}_{uuid4hex}_{original_name_sanitized}
    Contoh: products/20241001_143022_a3b9c2d1_kaos-polos.jpg

    Args:
        original_filename: Nama file asli dari client.
        folder: Subfolder di dalam bucket (e.g., "products", "banners").

    Returns:
        Path unik untuk disimpan di bucket.
    """
    import re
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    # Sanitasi nama file: hapus karakter berbahaya
    safe_name = re.sub(r"[^\w.\-]", "_", original_filename).lower()
    filename   = f"{timestamp}_{unique_id}_{safe_name}"
    return f"{folder}/{filename}" if folder else filename


# ============================================================
# SIGNED URL GENERATOR (untuk download produk digital)
# ============================================================

def generate_signed_download_url(
    base_url: str,
    file_path: str,
    secret_key: str,
    expires_in_hours: int = 24,
) -> tuple[str, str]:
    """
    Generate URL berttanda tangan (HMAC-SHA256) untuk download produk digital.
    URL hanya valid selama `expires_in_hours` jam.

    Args:
        base_url: URL dasar endpoint download (e.g., "https://store.haisen.my.id/download").
        file_path: Path relatif file di bucket.
        secret_key: Kunci rahasia dari settings.SECRET_KEY.
        expires_in_hours: Durasi validitas URL.

    Returns:
        Tuple (signed_url: str, expires_at_iso: str)
    """
    expires_ts = int(time.time()) + (expires_in_hours * 3600)
    expires_at = datetime.utcfromtimestamp(expires_ts).strftime("%Y-%m-%d %H:%M UTC")

    # Buat signature dari file_path + expires
    payload   = f"{file_path}:{expires_ts}"
    signature = hmac.new(
        secret_key.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()

    params = urlencode({"file": file_path, "expires": expires_ts, "sig": signature})
    signed_url = f"{base_url}?{params}"
    return signed_url, expires_at


def verify_signed_download_url(
    file_path: str,
    expires_ts: int,
    signature: str,
    secret_key: str,
) -> bool:
    """
    Verifikasi tanda tangan URL download.
    Returns True jika valid dan belum kedaluwarsa.
    """
    if int(time.time()) > expires_ts:
        return False  # URL kedaluwarsa
    payload          = f"{file_path}:{expires_ts}"
    expected_sig     = hmac.new(
        secret_key.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature)


# ============================================================
# PAYMENT REFERENCE GENERATORS
# ============================================================

def generate_payment_reference(order_code: str) -> str:
    """
    Generate referensi unik untuk transaksi pembayaran.
    Format: PAY-{order_code}-{4-char-random}
    Contoh: PAY-HSO-20241001-A3BX9Z-C7D2
    """
    suffix = secrets.token_hex(2).upper()
    return f"PAY-{order_code}-{suffix}"


def generate_invoice_number() -> str:
    """
    Generate nomor invoice sequential berbasis timestamp + random.
    Format: INV/YYYY/MM/XXXXXXXX
    Contoh: INV/2024/10/00012345
    """
    now    = datetime.now()
    random = secrets.randbelow(99999999)
    return f"INV/{now.year}/{now.month:02d}/{random:08d}"
