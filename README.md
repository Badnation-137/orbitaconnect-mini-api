# OrbitaConnect: Guest & Supplier Mini API

API sederhana untuk integrasi aplikasi OTA dengan cloud infrastructure.  
Fokus: **Supplier Ingest** + **Guest View** menggunakan FastAPI + PostgreSQL.

---

## Struktur Project

```
ota-mini-api/
├── main.py              # Semua endpoint API (FastAPI)
├── schema.sql           # Skema database PostgreSQL
├── requirements.txt     # Dependency Python
├── .env.example         # Template konfigurasi
├── docs/
│   └── API_SIMPLE.md    # Dokumentasi endpoint + contoh curl
└── README.md            # File ini
```

---

## Cara Setup (5 Menit)

### 1. Install dependency
```bash
pip install -r requirements.txt
```

### 2. Setup database
```bash
# Jalankan schema di database PostgreSQL kalian
psql -h ota-db -U ota_db_user -d orbitaconnect -f schema.sql
```

### 3. Konfigurasi .env
```bash
cp .env.example .env
# Edit DATABASE_URL sesuai koneksi kalian
```

### 4. Jalankan API
```bash
# Set env variable dulu
export DATABASE_URL="postgresql://ota_db_user:SecureP@ss2026!@ota-db:5432/orbitaconnect"

# Jalankan server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Buka dokumentasi interaktif
```
http://localhost:8000/docs
```

---

## Endpoint Tersedia

| Method | Path       | Siapa     | Fungsi                        |
|--------|------------|-----------|-------------------------------|
| POST   | `/ingest`  | Supplier  | Kirim data hotel, harga, stok |
| GET    | `/hotels`  | Guest     | Lihat hotel & harga           |
| GET    | `/health`  | System    | Cek koneksi database          |

---

## Fitur Utama

- **Idempotent**: kirim data yang sama berkali-kali → tidak error, tidak duplikat
- **Upsert Hotel**: hotel diperbarui jika sudah ada (berdasarkan supplier_id + external_id)
- **Rate**: hanya di-insert jika belum ada (tidak menimpa harga lama)
- **Availability**: selalu diperbarui dengan stok terbaru
- **Filter tanggal**: `GET /hotels?date=2026-06-15` untuk cari yang tersedia

---

## Dokumentasi Lengkap

Lihat `docs/API_SIMPLE.md` untuk contoh request/response dan perintah curl lengkap.
