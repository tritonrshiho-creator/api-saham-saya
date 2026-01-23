import yfinance as yf

def deteksi_paus(vol_today, avg_vol, price_change, high, close):
    # Logika Jarum Suntik (Buang Sampah)
    upper_shadow = 0
    if high > 0:
        upper_shadow = (high - close) / close * 100
        
    if upper_shadow > 2.0:
        return "⚠️ RAWAN GUYUR (Jarum)"

    ratio = vol_today / avg_vol if avg_vol > 0 else 0
    status = "Netral"

    if ratio > 1.5 and -2 < price_change < 2:
        status = "ACCUMULATION (Silent)"
    elif ratio > 2.5 and price_change > 3:
        status = "ACCUMULATION (Big)"
    elif ratio > 2.0 and price_change < -2:
        status = "DISTRIBUTION"
        
    return status

def analisa_saham(ticker, cek_spesifik=False):
    try:
        t_obj = yf.Ticker(ticker)
        # Ambil data 10 hari terakhir
        df = t_obj.history(period="10d")
        
        if df.empty: return None

        data_today = df.iloc[-1]
        data_prev = df.iloc[-2]
        
        harga_skrg = int(data_today['Close'])
        harga_high = int(data_today['High'])
        harga_low = int(data_today['Low'])
        harga_open = int(data_today['Open'])
        
        avg_volume = df['Volume'].mean()
        vol_today = data_today['Volume']
        transaksi_value = harga_skrg * vol_today
        
        change_pct = ((data_today['Close'] - data_prev['Close']) / data_prev['Close']) * 100
        
        kategori = []
        
        # --- LOGIKA FILTER ---
        upper_shadow = 0
        if harga_high > 0:
            upper_shadow = (harga_high - harga_skrg) / harga_skrg * 100
        is_jarum_sampah = upper_shadow > 2.0
        
        # Filter Likuiditas (Minimal 500 Juta) - Kecuali kalau cari spesifik
        is_liquid = transaksi_value > 500_000_000 
        
        if not is_jarum_sampah:
            if change_pct > 5: kategori.append("ARA")
            # Strict BSJP
            if harga_open == harga_low and harga_skrg > harga_open:
                kategori.append("BSJP")
            if vol_today > (1.2 * avg_volume) and change_pct > 0.5:
                kategori.append("SCALPING")

        info_paus = deteksi_paus(vol_today, avg_volume, change_pct, harga_high, harga_skrg)
        if "RAWAN GUYUR" in info_paus: info_paus = "Netral"

        # Trading Plan
        cl = int(harga_skrg * 0.95)
        tp1 = int(harga_skrg * 1.03)
        tp2 = int(harga_skrg * 1.06)
        
        # Mode Pencarian (Search)
        if cek_spesifik:
            if not kategori and info_paus == "Netral":
                kategori.append("NETRAL / WAIT")
            return {
                "ticker": ticker.replace(".JK", ""),
                "harga": harga_skrg,
                "change": round(change_pct, 2),
                "kategori": kategori,
                "info_paus": info_paus,
                "cl": cl, "tp1": tp1, "tp2": tp2
                # FITUR BERITA DIHAPUS
            }

        # Mode Scan Massal
        if not is_liquid: return None 
        if not kategori and info_paus == "Netral": return None
            
        return {
            "ticker": ticker.replace(".JK", ""),
            "harga": harga_skrg,
            "change": round(change_pct, 2),
            "kategori": kategori,
            "info_paus": info_paus,
            "cl": cl, "tp1": tp1, "tp2": tp2
            # FITUR BERITA DIHAPUS
        }
    except:
        return None