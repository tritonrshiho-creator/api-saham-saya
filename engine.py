import yfinance as yf
import pandas as pd
import pandas_ta as ta

def analisa_saham(ticker, cek_spesifik=False):
    # Rapikan kode ticker
    if not ticker.endswith(".JK"):
        ticker += ".JK"
    
    stock = yf.Ticker(ticker)
    
    # 1. AMBIL DATA HISTORIS
    try:
        hist = stock.history(period="6mo", interval="1d")
        if hist.empty: return None
    except:
        return None

    # Data Harga & Volume
    current_close = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2]
    change_pct = ((current_close - prev_close) / prev_close) * 100
    volume = hist['Volume'].iloc[-1]
    avg_volume = hist['Volume'].mean()

    # Hitung TP1 (Perbaikan bug null)
    tp1 = int(current_close * 1.03) # Target cuan 3%

    # Indikator Teknikal
    hist['MA20'] = ta.sma(hist['Close'], length=20)
    hist['MA50'] = ta.sma(hist['Close'], length=50)
    hist['RSI'] = ta.rsi(hist['Close'], length=14)

    ma20 = hist['MA20'].iloc[-1]
    ma50 = hist['MA50'].iloc[-1]
    rsi = hist['RSI'].iloc[-1]

    kategori = []
    info_tambahan = ""

    # --- TAHAP 1: SCREENING TEKNIKAL ---
    if change_pct >= 20:
        kategori.append("ARA")
    elif change_pct >= 2 and volume > (avg_volume * 1.2):
        kategori.append("SCALPING")
    elif 1 <= change_pct < 3:
         kategori.append("BSJP")

    is_swing = (current_close > ma20) and (ma20 > ma50)
    if is_swing:
        kategori.append("SWING")

    # --- TAHAP 2: SCREENING FUNDAMENTAL (REVISI) ---
    # Kita tidak lagi mewajibkan SWING. Semua dicek tapi pakai try-except ketat.
    
    try:
        # Trik: Ambil info ringan dulu biar server gak berat
        # Kita pakai standard yang lebih longgar untuk Bluechip
        info = stock.info 
        per = info.get('trailingPE', 99) 
        pbv = info.get('priceToBook', 99)
        roe = info.get('returnOnEquity', 0)

        info_tambahan = f"PER: {round(per,1)}x | PBV: {round(pbv,1)}x"

        # KRITERIA BARU (LEBIH LONGGAR):
        # PER < 20 (Sebelumnya 15)
        # PBV < 2.5 (Sebelumnya 1.5) -> Biar saham bank masuk
        # ROE > 5% (Perusahaan untung)
        if (0 < per < 20) and (pbv < 2.5) and (roe > 0.05):
            kategori.append("UNDERVALUED")
            
            # Kalau Undervalued DAN Swing = JACKPOT
            if is_swing:
                kategori.append("SUPER_STAR")
    except:
        pass 

    # Filter: Tampilkan hanya jika ada kategori ATAU pencarian spesifik
    if not cek_spesifik and not kategori:
        return None

    return {
        "ticker": ticker.replace(".JK", ""),
        "harga": int(current_close),
        "persen": round(change_pct, 2),
        "change": round(change_pct, 2), # Cadangan biar gak null
        "tp1": tp1, # Fix bug null
        "kategori": kategori,
        "info_paus": info_tambahan if info_tambahan else f"Vol: {round(volume/1000000,1)}M"
    }