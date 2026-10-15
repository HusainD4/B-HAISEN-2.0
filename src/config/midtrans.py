import base64
import hashlib
import httpx
from typing import Dict, Any, Optional, List
from src.config.settings import settings


class MidtransClient:
    """
    Wrapper Client untuk Midtrans Core API (Direct Charge: QRIS & Bank Virtual Account).
    Tidak menggunakan popup Snap; transaksi diproses langsung di antarmuka halaman toko.
    """

    def __init__(self):
        self.server_key = settings.MIDTRANS_SERVER_KEY
        self.client_key = settings.MIDTRANS_CLIENT_KEY
        self.is_production = settings.MIDTRANS_IS_PRODUCTION
        self.base_url = "https://api.midtrans.com/v2" if self.is_production else "https://api.sandbox.midtrans.com/v2"

    def _get_auth_header(self) -> Dict[str, str]:
        auth_bytes = f"{self.server_key}:".encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_b64}",
        }

    async def charge_core_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Endpoint Core API Charge (/v2/charge) untuk memproses pembayaran langsung.
        """
        url = f"{self.base_url}/charge"
        headers = self._get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def charge_qris(
        self,
        order_id: str,
        gross_amount: int,
        customer_details: Dict[str, Any],
        item_details: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Charge langsung QRIS Dinamis (Gopay / ShopeePay / Semua Aplikasi Bank & E-Wallet).
        Mengembalikan qr_string dan url gambar QR Code untuk ditampilkan di halaman frontend.
        """
        payload = {
            "payment_type": "qris",
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": gross_amount,
            },
            "qris": {
                "acquirer": "gopay",
            },
            "customer_details": customer_details,
        }
        if item_details:
            payload["item_details"] = item_details

        return await self.charge_core_api(payload)

    async def charge_bank_transfer(
        self,
        order_id: str,
        gross_amount: int,
        bank: str,  # "bca", "bni", "bri", "permata", "mandiri"
        customer_details: Dict[str, Any],
        item_details: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Charge langsung Bank Virtual Account (BCA, BNI, BRI, Permata, Mandiri E-Bill).
        Mengembalikan nomor VA atau Bill Key untuk dibayar pelanggan.
        """
        bank_lower = bank.lower().strip()

        if bank_lower == "mandiri":
            payload = {
                "payment_type": "echannel",
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": gross_amount,
                },
                "echannel": {
                    "bill_info1": "Payment For:",
                    "bill_info2": f"Order {order_id}",
                },
                "customer_details": customer_details,
            }
        elif bank_lower == "permata":
            payload = {
                "payment_type": "permata",
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": gross_amount,
                },
                "customer_details": customer_details,
            }
        else:
            payload = {
                "payment_type": "bank_transfer",
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": gross_amount,
                },
                "bank_transfer": {
                    "bank": bank_lower,  # bca, bni, bri
                },
                "customer_details": customer_details,
            }

        if item_details:
            payload["item_details"] = item_details

        return await self.charge_core_api(payload)

    async def get_transaction_status(self, order_id: str) -> Dict[str, Any]:
        """Memeriksa status pembayaran transaksi langsung ke server Midtrans."""
        url = f"{self.base_url}/{order_id}/status"
        headers = self._get_auth_header()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def cancel_transaction(self, order_id: str) -> Dict[str, Any]:
        """Membatalkan transaksi di Midtrans."""
        url = f"{self.base_url}/{order_id}/cancel"
        headers = self._get_auth_header()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers)
            return response.json()

    def verify_webhook_signature(
        self, order_id: str, status_code: str, gross_amount: str, signature_key: str
    ) -> bool:
        """
        Verifikasi keaslian webhook Midtrans menggunakan SHA-512.
        Formula: SHA512(order_id + status_code + gross_amount + ServerKey)
        """
        raw_string = f"{order_id}{status_code}{gross_amount}{self.server_key}"
        expected_signature = hashlib.sha512(raw_string.encode("utf-8")).hexdigest()
        return expected_signature.lower() == signature_key.lower()


midtrans_client = MidtransClient()
