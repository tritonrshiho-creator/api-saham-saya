import yfinance as yf
import pandas as pd
import pandas_ta as ta

def analisa_saham(ticker, cek_spesifik=False):
    # Rapikan kode ticker
    if not ticker.endswith(".JK"):
        ticker += ".JK"
    
    stock = yf.Ticker(ticker)
    
    # 1. AMBIL DATA HISTORIS (Cukup 6 bulan untuk Swing)
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

    # Indikator Teknikal (RSI & MA)
    hist['MA20'] = ta.sma(hist['Close'], length=20)
    hist['MA50'] = ta.sma(hist['Close'], length=50)
    hist['RSI'] = ta.rsi(hist['Close'], length=14)

    ma20 = hist['MA20'].iloc[-1]
    ma50 = hist['MA50'].iloc[-1]
    rsi = hist['RSI'].iloc[-1]

    kategori = []
    info_tambahan = ""

    # --- TAHAP 1: SCREENING TEKNIKAL (Cepat) ---
    
    # A. Logika Scalping (Liar)
    if change_pct >= 20:
        kategori.append("ARA")
    elif change_pct >= 2 and volume > (avg_volume * 1.2):
        kategori.append("SCALPING")
    elif 1 <= change_pct < 3:
         kategori.append("BSJP")

    # B. Logika Swing (Santai)
    # Syarat: Harga > MA20 > MA50 (Uptrend)
    is_swing_potential = (current_close > ma20) and (ma20 > ma50)

    if is_swing_potential:
        kategori.append("SWING")

    # --- TAHAP 2: SCREENING FUNDAMENTAL (Berat) ---
    # HANYA JALANKAN INI JIKA:
    # 1. User minta cek spesifik (Search)
    # 2. ATAU Sahamnya sudah lolos screening Swing (Biar gak buang waktu cek saham jelek)
    
    check_fundamental = cek_spesifik or ("SWING" in kategori)

    if check_fundamental:
        try:
            # Ini proses yang bikin berat, jadi kita batasi
            info = stock.info 
            per = info.get('trailingPE', 999) 
            pbv = info.get('priceToBook', 999)
            roe = info.get('returnOnEquity', 0)

            # Format Info biar enak dibaca
            info_tambahan = f"PER: {round(per,1)}x | PBV: {round(pbv,1)}x"

            # Logika Undervalued (Diskon)
            # PER < 15, PBV < 1.5, ROE Positif
            if (0 < per < 15) and (pbv < 1.5) and (roe > 0):
                kategori.append("UNDERVALUED")
                
                # JACKPOT: Sudah Swing (Uptrend) + Undervalued (Murah)
                if "SWING" in kategori:
                    kategori.append("SUPER_STAR") 

        except:
            info_tambahan = "Info Fundamental Gagal"

    # Filter Buang Data Kosong (Kecuali pencarian spesifik)
    if not cek_spesifik and not kategori:
        return None

    return {
        "ticker": ticker.replace(".JK", ""),
        "harga": int(current_close),
        "persen": round(change_pct, 2),
        "kategori": kategori,
        "info_paus": info_tambahan if info_tambahan else f"Vol: {round(volume/1000000,1)}M"
    }