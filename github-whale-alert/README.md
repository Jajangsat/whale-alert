# GitHub Actions Whale Price Alert

Gratis 24/7 price monitoring via GitHub Actions (2000 menit/bulan gratis).

## Setup (5 Menit)

### 1. Fork/Clone Repo
```bash
# Di GitHub, buat repo baru atau fork repo ini
git clone https://github.com/USERNAME/whale-alert.git
cd whale-alert
```

### 2. Copy File
Copy semua file ke repo kamu:
- `.github/workflows/whale_alert.yml`
- `check_prices.py`

### 3. Set Secrets GitHub

Di GitHub repo kamu:
1. **Settings** → **Secrets and variables** → **Actions**
2. Klik **New repository secret**
3. Tambah 2 secrets:

| Name | Value |
|------|-------|
| `BOT_TOKEN` | `8940968944:AAGxkASInSNxiFH-nhnUY3Bx95ucc3Tn3W4` |
| `CHAT_ID` | `2005620069` |

### 4. Commit & Push
```bash
git add .
git commit -m "Setup whale alert bot"
git push
```

### 5. Test Manual (Optional)
1. Ke tab **Actions** di repo GitHub
2. Klik workflow **Whale Price Alert**
3. Klik **Run workflow**
4. Tunggu ~1 menit

---

## Cara Kerja

```
┌─────────────────────────────────────────────────────┐
│  GitHub Actions (setiap 5 menit)                     │
├─────────────────────────────────────────────────────┤
│  1. Fetch harga dari CoinGecko (gratis)             │
│  2. Bandingkan dengan harga sebelumnya              │
│  3. Jika perubahan >= 5% → kirim alert ke Telegram  │
└─────────────────────────────────────────────────────┘
```

---

## Fitur

| Fitur | Status |
|-------|--------|
| Price alert ±5% | ✅ |
| Multi-token (BTC, ETH, BNB, SOL, dll) | ✅ |
| Cek setiap 5 menit | ✅ |
| Gratis 2000 menit/bulan | ✅ |
| No CC required | ✅ |

---

## Token yang Dimonitor

- BTC (Bitcoin)
- ETH (Ethereum)
- BNB (Binance Coin)
- SOL (Solana)
- MATIC (Polygon)
- ARB (Arbitrum)
- AVAX (Avalanche)
- LINK (Chainlink)
- UNI (Uniswap)
- SHIB (Shiba Inu)

---

## Custom Token

Edit `check_prices.py`, tambah token di `MONITOR_TOKENS`:

```python
MONITOR_TOKENS = [
    {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"},
    # Tambah di sini (gunakan CoinGecko ID)
    {"id": "nama-token-di-coingecko", "symbol": "SYM", "name": "Nama"},
]
```

Cari CoinGecko ID di: https://api.coingecko.com/api/v3/coins/list

---

## Troubleshooting

**Action tidak jalan?**
- Cek tab Actions → mungkin perlu enable workflow

**Alert tidak terkirim?**
- Cek secrets (BOT_TOKEN & CHAT_ID)
- Pastikan bot sudah di-start di Telegram

**Rate limit CoinGecko?**
- Free API: 10-50 calls/menit
- Kita cuma 1 call per 5 menit → aman

---

## Batasan

- ❌ Tidak real-time (cek per 5 menit)
- ❌ Tidak bisa whale tx on-chain (butuh server 24/7)
- ✅ Price alerts jalan gratis selamanya

---

## License

MIT
