import os
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from io import StringIO, BytesIO
import zipfile

# === CONFIG ===
EXCEL_PATH = "realized_weather.xlsx"
STATION = '330'

# === LOAD EXISTING FILE OR START NEW ===
if os.path.exists(EXCEL_PATH):
    df_existing = pd.read_excel(EXCEL_PATH)
    df_existing["datetime"] = pd.to_datetime(df_existing["datetime"])
    if df_existing["Q"].notna().any():
        latest_dt = df_existing[df_existing["Q"].notna()]["datetime"].max()
        print(f"📘 Laatste geldige Q-timestamp: {latest_dt}")
else:
    df_existing = pd.DataFrame(columns=["datetime", "T", "Q", "SQ", "U", "FF", "# STN", "YYYYMMDD", "HH"])
    latest_dt = datetime(2023, 1, 1)
    print("📕 Geen bestaand bestand gevonden. Nieuw bestand zal worden aangemaakt.")

# === DETERMINE PERIOD TO DOWNLOAD ===
start_date = latest_dt.date()
end_date = datetime.now(timezone.utc).date()
print(f"📅 Downloadperiode: {start_date} t/m {end_date}")

# === KNMI POST REQUEST ===
url = "https://www.daggegevens.knmi.nl/klimatologie/uurgegevens"

payload = {
    'start': start_date.strftime('%Y%m%d'),
    'end': end_date.strftime('%Y%m%d'),
    'stns': STATION,
    'fmt': 'csv'
}
response = requests.post(url, data=payload)
content_type = response.headers.get("Content-Type", "")

# === KNMI kolomnamen (volgens documentatie)
knmi_columns = [
    "STN", "YYYYMMDD", "HH", "DD", "FH", "FF", "FX", "T", "T10N", "TD", "SQ", "Q", "DR",
    "RH", "P", "VV", "N", "U", "WW", "IX", "M", "R", "S", "O", "Y"
]

# === PARSE RESPONSE (TXT or ZIP)
def parse_knmi_lines(text_lines):
    lines = [l for l in text_lines if not l.startswith('#')]
    if not lines:
        raise ValueError("Geen datarijen gevonden in KNMI-bestand.")

    df = pd.read_csv(StringIO('\n'.join(lines)), sep=',', header=None)
    df.columns = knmi_columns[:len(df.columns)]
    print("📄 Ingelezen kolommen:", df.columns.tolist())

    # Bereken datetime (HH - 1 om correct uurvak te krijgen)
    df["YYYYMMDD"] = df["YYYYMMDD"].astype(str)
    df["HH"] = df["HH"].astype(int).apply(lambda h: h - 1 if h > 0 else 0)
    df["datetime"] = pd.to_datetime(df["YYYYMMDD"], format="%Y%m%d") + pd.to_timedelta(df["HH"], unit="h")

    # Selecteer relevante kolommen
    df_out = pd.DataFrame()
    df_out["# STN"] = df["STN"]
    df_out["YYYYMMDD"] = df["YYYYMMDD"]
    df_out["HH"] = df["HH"]
    df_out["FF"] = df["FF"]
    df_out["T"] = df["T"] / 10.0 if "T" in df.columns else None
    df_out["SQ"] = df["SQ"]
    df_out["Q"] = df["Q"]
    df_out["U"] = df["U"]
    df_out["datetime"] = df["datetime"]

    return df_out

if "text" in content_type:
    df_new = parse_knmi_lines(response.text.splitlines())

elif "zip" in content_type:
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        file_name = z.namelist()[0]
        with z.open(file_name) as f:
            text_lines = f.read().decode("utf-8").splitlines()
            df_new = parse_knmi_lines(text_lines)

else:
    print("❌ Onbekend bestandstype ontvangen van KNMI")
    print(response.text[:500])
    raise Exception("KNMI gaf geen bruikbare data terug.")

# === FILTER & APPEND ===
df_new = df_new[df_new["datetime"] > latest_dt]
if df_new.empty:
    print("⚠️ Geen nieuwe records gevonden.")
else:
    print(f"✅ {len(df_new)} nieuwe rijen gevonden")

    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset="datetime").sort_values("datetime")

# === AANVULLEN TOT HUIDIG UUR ===
now_rounded = datetime.now().replace(minute=0, second=0, microsecond=0)
last_in_combined = df_combined["datetime"].max()
expected_range = pd.date_range(start=last_in_combined + timedelta(hours=1), end=now_rounded, freq="h")

if not expected_range.empty:
    df_missing = pd.DataFrame({
        "datetime": expected_range,
        "T": [None] * len(expected_range),
        "Q": [None] * len(expected_range),
        "SQ": [None] * len(expected_range),
        "U": [None] * len(expected_range),
        "FF": [None] * len(expected_range),
        "# STN": [STATION] * len(expected_range),
        "YYYYMMDD": [dt.strftime("%Y%m%d") for dt in expected_range],
        "HH": [dt.hour for dt in expected_range],
    })

    df_combined = pd.concat([df_combined, df_missing], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset="datetime").sort_values("datetime")
    print(f"🕐 {len(df_missing)} lege uren toegevoegd tot {now_rounded}")

# === SAVE TO EXCEL ===
df_combined.to_excel(EXCEL_PATH, index=False)
print(f"💾 Bestand geüpdatet t/m {df_combined['datetime'].max()} ✅")
