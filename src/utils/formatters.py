"""
Modul: Formatters Helper
Fungsi utilitas untuk pemformatan data: Rupiah, tanggal Indonesia, string sanitasi.
"""
import re
from datetime import datetime, date
from typing import Union


MONTHS_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

DAYS_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def format_rupiah(amount: Union[int, float], with_prefix: bool = True) -> str:
    """
    Format angka ke format mata uang Rupiah Indonesia.
    Contoh: 150000 -> "Rp 150.000" atau "Rp 150.000,00"

    Args:
        amount: Nilai angka.
        with_prefix: Jika True, tambahkan "Rp " di depan.

    Returns:
        String mata uang.
    """
    if amount is None:
        return "Rp 0" if with_prefix else "0"
    # Format ribuan dengan titik
    formatted = f"{int(amount):,}".replace(",", ".")
    return f"Rp {formatted}" if with_prefix else formatted


def format_rupiah_decimal(amount: Union[int, float]) -> str:
    """Format Rupiah dengan 2 desimal: Rp 150.000,50"""
    integer_part = int(amount)
    decimal_part = round((amount - integer_part) * 100)
    return f"Rp {integer_part:,}".replace(",", ".") + f",{decimal_part:02d}"


def format_date_id(
    date_obj: Union[datetime, date, str],
    show_time: bool = False,
    long_format: bool = True,
) -> str:
    """
    Format tanggal ke format Indonesia.
    Contoh: datetime(2024, 5, 1) -> "1 Mei 2024" atau "Rabu, 1 Mei 2024 14:30"

    Args:
        date_obj: Objek datetime/date atau string ISO (YYYY-MM-DD).
        show_time: Jika True, tambahkan jam:menit.
        long_format: Jika True, tambahkan nama hari.

    Returns:
        String tanggal format Indonesia.
    """
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj)
        except ValueError:
            return date_obj

    day_name  = DAYS_ID[date_obj.weekday()]
    month_name = MONTHS_ID[date_obj.month]
    result    = f"{date_obj.day} {month_name} {date_obj.year}"

    if long_format:
        result = f"{day_name}, {result}"
    if show_time and isinstance(date_obj, datetime):
        result += f" {date_obj.strftime('%H:%M')}"

    return result


def format_phone_wa(phone: str) -> str:
    """
    Konversi nomor telepon ke format WhatsApp Indonesia.
    Contoh: "08123456789" -> "628123456789"
             "+628123456789" -> "628123456789"

    Args:
        phone: Nomor telepon (berbagai format).

    Returns:
        String nomor WA tanpa +.
    """
    phone = re.sub(r"[^\d+]", "", phone)
    phone = phone.lstrip("+")
    if phone.startswith("0"):
        phone = "62" + phone[1:]
    if not phone.startswith("62"):
        phone = "62" + phone
    return phone


def format_order_code(prefix: str = "HSO") -> str:
    """
    Buat kode pesanan dengan format prefix + timestamp.
    Contoh: "HSO-20241001-143022"
    (Gunakan generators.generate_order_code() untuk versi dengan random suffix.)
    """
    now = datetime.now()
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M%S')}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Potong teks panjang dan tambahkan suffix jika diperlukan."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix


def sanitize_filename(filename: str) -> str:
    """
    Hapus karakter tidak aman dari nama file.
    Contoh: "my file (1).exe" -> "my_file_1.exe"
    """
    # Ganti spasi & karakter berbahaya
    name = re.sub(r"[^\w.\-]", "_", filename)
    # Hapus titik berulang
    name = re.sub(r"\.{2,}", ".", name)
    return name.strip("_")


def slugify(text: str) -> str:
    """
    Konversi teks ke slug URL-safe lowercase.
    Contoh: "Produk Terbaru 2024" -> "produk-terbaru-2024"
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


def mask_email(email: str) -> str:
    """
    Masking email untuk tampilan publik.
    Contoh: "johndoe@gmail.com" -> "jo***@gmail.com"
    """
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"{local}***@{domain}"
    return f"{local[:2]}{'*' * (len(local) - 2)}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Masking nomor telepon untuk tampilan publik.
    Contoh: "628123456789" -> "6281****6789"
    """
    if len(phone) < 8:
        return phone
    return phone[:4] + "*" * (len(phone) - 8) + phone[-4:]
