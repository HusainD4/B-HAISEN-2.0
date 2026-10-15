"""
Modul: Notification Templates
Berisi semua template HTML email dan teks pesan WhatsApp.
"""
from datetime import datetime


# ============================================================
# EMAIL TEMPLATES (HTML)
# ============================================================

def email_order_receipt(
    customer_name: str,
    order_code: str,
    items: list[dict],
    total_amount: int,
    payment_method: str,
    order_date: str,
) -> dict:
    """
    Template email konfirmasi pesanan berhasil dibuat.
    Returns: {"subject": str, "html": str}
    """
    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee;">{item['name']}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">{item['qty']}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;text-align:right;">
                Rp{item['price']:,.0f}
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head><meta charset="UTF-8"><title>Konfirmasi Pesanan</title></head>
    <body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:0;">
      <div style="max-width:600px;margin:30px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <div style="background:#1a1a2e;padding:24px;text-align:center;">
          <h1 style="color:#e4b44a;margin:0;font-size:24px;">Haisen Official Store</h1>
          <p style="color:#ccc;margin:4px 0 0;">Konfirmasi Pesanan</p>
        </div>
        <div style="padding:32px;">
          <p>Halo, <strong>{customer_name}</strong>!</p>
          <p>Pesanan Anda dengan kode <strong>{order_code}</strong> telah berhasil dibuat pada <strong>{order_date}</strong>.</p>

          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:20px 0;">
            <thead>
              <tr style="background:#f0f0f0;">
                <th style="padding:10px;text-align:left;">Produk</th>
                <th style="padding:10px;text-align:center;">Qty</th>
                <th style="padding:10px;text-align:right;">Harga</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>

          <table width="100%" style="margin-top:8px;">
            <tr>
              <td style="text-align:right;font-weight:bold;font-size:16px;">
                Total: <span style="color:#1a1a2e;">Rp{total_amount:,.0f}</span>
              </td>
            </tr>
          </table>

          <div style="background:#fffbea;border:1px solid #e4b44a;border-radius:6px;padding:16px;margin:24px 0;">
            <p style="margin:0;font-size:14px;"><strong>Metode Pembayaran:</strong> {payment_method}</p>
            <p style="margin:8px 0 0;font-size:13px;color:#666;">
              Segera selesaikan pembayaran Anda. Pesanan akan otomatis dibatalkan jika tidak dibayar dalam <strong>24 jam</strong>.
            </p>
          </div>

          <p style="font-size:13px;color:#888;">
            Jika Anda memiliki pertanyaan, hubungi kami melalui WhatsApp atau email ini.
          </p>
        </div>
        <div style="background:#f0f0f0;padding:16px;text-align:center;font-size:12px;color:#999;">
          &copy; {datetime.now().year} Haisen Official Store. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    """
    return {"subject": f"Konfirmasi Pesanan #{order_code}", "html": html}


def email_payment_success(
    customer_name: str,
    order_code: str,
    total_amount: int,
    paid_at: str,
) -> dict:
    """Template email notifikasi pembayaran berhasil."""
    html = f"""
    <!DOCTYPE html><html lang="id">
    <head><meta charset="UTF-8"><title>Pembayaran Berhasil</title></head>
    <body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:0;">
      <div style="max-width:600px;margin:30px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <div style="background:#155724;padding:24px;text-align:center;">
          <h1 style="color:#fff;margin:0;font-size:22px;">✅ Pembayaran Berhasil!</h1>
        </div>
        <div style="padding:32px;">
          <p>Halo, <strong>{customer_name}</strong>!</p>
          <p>Pembayaran untuk pesanan <strong>#{order_code}</strong> sebesar
            <strong>Rp{total_amount:,.0f}</strong> telah kami terima pada <strong>{paid_at}</strong>.
          </p>
          <p>Tim kami akan segera memproses pesanan Anda. Terima kasih telah berbelanja di Haisen Official Store!</p>
        </div>
        <div style="background:#f0f0f0;padding:16px;text-align:center;font-size:12px;color:#999;">
          &copy; {datetime.now().year} Haisen Official Store.
        </div>
      </div>
    </body></html>
    """
    return {"subject": f"Pembayaran #{order_code} Berhasil", "html": html}


def email_digital_product_delivery(
    customer_name: str,
    order_code: str,
    product_name: str,
    download_url: str,
    expires_at: str,
) -> dict:
    """Template email pengiriman produk digital (link download)."""
    html = f"""
    <!DOCTYPE html><html lang="id">
    <head><meta charset="UTF-8"><title>Produk Digital Siap Diunduh</title></head>
    <body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:0;">
      <div style="max-width:600px;margin:30px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <div style="background:#1a1a2e;padding:24px;text-align:center;">
          <h1 style="color:#e4b44a;margin:0;font-size:22px;">📦 Produk Siap Diunduh</h1>
        </div>
        <div style="padding:32px;">
          <p>Halo, <strong>{customer_name}</strong>!</p>
          <p>Terima kasih atas pesanan Anda (<strong>#{order_code}</strong>).<br>
             Produk digital <strong>{product_name}</strong> sudah siap untuk diunduh.
          </p>
          <div style="text-align:center;margin:32px 0;">
            <a href="{download_url}"
               style="background:#e4b44a;color:#1a1a2e;padding:14px 32px;border-radius:6px;
                      text-decoration:none;font-weight:bold;font-size:16px;">
              ⬇ Unduh Sekarang
            </a>
          </div>
          <p style="font-size:13px;color:#888;text-align:center;">
            Link berlaku hingga: <strong>{expires_at}</strong>.<br>
            Setelah kedaluwarsa, hubungi kami untuk mendapatkan link baru.
          </p>
        </div>
        <div style="background:#f0f0f0;padding:16px;text-align:center;font-size:12px;color:#999;">
          &copy; {datetime.now().year} Haisen Official Store.
        </div>
      </div>
    </body></html>
    """
    return {"subject": f"Download Link Pesanan #{order_code} – {product_name}", "html": html}


def email_order_status_update(
    customer_name: str,
    order_code: str,
    new_status: str,
    note: str = "",
) -> dict:
    """Template email perubahan status pesanan (processing → shipped → completed)."""
    status_map = {
        "processing": ("🔄 Sedang Diproses", "#0d6efd"),
        "shipped": ("🚚 Pesanan Dikirim", "#fd7e14"),
        "completed": ("✅ Pesanan Selesai", "#198754"),
        "cancelled": ("❌ Pesanan Dibatalkan", "#dc3545"),
    }
    label, color = status_map.get(new_status, (new_status.title(), "#6c757d"))
    html = f"""
    <!DOCTYPE html><html lang="id">
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:0;">
      <div style="max-width:600px;margin:30px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
        <div style="background:{color};padding:24px;text-align:center;">
          <h1 style="color:#fff;margin:0;font-size:22px;">{label}</h1>
        </div>
        <div style="padding:32px;">
          <p>Halo, <strong>{customer_name}</strong>!</p>
          <p>Status pesanan Anda <strong>#{order_code}</strong> telah diperbarui menjadi: <strong>{label}</strong>.</p>
          {"<p><em>Catatan: " + note + "</em></p>" if note else ""}
        </div>
        <div style="background:#f0f0f0;padding:16px;text-align:center;font-size:12px;color:#999;">
          &copy; {datetime.now().year} Haisen Official Store.
        </div>
      </div>
    </body></html>
    """
    return {"subject": f"Update Pesanan #{order_code} – {label}", "html": html}


# ============================================================
# WHATSAPP MESSAGE TEMPLATES (Plain Text)
# ============================================================

def wa_order_created_admin(
    order_code: str,
    customer_name: str,
    total_amount: int,
    items_summary: str,
) -> str:
    """Pesan WA ke admin saat ada pesanan baru masuk."""
    return (
        f"🛒 *PESANAN BARU MASUK*\n"
        f"{'─' * 30}\n"
        f"Kode Pesanan : *{order_code}*\n"
        f"Pelanggan    : {customer_name}\n"
        f"Produk       : {items_summary}\n"
        f"Total        : *Rp{total_amount:,.0f}*\n"
        f"{'─' * 30}\n"
        f"Silakan cek dashboard untuk memproses pesanan."
    )


def wa_payment_success_admin(
    order_code: str,
    customer_name: str,
    total_amount: int,
    payment_method: str,
) -> str:
    """Pesan WA ke admin saat pembayaran berhasil dikonfirmasi."""
    return (
        f"✅ *PEMBAYARAN DITERIMA*\n"
        f"{'─' * 30}\n"
        f"Kode Pesanan : *{order_code}*\n"
        f"Pelanggan    : {customer_name}\n"
        f"Metode       : {payment_method}\n"
        f"Jumlah       : *Rp{total_amount:,.0f}*\n"
        f"{'─' * 30}\n"
        f"Segera proses pesanan."
    )


def wa_order_status_customer(
    customer_name: str,
    order_code: str,
    status_label: str,
    note: str = "",
) -> str:
    """Pesan WA ke pelanggan saat status pesanan berubah."""
    msg = (
        f"Halo *{customer_name}*! 👋\n\n"
        f"Pembaruan status pesanan Anda:\n"
        f"Kode    : *{order_code}*\n"
        f"Status  : *{status_label}*\n"
    )
    if note:
        msg += f"Catatan : {note}\n"
    msg += "\nTerima kasih telah berbelanja di *Haisen Official Store* 💛"
    return msg


def wa_download_link_customer(
    customer_name: str,
    product_name: str,
    download_url: str,
    expires_at: str,
) -> str:
    """Pesan WA ke pelanggan berisi link download produk digital."""
    return (
        f"Halo *{customer_name}*! 👋\n\n"
        f"Produk digital Anda sudah siap:\n"
        f"📦 *{product_name}*\n\n"
        f"🔗 Link Download:\n{download_url}\n\n"
        f"⏳ Berlaku hingga: *{expires_at}*\n\n"
        f"_Haisen Official Store_ 💛"
    )
