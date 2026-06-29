"""
OrbitaConnect: Guest & Supplier Mini API
FastAPI + PostgreSQL
Endpoint:
POST   /ingest          → Supplier kirim data hotel, harga, ketersediaan
GET    /hotels          → Guest lihat daftar hotel (filter by date opsional)
GET    /hotels/list     → Daftar semua hotel (untuk manage panel)
PUT    /hotels/{id}     → Update nama hotel
DELETE /hotels/{id}     → Hapus hotel beserta rates & availability
GET    /health          → Cek koneksi database
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
import psycopg2
import psycopg2.extras
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OrbitaConnect Mini API",
    description="Guest & Supplier integration API untuk platform OTA",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ota_db_user:SecureP@ss2026!@ota-db:5432/orbitaconnect"
)

def get_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Gagal konek ke database: {e}")
        raise HTTPException(status_code=503, detail="Database tidak bisa dihubungi")

# ─── Models ──────────────────────────────────────────────────────────────────
class RateIn(BaseModel):
    room_type: str
    price: float = Field(..., ge=0)
    valid_from: date
    valid_to: date

class AvailIn(BaseModel):
    room_type: str
    date: date
    rooms_left: int = Field(..., ge=0)

class IngestPayload(BaseModel):
    supplier_id: str = Field(..., example="SUP-001")
    external_hotel_id: str = Field(..., example="HTL-01")
    name: str = Field(..., example="Grand Hotel Jakarta")
    rates: List[RateIn]
    availability: List[AvailIn]

class UpdateHotelPayload(BaseModel):
    name: str = Field(..., example="Grand Hotel Jakarta Updated")

# ─── Endpoint 1: Supplier Ingest ──────────────────────────────────────────────
@app.post("/ingest", summary="Supplier: Kirim data hotel, harga, dan stok")
def ingest(payload: IngestPayload):
    for r in payload.rates:
        if r.valid_from > r.valid_to:
            raise HTTPException(
                status_code=400,
                detail=f"Rate '{r.room_type}': valid_from tidak boleh setelah valid_to"
            )
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cur.execute("""
            INSERT INTO hotels (supplier_id, external_id, name, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (supplier_id, external_id)
            DO UPDATE SET name = EXCLUDED.name, updated_at = NOW()
            RETURNING id
        """, (payload.supplier_id, payload.external_hotel_id, payload.name))
        hotel_id = cur.fetchone()["id"]

        for r in payload.rates:
            cur.execute("""
                INSERT INTO rates (hotel_id, room_type, price, currency, valid_from, valid_to)
                VALUES (%s, %s, %s, 'IDR', %s, %s)
                ON CONFLICT (hotel_id, room_type, valid_from, valid_to) DO NOTHING
            """, (hotel_id, r.room_type, r.price, r.valid_from, r.valid_to))

        for a in payload.availability:
            cur.execute("""
                INSERT INTO availability (hotel_id, room_type, date, rooms_left, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (hotel_id, room_type, date)
                DO UPDATE SET rooms_left = EXCLUDED.rooms_left, updated_at = NOW()
            """, (hotel_id, a.room_type, a.date, a.rooms_left))

        conn.commit()
        return {
            "status": "ok",
            "hotel_id": str(hotel_id),
            "rates_processed": len(payload.rates),
            "availability_processed": len(payload.availability),
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ─── Endpoint 2: Guest View ───────────────────────────────────────────────────
@app.get("/hotels", summary="Guest: Lihat daftar hotel dan harga")
def list_hotels(
    date_filter: Optional[date] = Query(None, alias="date", description="Filter tanggal (YYYY-MM-DD)")
):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        if date_filter:
            cur.execute("""
                SELECT h.id::text AS hotel_id, h.name AS hotel_name,
                    r.room_type, r.price, r.currency,
                    a.rooms_left, a.date AS available_date
                 FROM hotels h
                JOIN rates r        ON r.hotel_id = h.id
                JOIN availability a ON a.hotel_id = h.id AND a.room_type = r.room_type
                WHERE r.valid_from <= %s AND r.valid_to >= %s
                  AND a.date = %s AND a.rooms_left > 0
                ORDER BY h.name, r.room_type
            """, (date_filter, date_filter, date_filter))
        else:
            cur.execute("""
                SELECT h.id::text AS hotel_id, h.name AS hotel_name,
                    r.room_type, r.price, r.currency,
                    a.rooms_left, a.date AS available_date
                 FROM hotels h
                JOIN rates r        ON r.hotel_id = h.id
                JOIN availability a ON a.hotel_id = h.id AND a.room_type = r.room_type
                ORDER BY h.name, r.room_type, a.date
            """)

        rows = cur.fetchall()
        return {
            "status": "ok",
            "filter_date": str(date_filter) if date_filter else None,
            "total": len(rows),
            "hotels": [dict(row) for row in rows],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ─── Endpoint 3: List Hotels (untuk Manage Panel) ─────────────────────────────
@app.get("/hotels/list", summary="Daftar semua hotel untuk manajemen")
def list_hotels_manage():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("""
            SELECT h.id::text, h.supplier_id, h.external_id, h.name, h.created_at, h.updated_at,
                COUNT(DISTINCT r.id) AS total_rates,
                COUNT(DISTINCT a.id) AS total_availability
            FROM hotels h 
            LEFT JOIN rates r ON r.hotel_id = h.id
            LEFT JOIN availability a ON a.hotel_id = h.id
            GROUP BY h.id, h.supplier_id, h.external_id, h.name, h.created_at, h.updated_at
            ORDER BY h.updated_at DESC
        """)
        rows = cur.fetchall()
        return {"status": "ok", "total": len(rows), "hotels": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ─── Endpoint 4: Update Hotel ─────────────────────────────────────────────────
@app.put("/hotels/{hotel_id}", summary="Update nama hotel")
def update_hotel(hotel_id: str, payload: UpdateHotelPayload):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("""
            UPDATE hotels SET name = %s, updated_at = NOW()
            WHERE id = %s::uuid RETURNING id, name
        """, (payload.name, hotel_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Hotel tidak ditemukan")
        conn.commit()
        return {"status": "ok", "hotel_id": str(row["id"]), "name": row["name"]}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ─── Endpoint 5: Delete Hotel ─────────────────────────────────────────────────
@app.delete("/hotels/{hotel_id}", summary="Hapus hotel beserta semua data terkait")
def delete_hotel(hotel_id: str):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("""
            DELETE FROM hotels WHERE id = %s::uuid RETURNING id, name
        """, (hotel_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Hotel tidak ditemukan")
        conn.commit()
        return {"status": "ok", "deleted_hotel": row["name"], "hotel_id": str(row["id"])}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ─── Endpoint 6: Health Check ─────────────────────────────────────────────────
@app.get("/health", summary="Cek status koneksi database")
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

# ── Root: Serve Frontend Dashboard ──────────────────────────────────────────
# Mount static files DI BAWAH semua endpoint agar tidak menabrak route API
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "app": "OrbitaConnect Mini API",
            "version": "1.0.0",
            "docs": "/docs",
            "message": "Frontend folder not found. Use /docs for API documentation."
        }