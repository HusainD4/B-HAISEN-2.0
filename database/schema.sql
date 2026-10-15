-- ==============================================================================
-- DATABASE SCHEMA & INITIAL DDL QUERIES
-- Project: HAISEN OFFICIAL STORE - Digital Products & Services
-- Database Engine: PostgreSQL 14+ (UUID & JSONB Support)
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. RBAC (Roles & Permissions)
-- ==========================================

CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_roles_slug ON roles(slug);

CREATE TABLE IF NOT EXISTS permissions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(100) NOT NULL UNIQUE,
    module VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_permissions_code ON permissions(code);
CREATE INDEX IF NOT EXISTS ix_permissions_module ON permissions(module);

CREATE TABLE IF NOT EXISTS role_permissions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    role_id VARCHAR(36) NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id VARCHAR(36) NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS ix_role_permissions_permission_id ON role_permissions(permission_id);

-- ==========================================
-- 2. Users & Session Tokens
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(25),
    address TEXT,
    province VARCHAR(100),
    city VARCHAR(100),
    district VARCHAR(100),
    postal_code VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    role_id VARCHAR(36) REFERENCES roles(id) ON DELETE SET NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS ix_users_is_deleted ON users(is_deleted);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens(token_hash);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_token_hash ON password_reset_tokens(token_hash);

-- ==========================================
-- 3. Product Catalog & Digital Assets
-- ==========================================

CREATE TABLE IF NOT EXISTS product_categories (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    icon_url VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_product_categories_slug ON product_categories(slug);

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    category_id VARCHAR(36) REFERENCES product_categories(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(160) NOT NULL UNIQUE,
    short_description VARCHAR(300),
    description TEXT NOT NULL,
    banner_image_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    gallery_images JSONB DEFAULT '[]'::jsonb,
    base_price INTEGER NOT NULL DEFAULT 0,
    discount_price INTEGER,
    product_type VARCHAR(20) NOT NULL DEFAULT 'digital',
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    meta_title VARCHAR(150),
    meta_description VARCHAR(255),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_products_slug ON products(slug);
CREATE INDEX IF NOT EXISTS ix_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS ix_products_is_featured ON products(is_featured);
CREATE INDEX IF NOT EXISTS ix_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS ix_products_is_deleted ON products(is_deleted);

CREATE TABLE IF NOT EXISTS product_variants (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    product_id VARCHAR(36) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    variant_image_url VARCHAR(500),
    price INTEGER NOT NULL,
    discount_price INTEGER,
    stock INTEGER,
    license_type VARCHAR(50) DEFAULT 'standard',
    digital_file_key VARCHAR(500),
    digital_file_name VARCHAR(255),
    digital_file_size INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_product_variants_sku ON product_variants(sku);
CREATE INDEX IF NOT EXISTS ix_product_variants_product_id ON product_variants(product_id);

-- ==========================================
-- 4. Cart & Orders
-- ==========================================

CREATE TABLE IF NOT EXISTS cart_items (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id VARCHAR(36) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_id VARCHAR(36) NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_cart_items_user_id ON cart_items(user_id);

CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    order_number VARCHAR(40) NOT NULL UNIQUE,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(150) NOT NULL,
    customer_phone VARCHAR(25),
    total_amount INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    payment_method VARCHAR(50),
    notes TEXT,
    shipping_address TEXT,
    shipping_province VARCHAR(100),
    shipping_city VARCHAR(100),
    shipping_district VARCHAR(100),
    shipping_postal_code VARCHAR(10),
    shipping_cost INTEGER NOT NULL DEFAULT 0,
    courier VARCHAR(50),
    courier_service VARCHAR(50),
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS ix_orders_customer_email ON orders(customer_email);
CREATE INDEX IF NOT EXISTS ix_orders_status ON orders(status);

CREATE TABLE IF NOT EXISTS order_items (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    order_id VARCHAR(36) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id VARCHAR(36) REFERENCES products(id) ON DELETE SET NULL,
    variant_id VARCHAR(36) REFERENCES product_variants(id) ON DELETE SET NULL,
    product_name VARCHAR(150) NOT NULL,
    variant_name VARCHAR(100) NOT NULL,
    variant_image_url VARCHAR(500),
    price INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    subtotal INTEGER NOT NULL,
    license_type VARCHAR(50),
    digital_file_key VARCHAR(500)
);
CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items(order_id);

-- ==========================================
-- 5. Payments & Webhooks
-- ==========================================

CREATE TABLE IF NOT EXISTS payment_transactions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    order_id VARCHAR(36) NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    midtrans_transaction_id VARCHAR(100),
    payment_type VARCHAR(50) NOT NULL,
    gross_amount INTEGER NOT NULL,
    transaction_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    fraud_status VARCHAR(50),
    qr_string TEXT,
    qr_code_url VARCHAR(500),
    bank VARCHAR(30),
    va_number VARCHAR(50),
    bill_key VARCHAR(50),
    biller_code VARCHAR(50),
    expiry_time TIMESTAMPTZ,
    raw_response JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_payment_transactions_order_id ON payment_transactions(order_id);
CREATE INDEX IF NOT EXISTS ix_payment_transactions_midtrans_id ON payment_transactions(midtrans_transaction_id);
CREATE INDEX IF NOT EXISTS ix_payment_transactions_status ON payment_transactions(transaction_status);

CREATE TABLE IF NOT EXISTS payment_webhook_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    order_id VARCHAR(100),
    transaction_status VARCHAR(50),
    signature_valid BOOLEAN NOT NULL DEFAULT FALSE,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_payment_webhook_logs_order_id ON payment_webhook_logs(order_id);

-- ==========================================
-- 6. DEFAULT SEED DATA (ROLES & PERMISSIONS)
-- ==========================================

INSERT INTO roles (id, name, slug, description, is_system) VALUES
    ('role-superadmin-0000-000000000001', 'Superadmin', 'superadmin', 'Akses penuh ke seluruh modul sistem dan konfigurasi', TRUE),
    ('role-admin-0000-0000000000000002', 'Admin', 'admin', 'Pengelolaan produk, pesanan, dan verifikasi pengguna', TRUE),
    ('role-finance-0000-0000000000000003', 'Finance', 'finance', 'Akses laporan keuangan dan rekonsiliasi pembayaran', TRUE),
    ('role-staff-0000-00000000000000004', 'Staff / CS', 'staff', 'Layanan bantuan customer service dan status pesanan', TRUE),
    ('role-user-0000-000000000000000005', 'User', 'user', 'Pelanggan toko untuk berbelanja dan unduh aset digital', TRUE)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO permissions (id, name, code, module, description) VALUES
    ('perm-user-read-0001', 'Lihat Pengguna', 'user:read', 'users', 'Melihat daftar dan profil pengguna'),
    ('perm-user-manage-0002', 'Kelola Pengguna', 'user:manage', 'users', 'Membuat, mengubah, atau menghapus pengguna'),
    ('perm-role-manage-0003', 'Kelola Role & Akses', 'role:manage', 'auth', 'Mengatur hak akses dan role dinamis'),
    ('perm-product-create-0004', 'Buat Produk & Upload', 'product:create', 'products', 'Menambah produk, upload media banner & aset'),
    ('perm-product-update-0005', 'Ubah Produk', 'product:update', 'products', 'Memperbarui katalog, varian & harga produk'),
    ('perm-product-delete-0006', 'Hapus Produk', 'product:delete', 'products', 'Menghapus produk & varian'),
    ('perm-order-read-all-0007', 'Lihat Seluruh Pesanan', 'order:read_all', 'orders', 'Melihat semua riwayat transaksi customer'),
    ('perm-payment-manage-0008', 'Kelola Pembayaran', 'payment:manage', 'payments', 'Rekonsiliasi dan sinkronisasi status pembayaran')
ON CONFLICT (code) DO NOTHING;

-- Superadmin Memiliki Seluruh Permissions
INSERT INTO role_permissions (id, role_id, permission_id)
SELECT uuid_generate_v4()::text, 'role-superadmin-0000-000000000001', p.id
FROM permissions p
ON CONFLICT DO NOTHING;

-- Admin: user:read, user:manage, product:create, product:update, product:delete, order:read_all, payment:manage
INSERT INTO role_permissions (id, role_id, permission_id)
SELECT uuid_generate_v4()::text, 'role-admin-0000-0000000000000002', p.id
FROM permissions p
WHERE p.code IN ('user:read', 'user:manage', 'product:create', 'product:update', 'product:delete', 'order:read_all', 'payment:manage')
ON CONFLICT DO NOTHING;

-- Finance: order:read_all, payment:manage
INSERT INTO role_permissions (id, role_id, permission_id)
SELECT uuid_generate_v4()::text, 'role-finance-0000-0000000000000003', p.id
FROM permissions p
WHERE p.code IN ('order:read_all', 'payment:manage')
ON CONFLICT DO NOTHING;

-- Staff: order:read_all, user:read
INSERT INTO role_permissions (id, role_id, permission_id)
SELECT uuid_generate_v4()::text, 'role-staff-0000-00000000000000004', p.id
FROM permissions p
WHERE p.code IN ('order:read_all', 'user:read')
ON CONFLICT DO NOTHING;
