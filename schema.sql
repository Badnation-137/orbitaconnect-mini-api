-- ============================================================
-- OrbitaConnect: Schema PostgreSQL
-- Jalankan sekali di database: orbitaconnect
-- ============================================================

-- 1. Tabel Hotels
--    Menyimpan data hotel dari berbagai supplier
CREATE TABLE IF NOT EXISTS hotels (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id VARCHAR(100) NOT NULL,
    external_id VARCHAR(100) NOT NULL,
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (supplier_id, external_id)
);

-- 2. Tabel Rates
--    Menyimpan harga per tipe kamar dalam rentang tanggal
CREATE TABLE IF NOT EXISTS rates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id    UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    room_type   VARCHAR(100) NOT NULL,
    price       NUMERIC(15, 2) NOT NULL CHECK (price >= 0),
    currency    VARCHAR(10) NOT NULL DEFAULT 'IDR',
    valid_from  DATE NOT NULL,
    valid_to    DATE NOT NULL,
    CHECK (valid_from <= valid_to),
    UNIQUE (hotel_id, room_type, valid_from, valid_to)
);

-- 3. Tabel Availability
--    Menyimpan jumlah kamar tersedia per tanggal per tipe kamar
CREATE TABLE IF NOT EXISTS availability (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id    UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    room_type   VARCHAR(100) NOT NULL,
    date        DATE NOT NULL,
    rooms_left  INTEGER NOT NULL CHECK (rooms_left >= 0),
    updated_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (hotel_id, room_type, date)
);

-- ============================================================
-- Index untuk performa query Guest
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_rates_hotel_date   ON rates (hotel_id, valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_avail_hotel_date   ON availability (hotel_id, date);
CREATE INDEX IF NOT EXISTS idx_avail_room_date    ON availability (room_type, date);

-- ============================================================
-- Contoh data awal (opsional, bisa di-comment)
-- ============================================================
-- INSERT INTO hotels (supplier_id, external_id, name)
-- VALUES ('SUP-001', 'HTL-01', 'Grand Hotel Jakarta')
-- ON CONFLICT DO NOTHING;
