from fastapi import FastAPI
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import requests
import database 
from engine import analisa_saham 
import socket
import time

app = FastAPI()

# --- 1. PENGAMAN ANTI-MACET (WAJIB ADA) ---
# Jika 3 detik tidak ada respon, POTONG KONEKSI!
socket.setdefaulttimeout(3) 

# --- LOAD DATABASE ---
def update_database_saham():
    print("⏳ Sedang memuat database saham...")
    # Coba load online dulu
    try:
        url = "https://raw.githubusercontent.com/eschben/idx-companies/main/data/companies.json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Filter saham 4 huruf
            saham_list = [item['symbol'] + ".JK" for item in data if len(item['symbol']) == 4]
            print(f"✅ DATA ONLINE: {len(saham_list)} Saham siap dipantau.")
            return saham_list
    except:
        pass
    # Fallback ke lokal
    print(f"✅ DATA LOKAL: {len(database.semua_saham)} Saham siap dipantau.")
    return database.semua_saham

LIST_SAHAM_AKTIF = update_database_saham()

@app.get("/")
def home():
    return {"status": "Server Ready (Fast Mode)"}

@app.get("/scan")
def scan_dashboard(min_price: int = 50, max_price: int = 100000):
    dashboard_data = {
        "ara": [], "scalping": [], "bsjp": [], "accumulation": []
    }
    
    total_saham = len(LIST_SAHAM_AKTIF)
    print(f"🚀 Scanning {total_saham} saham... (Timeout 3 Detik)")
    
    def process_ticker(data):
        index, ticker = data
        # Print setiap saham biar kelihatan jalan atau macet
        # Gunakan 'end=\r' biar barisnya tidak menuhin layar
        if index % 5 == 0: # Print tiap 5 saham biar gak pusing
            print(f"👉 [{index}/{total_saham}] Cek {ticker}...", end="\r")
        
        try:
            hasil = analisa_saham(ticker) 
            if not hasil: return None
            if hasil['harga'] < min_price or hasil['harga'] > max_price: return None
            return hasil
        except Exception as e:
            # Kalau error/timeout, LANGSUNG LEWATI. Jangan ditunggu.
            return None

    # Siapkan data dengan nomor urut
    target_scan = list(enumerate(LIST_SAHAM_AKTIF))

    # Gunakan 20 Worker biar ngebut (karena kita sudah punya timeout, aman)
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(process_ticker, target_scan)
        
        for hasil in results:
            if hasil:
                if "ARA" in hasil['kategori']: dashboard_data['ara'].append(hasil)
                if "SCALPING" in hasil['kategori']: dashboard_data['scalping'].append(hasil)
                if "BSJP" in hasil['kategori']: dashboard_data['bsjp'].append(hasil)
                if "ACCUMULATION" in hasil['info_paus']: dashboard_data['accumulation'].append(hasil)

    print(f"\n✅ Scan Selesai! Mengirim data ke HP...")
    return dashboard_data

@app.get("/cari")
def cari_saham(ticker: str):
    print(f"🔎 Mencari: {ticker}")
    kode_bersih = ticker.upper().replace(".JK", "") + ".JK"
    try:
        hasil = analisa_saham(kode_bersih, cek_spesifik=True)
        if hasil: return {"status": "found", "data": hasil}
        else: return {"status": "not_found"}
    except:
        return {"status": "error"}

if __name__ == "__main__":
    uvicorn.run("api_saham:app", host="127.0.0.1", port=8000, reload=True)