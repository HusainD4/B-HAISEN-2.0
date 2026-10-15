# 1. Pindah ke direktori backend
cd backend

# 2. Aktifkan Virtual Environment (Windows)
.\venv\Scripts\Activate.ps1
# (Jika belum ada venv: python -m venv venv lalu jalankan aktivasi di atas)

# 3. Install dependensi
pip install -r requirements.txt

# 4. Salin file environment jika belum ada
Copy-Item .env.example .env
# (Pastikan nilai DATABASE_URL di .env mengarah ke database PostgreSQL Anda)

# 5. Buat akun Superadmin awal (1x pakai)
python scripts/generate_superadmin.py

# 6. Jalankan Server Development Uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
