# HAISEN OFFICIAL STORE - API DOCUMENTATION

Dokumentasi lengkap REST API backend untuk platform Haisen Official Store (Produk Digital & Layanan).

- **Base URL**: `http://localhost:8000` (atau URL server staging/production)
- **API Version**: `v1`
- **Swagger Docs**: `http://localhost:8000/docs` (Aktif saat `DEBUG=true`)
- **Format Data**: JSON (`application/json`) dan `multipart/form-data` untuk upload aset.

---

## 1. Standar Format Request & Response

### Format Header Autentikasi
Untuk endpoint yang membutuhkan autentikasi:
```http
Authorization: Bearer <access_token>
```

### Standar Response Sukses
```json
{
  "success": true,
  "data": { ... },
  "message": "Operasi berhasil"
}
```

### Standar Response Error
```json
{
  "detail": "Pesan deskripsi kesalahan yang spesifik",
  "status_code": 400
}
```

### Format Error Validasi (HTTP 422)
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error"
    }
  ]
}
```

---

## 2. Dynamic RBAC & Role Matrix

| Role Slug | Deskripsi Singkat | Izin Utama |
|---|---|---|
| `superadmin` | Pemilik sistem & IT Admin | Seluruh akses tanpa batasan |
| `admin` | Pengelola toko harian | Produk, Kategori, Pesanan, Verifikasi User |
| `finance` | Akuntan / Keuangan | Rekonsiliasi Midtrans, Riwayat Pesanan & Pendapatan |
| `staff` | Customer Service / Support | Monitoring pesanan customer, Bantuan komplain |
| `user` | Pelanggan Toko | Katalog, Keranjang, Checkout, Unduh file berbayar |

---

## 3. Modul Autentikasi (`/api/v1/auth`)

### 3.1. Registrasi Akun Baru
- **Endpoint**: `POST /api/v1/auth/register`
- **Auth**: Publik
- **Rate Limit**: 10 req/menit

**Request Body:**
```json
{
  "email": "customer@example.com",
  "password": "Password123!",
  "full_name": "Budi Santoso",
  "phone": "081234567890",
  "address": "Jl. Merdeka No. 45, RT 02 / RW 05, Dekat Masjid Al-Ikhlas",
  "province": "Jawa Barat",
  "city": "Kota Bandung",
  "district": "Coblong",
  "postal_code": "40132"
}
```

**Response (HTTP 201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "9a7fbc28d...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "67b84db8-b570-466d-8c10-9cbb8aa4041d",
    "email": "customer@example.com",
    "full_name": "Budi Santoso",
    "phone": "081234567890",
    "address": "Jl. Merdeka No. 45, RT 02 / RW 05, Dekat Masjid Al-Ikhlas",
    "province": "Jawa Barat",
    "city": "Kota Bandung",
    "district": "Coblong",
    "postal_code": "40132",
    "role": "user",
    "is_active": true,
    "is_verified": false
  }
}
```

---

### 3.2. Login Pengguna
- **Endpoint**: `POST /api/v1/auth/login`
- **Auth**: Publik
- **Rate Limit**: 5 req/menit (Anti brute-force)

**Request Body:**
```json
{
  "email": "customer@example.com",
  "password": "Password123!"
}
```

**Response (HTTP 200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "a1c2d3e4f...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "67b84db8-b570-466d-8c10-9cbb8aa4041d",
    "email": "customer@example.com",
    "full_name": "Budi Santoso",
    "phone": "081234567890",
    "role": "user",
    "is_active": true,
    "is_verified": true
  }
}
```

---

### 3.3. Refresh Access Token
- **Endpoint**: `POST /api/v1/auth/refresh`
- **Auth**: Publik

**Request Body:**
```json
{
  "refresh_token": "a1c2d3e4f..."
}
```

**Response (HTTP 200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "new_rotated_refresh_token...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": { ... }
}
```

---

### 3.4. Logout
- **Endpoint**: `POST /api/v1/auth/logout`
- **Auth**: Bearer Token

**Request Body:**
```json
{
  "refresh_token": "a1c2d3e4f..."
}
```

**Response (HTTP 200 OK):**
```json
{
  "message": "Berhasil logout dari sistem."
}
```

---

### 3.5. Informasi Akun Saat Ini (`/me`)
- **Endpoint**: `GET /api/v1/auth/me`
- **Auth**: Bearer Token

**Response (HTTP 200 OK):**
```json
{
  "user": {
    "id": "67b84db8-b570-466d-8c10-9cbb8aa4041d",
    "email": "customer@example.com",
    "full_name": "Budi Santoso",
    "phone": "081234567890",
    "role": "user",
    "is_active": true,
    "is_verified": true
  },
  "role": "user",
  "permissions": []
}
```

---

### 3.6. Lupa Password & Reset Password
- **Forgot Password**: `POST /api/v1/auth/forgot-password`
  - Body: `{"email": "customer@example.com"}`
  - Response: `{"message": "Jika email terdaftar, instruksi reset kata sandi telah dikirim ke kotak masuk Anda."}`

- **Reset Password**: `POST /api/v1/auth/reset-password`
  - Body: `{"token": "reset_token_from_email", "new_password": "NewSecurePassword123!"}`
  - Response: `{"message": "Kata sandi berhasil diatur ulang. Silakan login dengan kata sandi baru."}`

- **Ganti Password (Saat Login)**: `POST /api/v1/auth/change-password`
  - Body: `{"old_password": "Password123!", "new_password": "NewSecurePassword123!"}`
  - Response: `{"message": "Kata sandi berhasil diperbarui."}`

---

## 4. Modul Manajemen User & RBAC (`/api/v1/users`)

### 4.1. Ambil Profil & Update Profil Sendiri
- `GET /api/v1/users/profile` (Auth: User Aktif)
- `PUT /api/v1/users/profile` (Auth: User Aktif)
  - Body: `{"full_name": "Budi Santoso S.Kom", "phone": "081298765432"}`

### 4.2. Daftar Pengguna (Admin / Superadmin)
- **Endpoint**: `GET /api/v1/users`
- **Query Params**:
  - `page` (int, default: 1)
  - `limit` (int, default: 20)
  - `search` (string, optional: email/nama)
  - `role` (string, optional: `admin`, `user`, dll)
  - `is_active` (boolean, optional)
- **Permission**: `user:read`

**Response (HTTP 200 OK):**
```json
{
  "items": [
    {
      "id": "67b84db8-b570-466d-8c10-9cbb8aa4041d",
      "email": "customer@example.com",
      "full_name": "Budi Santoso",
      "phone": "081234567890",
      "is_active": true,
      "is_verified": true,
      "role": {
        "id": "role-user-0000-000000000000000005",
        "name": "User",
        "slug": "user"
      },
      "created_at": "2026-10-14T08:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

### 4.3. Buat User Oleh Admin
- **Endpoint**: `POST /api/v1/users`
- **Permission**: `user:manage`
- **Body**:
```json
{
  "email": "finance@haisen.my.id",
  "password": "PasswordStaff123!",
  "full_name": "Dewi Finance",
  "phone": "081999888777",
  "role_id": "role-finance-0000-0000000000000003",
  "is_active": true
}
```

### 4.4. Operasi Akun User Lainnya
- `PUT /api/v1/users/{user_id}`: Edit data pengguna
- `PATCH /api/v1/users/{user_id}/role`: Ubah role (`{"role_id": "..."}`)
- `PATCH /api/v1/users/{user_id}/status`: Aktif/Nonaktifkan (`{"is_active": false}`)
- `DELETE /api/v1/users/{user_id}`: Soft delete user

### 4.5. Kelola Role & Permissions Dinamis (Superadmin Only)
- `GET /api/v1/users/roles/all`: Ambil seluruh role & izin
- `POST /api/v1/users/roles`: Buat role baru (`{"name": "Editor", "slug": "editor", "description": "..."}`)
- `PUT /api/v1/users/roles/{role_id}/permissions`: Sinkronisasi permissions (`{"permission_ids": ["perm-1", "perm-2"]}`)
- `DELETE /api/v1/users/roles/{role_id}`: Hapus role non-sistem
- `GET /api/v1/users/permissions/all`: Ambil master permissions sistem

---

## 5. Modul Katalog Produk & Storage S3 (`/api/v1/products`)

### 5.1. Upload Gambar & File Aset ke Bucket
- `POST /api/v1/products/upload/banner`: Multipart form-data `file` (Banner lebar untuk hero/header)
- `POST /api/v1/products/upload/thumbnail`: Multipart form-data `file` (Foto cover produk)
- `POST /api/v1/products/upload/variant-image`: Multipart form-data `file` (Foto preview varian)
- `POST /api/v1/products/upload/digital-file`: Multipart form-data `file` (File arsip ZIP/PDF/Program yang tersimpan aman di private bucket)

**Response Upload Gambar:**
```json
{
  "url": "https://storage.haisen.my.id/products/banners/20261014_banner.webp",
  "file_key": "products/banners/20261014_banner.webp",
  "file_name": "banner.webp",
  "file_size": 245000,
  "content_type": "image/webp"
}
```

### 5.2. Katalog Publik (Storefront)
- **Endpoint**: `GET /api/v1/products`
- **Query Params**:
  - `page`: Nomor halaman (default: 1)
  - `limit`: Jumlah per halaman (default: 12)
  - `search`: Kata kunci pencarian nama/deskripsi
  - `category`: Filter slug kategori (misal: `template-website`)
  - `featured`: Filter produk rekomendasi (`true`/`false`)
  - `sort`: `newest`, `price_asc`, `price_desc`

**Response:**
```json
{
  "items": [
    {
      "id": "prod-1234",
      "name": "SaaS Landing Page Template",
      "slug": "saas-landing-page-template",
      "short_description": "Template Next.js + Tailwind CSS modern",
      "banner_image_url": "https://storage.haisen.my.id/banner.webp",
      "thumbnail_url": "https://storage.haisen.my.id/thumb.webp",
      "base_price": 250000,
      "discount_price": 199000,
      "is_featured": true,
      "category": {
        "id": "cat-1",
        "name": "Template Website",
        "slug": "template-website"
      },
      "variants": [
        {
          "id": "var-1",
          "name": "Personal License",
          "sku": "SAAS-PERS-01",
          "variant_image_url": "https://storage.haisen.my.id/var1.webp",
          "price": 199000,
          "discount_price": null,
          "license_type": "personal"
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 12,
  "total_pages": 1
}
```

### 5.3. Detail Produk Berdasarkan Slug
- **Endpoint**: `GET /api/v1/products/detail/{slug}`
- **Auth**: Publik

### 5.4. Tambah Produk Lengkap (Admin)
- **Endpoint**: `POST /api/v1/products`
- **Permission**: `product:create`

**Request Body:**
```json
{
  "category_id": "cat-uuid",
  "name": "E-Commerce Microservices Boilerplate",
  "slug": "ecommerce-microservices-boilerplate",
  "short_description": "Arsitektur lengkap backend FastAPI + PostgreSQL",
  "description": "Dokumentasi dan source code lengkap siap pakai.",
  "banner_image_url": "https://storage.haisen.my.id/banner.webp",
  "thumbnail_url": "https://storage.haisen.my.id/thumb.webp",
  "gallery_images": ["https://storage.haisen.my.id/screen1.webp"],
  "base_price": 450000,
  "discount_price": 350000,
  "is_featured": true,
  "is_active": true,
  "variants": [
    {
      "name": "Standard Single Dev",
      "sku": "ECOM-STD-01",
      "variant_image_url": "https://storage.haisen.my.id/var1.webp",
      "price": 350000,
      "license_type": "single-developer",
      "digital_file_key": "private/assets/ecom-v1.zip",
      "digital_file_name": "ecom-v1.zip",
      "digital_file_size": 15420000
    }
  ]
}
```

### 5.5. Unduh Aset Digital Terproteksi (Presigned URL)
- **Endpoint**: `GET /api/v1/products/variants/{variant_id}/download-url`
- **Auth**: Bearer Token
- **Response**:
```json
{
  "download_url": "https://storage.haisen.my.id/private/assets/ecom-v1.zip?X-Amz-Signature=...&Expires=3600",
  "file_name": "ecom-v1.zip",
  "expires_in": 3600
}
```

---

## 6. Modul Keranjang Belanja & Checkout (`/api/v1/orders`)

### 6.1. Manajemen Keranjang Belanja (Tersimpan di Database)
- `GET /api/v1/orders/cart`: Ambil item keranjang belanja user
- `POST /api/v1/orders/cart`: Tambah varian produk ke keranjang
  - Body: `{"variant_id": "var-1", "quantity": 1}`
- `PUT /api/v1/orders/cart/{item_id}`: Ubah kuantitas item (`{"quantity": 2}`)
- `DELETE /api/v1/orders/cart/{item_id}`: Hapus item dari keranjang
- `DELETE /api/v1/orders/cart`: Kosongkan keranjang belanja

### 6.2. Aturan Input Data Checkout (Fisik vs Digital / Jasa)

Sistem membedakan kebutuhan data saat checkout berdasarkan jenis produk yang dibeli:

| Tipe Produk | Data yang Wajib / Diperlukan | Ongkir & Kurir |
|---|---|---|
| **Barang / Fisik (`physical`)** | Data Akun (Nama, Email, No HP) + **Alamat Lengkap Pengiriman** (Jalan, RT/RW, Patokan), **Provinsi, Kabupaten/Kota, Kecamatan** (Kalkulasi RajaOngkir), **Kode Pos** (Validasi Kurir), dan **Catatan Pesanan**. | **Wajib diisi**: `courier`, `courier_service`, dan `shipping_cost` dihitung otomatis via RajaOngkir. |
| **Produk Digital / Jasa (`digital` / `service`)** | Cukup **Data User yang Login** (Nama, Email, No HP), **Alamat Lengkap** (untuk identitas invoice kawasan Indonesia), dan **Catatan Pembeli**. | **Tidak diperlukan**: `shipping_cost = 0`, kurir tidak perlu diisi. |

---

### 6.3. Checkout Keranjang Belanja (Direct Midtrans Core API Tanpa Snap)
- **Endpoint**: `POST /api/v1/orders/checkout`
- **Auth**: Bearer Token

#### A. Contoh Request Produk Fisik (Data Lengkap + RajaOngkir)

**Request Body:**
```json
{
  "customer_name": "Budi Santoso",
  "customer_email": "customer@example.com",
  "customer_phone": "081234567890",
  "payment_method": "qris",
  "shipping_address": "Jl. Merdeka No. 45, RT 02 / RW 05, Dekat Masjid Al-Ikhlas",
  "shipping_province": "Jawa Barat",
  "shipping_city": "Kota Bandung",
  "shipping_district": "Coblong",
  "shipping_postal_code": "40132",
  "courier": "jne",
  "courier_service": "REG",
  "shipping_cost": 22000,
  "notes": "Tolong packing rapi ya"
}
```
*(Pilihan `payment_method`: `qris`, `bca_va`, `bni_va`, `bri_va`, `mandiri`)*

**Response (HTTP 201 Created):**
```json
{
  "order_number": "ORD-20261014-A1B2C3",
  "total_amount": 372000,
  "status": "pending",
  "payment_method": "qris",
  "customer_name": "Budi Santoso",
  "customer_email": "customer@example.com",
  "shipping_address": "Jl. Merdeka No. 45, RT 02 / RW 05, Dekat Masjid Al-Ikhlas",
  "shipping_province": "Jawa Barat",
  "shipping_city": "Kota Bandung",
  "shipping_district": "Coblong",
  "shipping_postal_code": "40132",
  "shipping_cost": 22000,
  "courier": "jne",
  "courier_service": "REG",
  "notes": "Tolong packing rapi ya",
  "items": [
    {
      "product_name": "E-Commerce Microservices Boilerplate",
      "variant_name": "Standard Single Dev",
      "price": 350000,
      "quantity": 1,
      "subtotal": 350000
    }
  ],
  "payment": {
    "payment_type": "qris",
    "gross_amount": 350000,
    "transaction_status": "pending",
    "qr_string": "00020101021226680016ID.CO.MIDTRANS.WWW01189360052...",
    "qr_code_url": "https://api.midtrans.com/v2/qris/31201931/qr-code",
    "bank": null,
    "va_number": null,
    "expiry_time": "2026-10-14T08:45:00Z"
  }
}
```

*Jika metode Virtual Account (contoh: `bca_va`):*
```json
"payment": {
  "payment_type": "bank_transfer",
  "gross_amount": 350000,
  "bank": "bca",
  "va_number": "7001200001234567",
  "expiry_time": "2026-10-15T08:00:00Z"
}
```

#### B. Contoh Request Produk Digital / Jasa (Hanya Data User, Alamat Lengkap & Catatan)
```json
{
  "payment_method": "qris",
  "shipping_address": "Jl. Merdeka No. 45, RT 02 / RW 05, Bandung",
  "notes": "Mohon kirimkan lisensi segera ke email saya."
}
```
*(Nama, email, dan no HP otomatis diambil dari session akun user yang login. Ongkos kirim Rp 0 dan kurir tidak perlu disertakan).*

---

### 6.4. Beli Langsung (Direct Buy Tanpa Keranjang)
- **Endpoint**: `POST /api/v1/orders/direct-buy`
- **Auth**: Opsional (Mendukung Guest Checkout)

**Request Body:**
```json
{
  "variant_id": "var-1",
  "quantity": 1,
  "customer_name": "Budi Santoso",
  "customer_email": "customer@example.com",
  "customer_phone": "081234567890",
  "payment_method": "bca_va",
  "notes": "Direct buy instant"
}
```

### 6.4. Riwayat & Detail Pesanan
- `GET /api/v1/orders/my-orders`: Riwayat pesanan user yang sedang login
- `GET /api/v1/orders/{order_number}`: Detail status pesanan & petunjuk bayar
- `GET /api/v1/orders/admin/all`: Seluruh pesanan toko (Permission: `order:read_all`)

---

## 7. Modul Pembayaran & Webhook Midtrans (`/api/v1/payments`)

### 7.1. Webhook Listener Otomatis dari Midtrans
- **Endpoint**: `POST /api/v1/payments/webhook`
- **Auth**: Publik (Verifikasi Signature Key SHA-512)

**Payload dari Midtrans:**
```json
{
  "order_id": "ORD-20261014-A1B2C3",
  "status_code": "200",
  "gross_amount": "350000.00",
  "signature_key": "4c3b2a1...",
  "transaction_status": "settlement",
  "fraud_status": "accept",
  "payment_type": "qris",
  "transaction_id": "tx-midtrans-999"
}
```

**Response (HTTP 200 OK):**
```json
{
  "status": "success",
  "message": "Webhook berhasil diproses. Status order diperbarui menjadi paid.",
  "order_id": "ORD-20261014-A1B2C3"
}
```

### 7.2. Polling Status Pembayaran (Client Frontend)
- **Endpoint**: `GET /api/v1/payments/status/{order_number}`
- **Auth**: Publik

**Response:**
```json
{
  "order_number": "ORD-20261014-A1B2C3",
  "is_paid": true,
  "status": "paid",
  "payment_type": "qris",
  "paid_at": "2026-10-14T08:15:30Z"
}
```

### 7.3. Sinkronisasi Manual Midtrans (Finance / Admin)
- **Endpoint**: `POST /api/v1/payments/sync-midtrans/{order_number}`
- **Permission**: `payment:manage`
