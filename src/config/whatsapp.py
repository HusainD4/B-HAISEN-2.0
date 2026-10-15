import logging
import httpx
from typing import Dict, Any, List, Optional
from src.config.settings import settings

logger = logging.getLogger("whatsapp_gateway")


class WhatsAppGatewayClient:
    """
    Client Integrasi WhatsApp Gateway Self-Hosted berbasis WhatsApp Web (Multi-Device QR Code).
    Tanpa pihak ketiga/SaaS berbayar.
    Dikhususkan untuk notifikasi internal: Superadmin, Admin, dan Staff.
    """

    def __init__(self):
        self.base_url = settings.WA_GATEWAY_URL.rstrip("/")
        self.api_key = settings.WA_API_KEY
        self.admin_numbers = settings.admin_phone_list

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["x-api-key"] = self.api_key
        return headers

    def _clean_phone_number(self, phone: str) -> str:
        """Membersihkan dan menstandarkan format nomor HP ke format 62xxx."""
        cleaned = "".join(filter(str.isdigit, phone))
        if cleaned.startswith("0"):
            cleaned = "62" + cleaned[1:]
        elif cleaned.startswith("+62"):
            cleaned = cleaned[1:]
        elif not cleaned.startswith("62") and cleaned:
            cleaned = "62" + cleaned
        return cleaned

    async def get_session_status(self) -> Dict[str, Any]:
        """
        Mengecek status koneksi sesi WhatsApp Web (CONNECTED, SCAN_QR, or DISCONNECTED).
        """
        url = f"{self.base_url}/session/status"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=self._get_headers())
                return res.json()
        except Exception as e:
            logger.error(f"Gagal memeriksa status sesi WhatsApp: {str(e)}")
            return {"connected": False, "status": "offline", "error": str(e)}

    async def get_qr_code(self) -> Optional[str]:
        """
        Mengambil QR Code (string base64 image / string QR) untuk di-scan oleh Admin/Staff.
        """
        url = f"{self.base_url}/session/qr"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    return data.get("qr") or data.get("qr_code") or data.get("image")
                return None
        except Exception as e:
            logger.error(f"Gagal mengambil QR Code WhatsApp: {str(e)}")
            return None

    async def send_message(self, phone_number: str, message: str) -> bool:
        """
        Mengirim pesan teks WhatsApp ke nomor tujuan tertentu.
        """
        target = self._clean_phone_number(phone_number)
        url = f"{self.base_url}/message/send-text"
        payload = {
            "receiver": target,
            "phone": target,
            "message": message,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload, headers=self._get_headers())
                if res.status_code in [200, 201]:
                    logger.info(f"Pesan WA berhasil dikirim ke {target}")
                    return True
                logger.warning(f"Gagal kirim pesan WA ({res.status_code}): {res.text}")
                return False
        except Exception as e:
            logger.error(f"Koneksi WhatsApp Gateway error ke {target}: {str(e)}")
            return False

    async def notify_admins(self, message: str) -> Dict[str, bool]:
        """
        Broadcast notifikasi alert transaksi/sistem penting ke seluruh nomor Superadmin, Admin, dan Staff.
        """
        results = {}
        if not self.admin_numbers:
            logger.warning("Tidak ada nomor WA Admin/Staff yang terdaftar di konfigurasi.")
            return results

        for number in self.admin_numbers:
            success = await self.send_message(number, message)
            results[number] = success
        return results


whatsapp_client = WhatsAppGatewayClient()
