import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILES = {
    # src/config
    "src/config/database.py": '''"""
Modul: Database Connection
Fungsi:
- Mengelola koneksi dan engine database (Supabase / PostgreSQL).
- Inisialisasi session maker (async / sync session) untuk transaksi database.
Isi yang diharapkan:
- create_async_engine / create_engine
- async_sessionmaker / sessionmaker
- Dependency get_db()
"""
''',
    "src/config/midtrans.py": '''"""
Modul: Midtrans Client Configuration
Fungsi:
- Konfigurasi kredensial Midtrans Payment Gateway (Snap API & Core API).
- Penanganan mode Sandbox vs Production.
Isi yang diharapkan:
- Client initialization dengan Server Key & Client Key
- Konfigurasi Snap & Core API instance
"""
''',
    "src/config/mailer.py": '''"""
Modul: Email Service Configuration
Fungsi:
- Konfigurasi SMTP / Email Provider API (Resend, SendGrid, Mailgun, dll).
Isi yang diharapkan:
- Mailer client / SMTP transport configuration
- Kredensial API key / user & password SMTP
"""
''',
    "src/config/whatsapp.py": '''"""
Modul: WhatsApp Gateway Configuration
Fungsi:
- Konfigurasi integrasi WhatsApp Gateway API (Fonnte, Watzap, Wablas, dll).
Isi yang diharapkan:
- Endpoint URL & API Token WhatsApp Gateway
- HTTP client instance / headers setup
"""
''',
    "src/config/settings.py": '''"""
Modul: Application Settings & Environment Variables
Fungsi:
- Validasi dan pemetaan environment variables (.env) menggunakan Pydantic Settings / Dotenv.
Isi yang diharapkan:
- Class Settings (BaseSettings)
- Konfigurasi APP_NAME, PORT, DATABASE_URL, MIDTRANS_KEYS, JWT_SECRET, dll.
"""
''',

    # src/core
    "src/core/database_base.py": '''"""
Modul: Database Base Model
Fungsi:
- Base class ORM untuk semua model database (SQLAlchemy DeclarativeBase).
Isi yang diharapkan:
- DeclarativeBase / Base class
- Common mixins (id, created_at, updated_at, is_deleted)
"""
''',
    "src/core/exceptions.py": '''"""
Modul: Global Exceptions & Error Handlers
Fungsi:
- Definisi custom HTTP exceptions dan format response error terstandar.
Isi yang diharapkan:
- Custom Exception classes (NotFoundException, UnauthorizedException, BadRequestException, dll)
- Global exception handler registration
"""
''',
    "src/core/middleware.py": '''"""
Modul: Application Middleware
Fungsi:
- Konfigurasi middleware aplikasi (CORS, Gzip, Logging, Request Execution Timing).
Isi yang diharapkan:
- CORSMiddleware setup
- Request logging middleware
- Custom header injection
"""
''',
    "src/core/security.py": '''"""
Modul: Security & Cryptography
Fungsi:
- Enkripsi/hashing password dan pembuatan/verifikasi token JWT.
Isi yang diharapkan:
- Password hashing (Bcrypt / Argon2) verify & hash functions
- create_access_token, create_refresh_token, decode_token
"""
''',
    "src/core/dependencies.py": '''"""
Modul: Core Dependencies
Fungsi:
- Dependency injection untuk autentikasi user dan pengecekan otorisasi multi-role.
Isi yang diharapkan:
- get_current_user
- Role checker dependency (Superadmin, Admin, Staff, User)
- Active user guard
"""
''',
    "src/core/rate_limiter.py": '''"""
Modul: Rate Limiter
Fungsi:
- Membatasi jumlah request endpoint untuk mitigasi DDoS dan brute force attack.
Isi yang diharapkan:
- Rate limiter middleware / decorator berbasis Redis atau in-memory
- Config key prefix, time window, max requests
"""
''',
    "src/core/base_service.py": '''"""
Modul: Base Service
Fungsi:
- Base class berorientasi objek (OOP) untuk seluruh service layer.
Isi yang diharapkan:
- BaseService class dengan helper transaksi dan penanganan error umum
"""
''',

    # src/modules/auth
    "src/modules/auth/auth_controller.py": '''"""
Modul: Auth Controller
Fungsi:
- Definisi endpoint / routing HTTP untuk login, register, refresh token, logout, dan verifikasi akun.
Isi yang diharapkan:
- APIRouter untuk /api/v1/auth
- Handler endpoints: login, register, refresh, me, logout
"""
''',
    "src/modules/auth/auth_service.py": '''"""
Modul: Auth Service
Fungsi:
- Business logic untuk autentikasi, validasi kredensial, dan penerbitan token JWT.
Isi yang diharapkan:
- AuthService class
- Metode: authenticate_user, register_user, refresh_tokens
"""
''',
    "src/modules/auth/auth_repository.py": '''"""
Modul: Auth Repository
Fungsi:
- Query database langsung yang berhubungan dengan credential dan sesi user.
Isi yang diharapkan:
- AuthRepository class
- Metode: find_by_email, create_user_record, store_refresh_token
"""
''',
    "src/modules/auth/auth_model.py": '''"""
Modul: Auth Model
Fungsi:
- Definisi tabel database untuk sesi login, refresh token, atau token reset password.
Isi yang diharapkan:
- RefreshToken model / UserSession model
"""
''',
    "src/modules/auth/auth_schema.py": '''"""
Modul: Auth Schema (DTO)
Fungsi:
- Validasi data request dan response untuk modul autentikasi (Pydantic models).
Isi yang diharapkan:
- LoginRequest, RegisterRequest, TokenResponse, UserResponse
"""
''',

    # src/modules/users
    "src/modules/users/user_controller.py": '''"""
Modul: Users Controller
Fungsi:
- Routing HTTP untuk manajemen user dan multi-role (CRUD user, ganti role, update profil).
Isi yang diharapkan:
- APIRouter untuk /api/v1/users
- Handler endpoints: get_users, get_user_by_id, update_profile, update_role, delete_user
"""
''',
    "src/modules/users/user_service.py": '''"""
Modul: Users Service
Fungsi:
- Business logic pengelolaan data user, validasi hak akses, dan manajemen role.
Isi yang diharapkan:
- UserService class
- Metode: list_users, get_user, update_user_profile, change_user_role
"""
''',
    "src/modules/users/user_repository.py": '''"""
Modul: Users Repository
Fungsi:
- Akses database untuk tabel users (pencarian, update data profil, filter role).
Isi yang diharapkan:
- UserRepository class
- Metode: get_all, get_by_id, update, delete
"""
''',
    "src/modules/users/user_model.py": '''"""
Modul: Users Model
Fungsi:
- Entity / tabel database untuk users dan enum roles.
Isi yang diharapkan:
- User model (id, email, password_hash, full_name, role, status, timestamps)
- RoleEnum (superadmin, admin, staff, user)
"""
''',
    "src/modules/users/user_schema.py": '''"""
Modul: Users Schema
Fungsi:
- Skema validasi data request & response untuk manajemen user.
Isi yang diharapkan:
- UserCreateSchema, UserUpdateSchema, UserResponseSchema, RoleUpdateSchema
"""
''',

    # src/modules/products
    "src/modules/products/product_controller.py": '''"""
Modul: Products Controller
Fungsi:
- Endpoint katalog produk digital dan layanan (list produk, detail, tambah/edit/hapus).
Isi yang diharapkan:
- APIRouter untuk /api/v1/products
- Endpoints publik & admin: get_products, get_product_by_slug, create_product, update_product, delete_product
"""
''',
    "src/modules/products/product_service.py": '''"""
Modul: Products Service
Fungsi:
- Business logic katalog produk, filter kategori, manajemen stok digital/lisensi.
Isi yang diharapkan:
- ProductService class
- Metode: fetch_active_products, create_new_product, update_existing_product
"""
''',
    "src/modules/products/product_repository.py": '''"""
Modul: Products Repository
Fungsi:
- Operasi query database untuk data produk, kategori, dan aset digital.
Isi yang diharapkan:
- ProductRepository class
- Metode: find_all, find_by_slug, insert, update, soft_delete
"""
''',
    "src/modules/products/product_model.py": '''"""
Modul: Products Model
Fungsi:
- Definisi tabel database untuk produk digital, kategori, file digital/lisensi, dan harga.
Isi yang diharapkan:
- Product model, ProductCategory model, ProductAsset model
"""
''',
    "src/modules/products/product_schema.py": '''"""
Modul: Products Schema
Fungsi:
- Validasi data request dan response katalog produk.
Isi yang diharapkan:
- ProductCreate, ProductUpdate, ProductResponse, ProductFilterQuery
"""
''',

    # src/modules/orders
    "src/modules/orders/order_controller.py": '''"""
Modul: Orders Controller
Fungsi:
- Endpoint keranjang belanja, checkout transaksi, dan riwayat pesanan.
Isi yang diharapkan:
- APIRouter untuk /api/v1/orders
- Endpoints: create_order, get_user_orders, get_order_detail, cancel_order
"""
''',
    "src/modules/orders/order_service.py": '''"""
Modul: Orders Service
Fungsi:
- Business logic pembuatan pesanan, kalkulasi total, validasi ketersediaan produk digital.
Isi yang diharapkan:
- OrderService class
- Metode: create_checkout_order, get_order_by_id, update_order_status
"""
''',
    "src/modules/orders/order_repository.py": '''"""
Modul: Orders Repository
Fungsi:
- Query database untuk tabel pesanan (orders) dan item pesanan (order_items).
Isi yang diharapkan:
- OrderRepository class
- Metode: save_order, find_by_order_number, list_by_user_id
"""
''',
    "src/modules/orders/order_model.py": '''"""
Modul: Orders Model
Fungsi:
- Definisi tabel database untuk data pesanan, nomor invoice, dan status pesanan.
Isi yang diharapkan:
- Order model, OrderItem model
- OrderStatusEnum (pending, paid, completed, cancelled, expired)
"""
''',
    "src/modules/orders/order_schema.py": '''"""
Modul: Orders Schema
Fungsi:
- Validasi payload pemesanan, checkout, dan respons detail order.
Isi yang diharapkan:
- OrderCreateSchema, OrderItemSchema, OrderResponseSchema
"""
''',

    # src/modules/payments
    "src/modules/payments/payment_controller.py": '''"""
Modul: Payments Controller
Fungsi:
- Endpoint pembayaran: request token Snap Midtrans dan webhook notification listener.
Isi yang diharapkan:
- APIRouter untuk /api/v1/payments
- Endpoints: create_snap_token, midtrans_webhook_handler
"""
''',
    "src/modules/payments/payment_service.py": '''"""
Modul: Payments Service
Fungsi:
- Logika komunikasi ke Midtrans, verifikasi signature webhook, dan update status transaksi.
Isi yang diharapkan:
- PaymentService class
- Metode: create_transaction, process_webhook_notification, check_transaction_status
"""
''',
    "src/modules/payments/payment_repository.py": '''"""
Modul: Payments Repository
Fungsi:
- Akses database untuk riwayat pembayaran, log transaksi payment gateway, dan invoice.
Isi yang diharapkan:
- PaymentRepository class
- Metode: record_payment_log, update_payment_status, get_by_transaction_id
"""
''',
    "src/modules/payments/payment_model.py": '''"""
Modul: Payments Model
Fungsi:
- Definisi tabel database transaksi pembayaran dan log webhook.
Isi yang diharapkan:
- PaymentTransaction model, PaymentLog model
- PaymentStatusEnum, PaymentMethodEnum
"""
''',
    "src/modules/payments/payment_schema.py": '''"""
Modul: Payments Schema
Fungsi:
- Validasi data transaksi pembayaran dan payload webhook Midtrans.
Isi yang diharapkan:
- PaymentRequestSchema, SnapTokenResponse, MidtransWebhookPayload
"""
''',

    # src/modules/notifications
    "src/modules/notifications/notification_service.py": '''"""
Modul: Notifications Service
Fungsi:
- Layanan terpusat untuk pengiriman notifikasi Email (invoice/link download) & WhatsApp blast/alert.
Isi yang diharapkan:
- NotificationService class
- Metode: send_order_receipt_email, send_digital_product_delivery, send_whatsapp_order_alert
"""
''',
    "src/modules/notifications/notification_templates.py": '''"""
Modul: Notification Templates
Fungsi:
- Template teks pesan WhatsApp dan HTML email untuk berbagai tipe notifikasi transaksi.
Isi yang diharapkan:
- Template email checkout & receipt HTML
- Template pesan WhatsApp konfirmasi pembayaran & pengiriman link download
"""
''',

    # src/utils
    "src/utils/formatters.py": '''"""
Modul: Formatters Helper
Fungsi:
- Fungsi utilitas untuk pemformatan data (Rupiah currency, tanggal Indonesia, sanitasi string).
Isi yang diharapkan:
- format_rupiah(amount: int | float) -> str
- format_date_id(date_obj) -> str
"""
''',
    "src/utils/generators.py": '''"""
Modul: Generators Helper
Fungsi:
- Generator kode unik (Nomor Invoice, kode lisensi, random slug/token).
Isi yang diharapkan:
- generate_invoice_number() -> str
- generate_secure_token(length: int) -> str
"""
''',

    # src/main.py
    "src/main.py": '''"""
Entry Point Utama Aplikasi
Fungsi:
- Inisialisasi framework (FastAPI / web framework), registrasi middleware, dan routing semua modul.
Isi yang diharapkan:
- app = FastAPI(...)
- Registrasi Router (auth, users, products, orders, payments)
- Event handler startup & shutdown
"""
''',

    # tests
    "tests/conftest.py": '''"""
Modul: Test Configuration & Fixtures
Fungsi:
- Konfigurasi testing environment, mock database session, dan test client (Pytest).
Isi yang diharapkan:
- Fixture test_client, db_session, mock_services
"""
''',

    # root files
    ".env.example": '''# Application Config
APP_NAME=haisen-store-backend
APP_ENV=development
APP_PORT=8000
SECRET_KEY=your-super-secret-key-change-me

# Database (Supabase / PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/haisen_store

# Midtrans Payment Gateway
MIDTRANS_SERVER_KEY=your-midtrans-server-key
MIDTRANS_CLIENT_KEY=your-midtrans-client-key
MIDTRANS_IS_PRODUCTION=false

# Email Provider (SMTP / Resend / SendGrid)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@example.com
SMTP_PASSWORD=your-app-password

# WhatsApp Gateway (Fonnte / Watzap)
WA_GATEWAY_URL=https://api.fonnte.com/send
WA_GATEWAY_TOKEN=your-whatsapp-token
''',

    "Dockerfile": '''# Dockerfile untuk haisen-store-backend
# Multi-stage build atau slim runtime Python
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',

    "requirements.txt": '''# Core Framework & Server
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0

# Database & ORM
sqlalchemy>=2.0.28
asyncpg>=0.29.0
alembic>=1.13.1

# Security & Authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.1.2

# HTTP Client & Integrasi (Midtrans, Mailer, WA)
httpx>=0.27.0
requests>=2.31.0

# Testing
pytest>=8.1.1
pytest-asyncio>=0.23.5
'''
}

def main():
    created = []
    for rel_path, content in FILES.items():
        abs_path = os.path.join(BASE_DIR, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(rel_path)
    print(f"Sukses membuat {len(created)} file dan folder.")

if __name__ == "__main__":
    main()
