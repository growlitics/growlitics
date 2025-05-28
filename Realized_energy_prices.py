# -*- coding: utf-8 -*-
"""
Created on Wed May 28 10:48:14 2025

@author: jarno
"""

import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# === CONFIGURATION ===
ENTSOE_TOKEN = "3595660d-f1c6-4479-b5e1-c763b2a28d13"
FILENAME = "realized_energy_prices.xlsx"
BIDDING_ZONE = "10YNL----------L"  # Netherlands

# === FETCH FUNCTION ===
def fetch_day_ahead_prices(date):
    start = date.strftime("%Y%m%d0000")
    end = (date + timedelta(days=1)).strftime("%Y%m%d0000")
    url = "https://web-api.tp.entsoe.eu/api"

    params = {
        "securityToken": ENTSOE_TOKEN,
        "documentType": "A44",
        "in_Domain": BIDDING_ZONE,
        "out_Domain": BIDDING_ZONE,
        "periodStart": start,
        "periodEnd": end
    }

    print(f"\n🔍 Fetching prices for {date.strftime('%Y-%m-%d')}...")

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        print("📄 Raw XML preview:")
        print(r.text[:500])  # Show first 500 characters
        print(f"✅ Response received (status {r.status_code}, {len(r.content)} bytes)")
    except requests.exceptions.Timeout:
        print(f"❌ Connection timed out trying to fetch data for {date}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch data: {e}")
        return pd.DataFrame()

    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        print(f"❌ XML Parse Error: {e}")
        return pd.DataFrame()

    prices = []
    ns = {'ns': 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3'}
    
    for pt in root.findall('.//ns:Point', ns):
        position = int(pt.find('ns:position', ns).text)
        price_eur_mwh = float(pt.find('ns:price.amount', ns).text)
        timestamp = datetime.combine(date, datetime.min.time()) + timedelta(hours=position - 1)
        prices.append({
            "Timestamp": timestamp,
            "Day-ahead (EUR/MWh)": round(price_eur_mwh / 1000, 5)
        })

    df = pd.DataFrame(prices)
    print(f"📈 Retrieved {len(df)} price points")
    if not df.empty:
        print(df.head(3).to_string(index=False))  # Show a preview of the first 3 rows

    return df


# === EXCEL APPENDER ===
def update_excel_file(prices_df, filename=FILENAME):
    try:
        existing = pd.read_excel(filename)

        # 🛡️ Clean legacy interval-format timestamps first
        if " - " in str(existing["Timestamp"].iloc[0]):
            existing["Timestamp"] = pd.to_datetime(
                existing["Timestamp"].astype(str).str.extract(r"^(.+?)\s+-")[0],
                dayfirst=True,
                errors="coerce"
            )
        else:
            existing["Timestamp"] = pd.to_datetime(existing["Timestamp"], errors="coerce")

        prices_df["Timestamp"] = pd.to_datetime(prices_df["Timestamp"], errors="coerce")

        # 🧹 Remove rows with broken timestamps (but warn)
        n_before = len(existing)
        existing = existing.dropna(subset=["Timestamp"])
        if len(existing) < n_before:
            print(f"⚠️ Dropped {n_before - len(existing)} rows with invalid existing timestamps")

        # 🧠 Merge safely
        combined = pd.concat([existing, prices_df])
        combined = combined.drop_duplicates(subset=["Timestamp"]).sort_values("Timestamp")

    except FileNotFoundError:
        combined = prices_df

    combined.to_excel(filename, index=False)
    print(f"✅ File '{filename}' updated safely with {len(prices_df)} new rows (total: {len(combined)})")


# === MAIN EXECUTION ===
def main():
    # Load existing data
    try:
        existing = pd.read_excel(FILENAME)
        if "Timestamp" in existing.columns:
            # Parse only the start time of the interval
            existing["Timestamp"] = pd.to_datetime(
                existing["Timestamp"].astype(str).str.extract(r"^(.+?)\s+-")[0],
                dayfirst=True,
                errors="coerce"  # makes sure invalid formats don't break the code
            )
        else:
            raise ValueError("Expected 'Timestamp' column.")
    except (FileNotFoundError, ValueError):
        existing = pd.DataFrame(columns=["Timestamp", "Day-ahead (EUR/MWh)"])

    # Determine where to resume
    if not existing.empty:
        last_date = existing["Timestamp"].max().date()
        rows_on_last_day = existing["Timestamp"].dt.date.eq(last_date).sum()
        if rows_on_last_day >= 24:
            start_date = last_date + timedelta(days=1)
        else:
            start_date = last_date  # try again from incomplete day
    else:
        start_date = datetime.today().date() - timedelta(days=30)

    # Determine end date
    today = datetime.today().date()
    end_date = today + timedelta(days=1) if datetime.now().hour >= 13 else today

    # Loop through days
    current_date = start_date
    while current_date <= end_date:
        df = fetch_day_ahead_prices(current_date)
        if not df.empty:
            update_excel_file(df)
        current_date += timedelta(days=1)

if __name__ == "__main__":
    main()
