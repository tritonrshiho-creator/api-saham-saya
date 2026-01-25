from fastapi import FastAPI
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import requests
import database 
from engine import analisa_saham 
import socket
import time

app = FastAPI()

# --- PENGAMAN ---
socket.setdefaulttimeout(3) 

# --- DATABASE RINGAN (Hanya Saham Pilihan) ---
# Kita batasi agar Server Gratisan tidak Timeout/Macet
def update_database_saham():
    # Daftar 60 Saham Paling Likuid & Sering Trading (Campuran Bluechip & Gorengan)
    saham_pilihan = [
        'BBRI.JK', 'BBCA.JK', 'BMRI.JK', 'BBNI.JK', 'TLKM.JK', 'ASII.JK', 'GOTO.JK', 'ANTM.JK', 'ADRO.JK', 'UNVR.JK',
        'ICBP.JK', 'INDF.JK', 'KLBF.JK', 'BRIS.JK', 'MDKA.JK', 'PGEO.JK', 'AMRT.JK', 'INKP.JK', 'PTBA.JK', 'MEDC.JK',
        'AKRA.JK', 'HRUM.JK', 'ITMG.JK', 'BUMI.JK', 'DEWA.JK', 'BREN.JK', 'TPIA.JK', 'BRPT.JK', 'SMGR.JK', 'INTP.JK',
        'GGRM.JK', 'HMSP.JK', 'SIDO.JK', 'MAPI.JK', 'ACES.JK', 'SCMA.JK', 'MNCN.JK', 'TOWR.JK', 'EXCL.JK', 'ISAT.JK',
        'CPIN.JK', 'JPFA.JK', 'EMTK.JK', 'ESSA.JK', 'MBMA.JK', 'NCKL.JK', 'UNTR.JK', 'BBTN.JK', 'BTPS.JK', 'SRTG.JK',
        'PANI.JK', 'PTMP.JK', 'WIFI.JK', 'FREN.JK', 'ELSA.JK', 'RAJA.JK', 'DOID.JK', 'ENRG.JK', 'LSIP.JK', 'DSNG.JK'
    ]
    print(f"✅ MODE RINGAN: Memantau {len(saham_pilihan)} Saham Terpopuler.")
    return saham_pilihan

LIST_SAHAM_AKTIF = update_database_saham()

@app.get("/")
def home():
    return {"status": "Server Ready (Light Mode)"}

@app.get("/scan")
def scan_dashboard(min_price: int = 50, max_price: int = 100000):
    dashboard_data = {
        "ara": [], "scalping": [], "bsjp": [], "accumulation": []
    }
    
    total_saham = len(LIST_SAHAM_AKTIF)
    print(f"🚀 Scanning {total_saham} saham... (Target Cepat)")
    
    def process_ticker(data):
        index, ticker = data
        # Print progress biar di log Render kelihatan jalan
        if index % 5 == 0: 
            print(f"👉 [{index+1}/{total_saham}] Cek {ticker}...")
        
        try:
            hasil = analisa_saham(ticker) 
            if not hasil: return None
            if hasil['harga'] < min_price or hasil['harga'] > max_price: return None
            return hasil
        except:
            return None

    target_scan = list(enumerate(LIST_SAHAM_AKTIF))

    # Gunakan 10 Worker (Cukup untuk 60 saham, selesai dalam ~10 detik)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(process_ticker, target_scan)
        
        for hasil in results:
            if hasil:
                if "ARA" in hasil['kategori']: dashboard_data['ara'].append(hasil)
                if "SCALPING" in hasil['kategori']: dashboard_data['scalping'].append(hasil)
                if "BSJP" in hasil['kategori']: dashboard_data['bsjp'].append(hasil)
                if "ACCUMULATION" in hasil['info_paus']: dashboard_data['accumulation'].append(hasil)

    print(f"✅ Scan Selesai! Mengirim data ke HP...")
    return dashboard_data

@app.get("/cari")
def cari_saham(ticker: str):
    # Fitur Cari tetap bisa cari SEMUA saham (bukan cuma yg 60 tadi)
    print(f"🔎 Mencari: {ticker}")
    kode_bersih = ticker.upper().replace(".JK", "") + ".JK"
    try:
        hasil = analisa_saham(kode_bersih, cek_spesifik=True)
        if hasil: return {"status": "found", "data": hasil}
        else: return {"status": "not_found"}
    except:
        return {"status": "error"}

if __name__ == "__main__":
    uvicorn.run("api_saham:app", host="0.0.0.0", port=8000)