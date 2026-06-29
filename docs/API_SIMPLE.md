# OrbitaConnect Mini API — Dokumentasi

## Base URL
```
http://localhost:8000
```

---

## Endpoint 1 — POST /ingest
**Dipakai oleh:** Supplier  
**Fungsi:** Kirim data hotel, daftar harga, dan ketersediaan kamar

### Request Body (JSON)
```json
{
  "supplier_id": "SUP-001",
  "external_hotel_id": "HTL-01",
  "name": "Grand Hotel Jakarta",
  "rates": [
    {
      "room_type": "Deluxe",
      "price": 850000,
      "valid_from": "2026-06-01",
      "valid_to": "2026-06-30"
    },
    {
      "room_type": "Suite",
      "price": 1500000,
      "valid_from": "2026-06-01",
      "valid_to": "2026-06-30"
    }
  ],
  "availability": [
    { "room_type": "Deluxe", "date": "2026-06-15", "rooms_left": 5 },
    { "room_type": "Suite",  "date": "2026-06-15", "rooms_left": 2 }
  ]
}
```

### Response Sukses (200)
```json
{
  "status": "ok",
  "hotel_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "rates_processed": 2,
  "availability_processed": 2
}
```

### Response Error (400) — tanggal terbalik
```json
{
  "detail": "Rate 'Deluxe': valid_from (2026-07-01) tidak boleh setelah valid_to (2026-06-01)"
}
```

### Response Error (503) — database mati
```json
{
  "detail": "Database tidak bisa dihubungi"
}
```

---

## Endpoint 2 — GET /hotels
**Dipakai oleh:** Guest  
**Fungsi:** Lihat daftar hotel, harga, dan stok kamar

### Query Parameter (Opsional)
| Parameter | Tipe   | Contoh       | Keterangan                          |
|-----------|--------|--------------|-------------------------------------|
| `date`    | string | `2026-06-15` | Filter hotel yang tersedia di tanggal ini |

### Contoh Request — tanpa filter
```
GET /hotels
```

### Contoh Request — dengan filter tanggal
```
GET /hotels?date=2026-06-15
```

### Response (200)
```json
{
  "status": "ok",
  "filter_date": "2026-06-15",
  "total": 2,
  "hotels": [
    {
      "hotel_name": "Grand Hotel Jakarta",
      "room_type": "Deluxe",
      "price": 850000.00,
      "currency": "IDR",
      "rooms_left": 5,
      "available_date": "2026-06-15"
    },
    {
      "hotel_name": "Grand Hotel Jakarta",
      "room_type": "Suite",
      "price": 1500000.00,
      "currency": "IDR",
      "rooms_left": 2,
      "available_date": "2026-06-15"
    }
  ]
}
```

---

## Endpoint 3 — GET /health
**Fungsi:** Cek status koneksi database

### Response Sukses (200)
```json
{ "status": "ok", "database": "connected" }
```

### Response Error (503)
```json
{ "detail": "Database tidak bisa dihubungi" }
```

---

## Cara Test dengan curl (3 Menit)

```bash
# 1. Cek health dulu
curl http://localhost:8000/health

# 2. Supplier: ingest data hotel
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": "SUP-001",
    "external_hotel_id": "HTL-01",
    "name": "Grand Hotel Jakarta",
    "rates": [
      {"room_type":"Deluxe","price":850000,"valid_from":"2026-06-01","valid_to":"2026-06-30"}
    ],
    "availability": [
      {"room_type":"Deluxe","date":"2026-06-15","rooms_left":5}
    ]
  }'

# 3. Guest: lihat hotel tersedia
curl "http://localhost:8000/hotels?date=2026-06-15"

# 4. Kirim payload yang sama lagi → tidak error (idempotent)
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": "SUP-001",
    "external_hotel_id": "HTL-01",
    "name": "Grand Hotel Jakarta",
    "rates": [
      {"room_type":"Deluxe","price":850000,"valid_from":"2026-06-01","valid_to":"2026-06-30"}
    ],
    "availability": [
      {"room_type":"Deluxe","date":"2026-06-15","rooms_left":5}
    ]
  }'
```
