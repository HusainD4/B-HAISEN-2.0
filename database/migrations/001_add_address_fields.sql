-- ==============================================================================
-- MIGRATION 001: Add Address Fields to Users & Shipping to Orders
-- Project: HAISEN OFFICIAL STORE
-- Run this once on your Supabase SQL Editor
-- ==============================================================================

-- 1. Add address columns to users table
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS address        TEXT,
    ADD COLUMN IF NOT EXISTS province       VARCHAR(100),
    ADD COLUMN IF NOT EXISTS city           VARCHAR(100),
    ADD COLUMN IF NOT EXISTS district       VARCHAR(100),
    ADD COLUMN IF NOT EXISTS postal_code    VARCHAR(10);

-- 2. Add shipping & courier columns to orders table
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS shipping_address   TEXT,
    ADD COLUMN IF NOT EXISTS shipping_province  VARCHAR(100),
    ADD COLUMN IF NOT EXISTS shipping_city      VARCHAR(100),
    ADD COLUMN IF NOT EXISTS shipping_district  VARCHAR(100),
    ADD COLUMN IF NOT EXISTS shipping_postal_code VARCHAR(10),
    ADD COLUMN IF NOT EXISTS courier            VARCHAR(50),
    ADD COLUMN IF NOT EXISTS courier_service    VARCHAR(50),
    ADD COLUMN IF NOT EXISTS shipping_cost      BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS order_note         TEXT;

-- 3. Add product_type to products table
ALTER TABLE products
    ADD COLUMN IF NOT EXISTS product_type VARCHAR(20) NOT NULL DEFAULT 'physical'
        CHECK (product_type IN ('physical', 'digital', 'service'));

-- Done
SELECT 'Migration 001 applied successfully.' AS status;
