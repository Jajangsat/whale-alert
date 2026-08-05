#!/usr/bin/env python3
"""
GitHub Actions Whale Price Alert
=================================
Checks crypto prices every 5 minutes and sends Telegram alerts
when price moves ±5% or more.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

import asyncio
import requests
from telegram import Bot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHAT_ID = os.environ.get('CHAT_ID', '')
PRICE_THRESHOLD = float(os.environ.get('PRICE_THRESHOLD', '5'))
ALWAYS_SEND = os.environ.get('ALWAYS_SEND', 'false').lower() == 'true'

# Tokens to monitor (CoinGecko IDs)
MONITOR_TOKENS = [
    {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"},
    {"id": "ethereum", "symbol": "ETH", "name": "Ethereum"},
    {"id": "binancecoin", "symbol": "BNB", "name": "BNB"},
    {"id": "solana", "symbol": "SOL", "name": "Solana"},
    {"id": "matic-network", "symbol": "MATIC", "name": "Polygon"},
    {"id": "arbitrum", "symbol": "ARB", "name": "Arbitrum"},
    {"id": "avalanche-2", "symbol": "AVAX", "name": "Avalanche"},
    {"id": "chainlink", "symbol": "LINK", "name": "Chainlink"},
    {"id": "uniswap", "symbol": "UNI", "name": "Uniswap"},
    {"id": "shiba-inu", "symbol": "SHIB", "name": "Shiba Inu"},
]

# State file for price history
STATE_FILE = "price_state.json"


def load_state():
    """Load previous price state"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_state(state):
    """Save current price state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def fetch_prices():
    """Fetch current prices from CoinGecko"""
    try:
        ids = ",".join([t["id"] for t in MONITOR_TOKENS])
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids,
            "order": "market_cap_desc",
            "sparkline": "false",
            "price_change_percentage": "1h,24h"
        }
        
        logger.info(f"Fetching prices for: {ids}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Fetched {len(data)} tokens")
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch prices: {e}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response: {e.response.text}")
        return None


def check_alerts(current_prices, previous_state):
    """Check for price alerts"""
    alerts = []
    new_state = {}
    
    for coin in current_prices:
        symbol = coin['symbol'].upper()
        price = coin['current_price']
        change_1h = coin.get('price_change_percentage_1h_in_currency', 0) or 0
        change_24h = coin.get('price_change_percentage_24h_in_currency', 0) or 0
        
        coin_id = coin['id']
        new_state[coin_id] = {
            "price": price,
            "time": datetime.now().isoformat()
        }
        
        # Check 1h change
        if abs(change_1h) >= PRICE_THRESHOLD:
            direction = "📈 NAIK" if change_1h > 0 else "📉 TURUN"
            alerts.append({
                "type": "1h",
                "symbol": symbol,
                "direction": direction,
                "change": change_1h,
                "price": price
            })
            logger.info(f"1h alert: {symbol} {direction} {change_1h:.2f}%")
        
        # Check if price moved significantly from last check
        if coin_id in previous_state:
            old_price = previous_state[coin_id].get("price", price)
            if old_price and old_price > 0:
                price_change_pct = ((price - old_price) / old_price) * 100
                
                if abs(price_change_pct) >= PRICE_THRESHOLD:
                    direction = "📈 NAIK" if price_change_pct > 0 else "📉 TURUN"
                    alerts.append({
                        "type": "5min",
                        "symbol": symbol,
                        "direction": direction,
                        "change": price_change_pct,
                        "price": price
                    })
                    logger.info(f"5min alert: {symbol} {direction} {price_change_pct:.2f}%")
    
    return alerts, new_state


async def send_alert(bot, chat_id, alert):
    """Send alert to Telegram"""
    emoji = "🔥" if abs(alert["change"]) > 10 else "⚡"
    
    msg = f"""{emoji} *PRICE ALERT* {emoji}
━━━━━━━━━━━━━━━━━━━━
*Token:* {alert['symbol']}
*Direction:* {alert['direction']}
*Change:* {alert['change']:+.2f}%
*Price:* ${alert['price']:,.6f}
*Timeframe:* {alert['type']}
━━━━━━━━━━━━━━━━━━━━
_Data: CoinGecko_"""
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="Markdown"
        )
        logger.info(f"Alert sent: {alert['symbol']} {alert['direction']} {alert['change']:.2f}%")
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")


async def send_summary(bot, chat_id, prices):
    """Send price summary"""
    lines = []
    for coin in prices:
        symbol = coin['symbol'].upper()
        price = coin['current_price']
        change = coin.get('price_change_percentage_24h', 0) or 0
        emoji = "📈" if change >= 0 else "📉"
        lines.append(f"{emoji} {symbol}: ${price:,.2f} ({change:+.2f}%)")
    
    msg = f"""📊 *Price Summary*\n\n""" + "\n".join(lines[:10]) + f"""\n\n_Data: CoinGecko | {datetime.now().strftime('%H:%M UTC')}_"""
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="Markdown"
        )
        logger.info("Summary sent")
        return True
    except Exception as e:
        logger.error(f"Failed to send summary: {e}")
        return False


def main():
    """Main function"""
    logger.info("=" * 50)
    logger.info("Starting price check...")
    
    # Validate config
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)
    
    if not CHAT_ID:
        logger.error("CHAT_ID not set!")
        sys.exit(1)
    
    logger.info(f"BOT_TOKEN: {'set' if BOT_TOKEN else 'missing'}")
    logger.info(f"CHAT_ID: {CHAT_ID}")
    logger.info(f"PRICE_THRESHOLD: {PRICE_THRESHOLD}%")
    logger.info(f"ALWAYS_SEND: {ALWAYS_SEND}")
    
    # Load previous state
    previous_state = load_state()
    logger.info(f"Loaded state with {len(previous_state)} tokens")
    
    # Fetch current prices
    prices = fetch_prices()
    if not prices:
        logger.error("Failed to fetch prices - exiting")
        sys.exit(1)
    
    # Check for alerts
    alerts, new_state = check_alerts(prices, previous_state)
    logger.info(f"Found {len(alerts)} alerts")
    
    # Initialize bot
    bot = Bot(token=BOT_TOKEN)
    
    # Send alerts if any
    if alerts:
        async def send_all_alerts():
            for alert in alerts:
                await send_alert(bot, CHAT_ID, alert)
        asyncio.run(send_all_alerts())
        logger.info(f"Sent {len(alerts)} alerts")
    
    # Always send summary if ALWAYS_SEND is true or first run
    if ALWAYS_SEND or len(previous_state) == 0:
        logger.info("Sending summary (ALWAYS_SEND=true or first run)")
        success = asyncio.run(send_summary(bot, CHAT_ID, prices))
        if success:
            logger.info("Summary sent successfully")
    
    # Save state
    save_state(new_state)
    logger.info("State saved")
    logger.info("Price check complete.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
