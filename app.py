import streamlit as st
from datetime import date, datetime, time, timedelta
import pandas as pd
import os
import pathlib
import tempfile
import subprocess
import requests
import base64

SAVE_DIR = pathlib.Path("saved_strategies")
SAVE_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Growlitics", layout="wide")

def safe_int(val, default):
    try:
        if pd.isna(val): return default
        return int(float(val))
    except Exception: return default

def safe_float(val, default):
    try:
        if pd.isna(val): return default
        return float(val)
    except Exception: return default

# --- Time Rounding ---
def round_time_to_nearest_15(dt: datetime) -> time:
    discard = timedelta(minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond)
    dt -= discard
    if discard >= timedelta(minutes=7.5):
        dt += timedelta(minutes=15)
    return dt.time()

def dimming_column():
    return st.column_config.TextColumn(
        "% dimmen",
        validate=r"^([0-9]|[1-9][0-9]|100)%?$"
    )

def commit_to_github(filename: str, content: bytes, commit_msg="Add strategy file"):
    GH_TOKEN = st.secrets["GH_TOKEN"]
    REPO = "growlitics/growlitics"
    BRANCH = "main"
    PATH = f"saved_strategies/{filename}"

    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Check if file exists to get SHA
    get_url = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
    resp = requests.get(get_url, headers=headers, params={"ref": BRANCH})
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    # Prepare content
    put_data = {
        "message": commit_msg,
        "branch": BRANCH,
        "content": base64.b64encode(content).decode("utf-8"),
    }
    if sha:
        put_data["sha"] = sha  # Include for updates

    put_resp = requests.put(get_url, headers=headers, json=put_data)
                
def save_user_settings_sidebar():
    with st.sidebar:
        st.markdown("### 💾 Save This Strategy")
        with st.form("save_strategy_form", clear_on_submit=False):
            strategy_name = st.text_input("Name this strategy before saving:", key="save_strategy_name")
            submit = st.form_submit_button("📁 Save Strategy Settings to GitHub")

            if submit:
                if not strategy_name.strip():
                    st.warning("⚠️ Please enter a strategy name before saving.")
                    return
                user_settings = {
                    "crop": st.session_state.get("crop"),
                    "transmission": st.session_state.get("transmission"),
                    "lighting_type": st.session_state.get("lighting_type"),
                    "lighting_intensity": st.session_state.get("lighting_intensity"),
                    "plant_density": st.session_state.get("plant_density"),
                    "plant_date": str(st.session_state.get("plant_date")),
                    "long_days": st.session_state.get("long_days"),
                    "long_day_dark_screen_rad": st.session_state.get("long_day_dark_screen_rad"),
                    "long_day_dark_screen_percentage": st.session_state.get("long_day_dark_screen_percentage"),
                    "long_day_energy_screen_rad": st.session_state.get("long_day_energy_screen_rad"),
                    "long_day_energy_screen_percentage": st.session_state.get("long_day_energy_screen_percentage"),
                    "short_days": st.session_state.get("short_days"),
                    "short_day_dark_screen_rad": st.session_state.get("short_day_dark_screen_rad"),
                    "short_day_dark_screen_percentage": st.session_state.get("short_day_dark_screen_percentage"),
                    "short_day_energy_screen_temp_dif": st.session_state.get("short_day_energy_screen_temp_dif"),
                    "short_day_energy_screen_rad": st.session_state.get("short_day_energy_screen_rad"),
                    "short_day_energy_screen_percentage": st.session_state.get("short_day_energy_screen_percentage"),
                    "target_weight": st.session_state.get("target_weight"),
                    "taxes": st.session_state.get("taxes"),
                    "expected_price": st.session_state.get("expected_price"),
                    "bonus": st.session_state.get("bonus"),
                    "penalty": st.session_state.get("penalty"),
                    "sim_date": str(st.session_state.get("sim_date")),
                    "sim_time": str(st.session_state.get("sim_time")),
                }
                filename = SAVE_DIR / f"{strategy_name.strip()}.xlsx"
                pd.DataFrame([user_settings]).to_excel(filename, index=False)

                try:
                    with open(filename, "rb") as f:
                        commit_to_github(filename.name, f.read(), commit_msg=f"Save strategy {filename.name}")
                except Exception as e:
                    st.error(f"❌ Commit to GitHub failed: {e}")
            
# --- Load User Settings ---
def load_user_settings():
    GH_TOKEN = st.secrets["GH_TOKEN"]
    headers = {"Authorization": f"token {GH_TOKEN}"}
    api_url = "https://api.github.com/repos/growlitics/growlitics/contents/saved_strategies"

    resp = requests.get(api_url, headers=headers)
    files = [f["name"] for f in resp.json() if f["name"].endswith(".xlsx")]

    if files:
        selected_file = st.selectbox("📂 Load existing strategy", files)
        if st.button("📤 Load Strategy"):
            raw_url = f"https://raw.githubusercontent.com/growlitics/growlitics/main/saved_strategies/{selected_file}"
            import io
            resp = requests.get(raw_url)
            df = pd.read_excel(io.BytesIO(resp.content))  # <-- FIXED
            for col in df.columns:
                st.session_state[col] = df[col].iloc[0]
            st.success(f"✅ Loaded settings from `{selected_file}`")
    else:
        st.info("No saved strategies found in GitHub.")

# --- Wizard State ---
if "step" not in st.session_state:
    st.session_state.step = 0

# --- Navigation ---
def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

# --- Style ---
st.markdown("""
    <style>
        @media (max-width: 768px) {
            .right-column {
                display: none !important;
            }
            .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        }
        @media (min-width: 769px) {
            .right-column {
                display: block;
            }
        }

        html, body, [data-testid="stApp"] {
            overflow: hidden;
            height: 100vh;
        }
        .main .block-container {
            padding-right: 0 !important;
        }

        div.stButton {
            width: 100%;
        }
        div.stButton > button {
            width: 100%;
            background-color: #34a853;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 24px;
            font-size: 16px;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- Layout ---
left_col = st.container()

with left_col:
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("logo.png", width=100)
    with col2:
        st.markdown("## **Growlitics**")
        st.markdown("AI-driven lighting optimization for greenhouses")

    st.markdown("---")

    # --- Password prefill ---
    if "crop" not in st.session_state:
        if "prefill_done" not in st.session_state:
            with st.expander("\U0001F510 Optional: Enter Access Password to preload settings"):
                with st.form("password_form"):
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Submit Password")

                    if submitted:
                        if password == "roadmap":
                            st.session_state.prefill_done = True
                            st.session_state.show_full_roadmap = True
                            #st.session_state.show_roadmap = True
                            st.rerun()
                       # elif password == "full_roadmap":
                       #     st.session_state.prefill_done = True
                       #     st.session_state.show_full_roadmap = True
                       #     st.rerun()
                        elif password == "guest":
                            st.session_state.crop = "Chrysant"
                            st.session_state.transmission = 70
                            st.session_state.lighting_type = "LED"
                            st.session_state.lighting_intensity = 180
                            excel_path = f"{password}.xlsx"
                            if os.path.exists(excel_path):
                                try:
                                    df = pd.read_excel(excel_path)
                                    if not df.empty:
                                        st.session_state.excel_data = df
                                        st.session_state.use_excel = True
                                    else:
                                        st.warning("Excel file is empty.")
                                        st.session_state.use_excel = False
                                except Exception as e:
                                    st.warning(f"\u26A0\ufe0f Excel file failed to load: {e}")
                                    st.session_state.use_excel = False
                            else:
                                st.info("\u2139\ufe0f No Excel file found.")
                                st.session_state.use_excel = False

                            st.session_state.step = 0
                            st.session_state.prefill_done = True
                            st.rerun()
                        else:
                            st.error("Invalid password")

                if st.button("Skip"):
                    st.session_state.prefill_done = True
                    st.rerun()

            st.stop()

    if "crop" not in st.session_state:
        if st.session_state.get("show_full_roadmap", False):
            st.markdown("<h2 style='text-align:center;'>\U0001F9ED Full Growlitics Roadmap</h2>", unsafe_allow_html=True)
            st.image("Phase_all.png", use_container_width =True)
            st.stop()
        if st.session_state.get("show_roadmap", False):
            st.markdown("<h2 style='text-align:center;'>\U0001F9ED Growlitics Roadmap</h2>", unsafe_allow_html=True)

            phase_images = ["phase1.png", "phase2.png", "phase3.png", "phase4.png"]
            phase_titles = ["Phase 1: Simulate until today", "Phase 2: Forecast & Strategy", "Phase 3: Simulation", "Phase 4: AI Optimization"]

            cols = st.columns(4)
            for i in range(4):
                with cols[i]:
                    st.image(phase_images[i], use_container_width =True)
                    st.markdown(f"<div style='text-align:center; font-weight:bold'>{phase_titles[i]}</div>", unsafe_allow_html=True)

            st.markdown("<br><hr><div style='text-align:center;'>\u2B05\ufe0f Refresh or use the sidebar to exit this view.</div>", unsafe_allow_html=True)
            st.stop()

        st.subheader("🌿 Select Your Crop")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌼 Chrysant", use_container_width =True):
                st.session_state.crop = "Chrysant"
                st.session_state.step = 0
        with col2:
            if st.button("🌺 Gerbera", use_container_width =True):
                st.session_state.crop = "Gerbera"
                st.session_state.step = 0
        st.stop()

    step = st.session_state.step
    with st.sidebar:
        st.markdown("### 🔁 Load a Saved Strategy")
        load_user_settings()
    if step == 0:
        if st.session_state.get("use_excel", False):
            st.subheader("📅 Step 1: Select Planning Info from QMS")
            current_year = date.today().year
    
            # --- Widget persistence using session_state ---
            st.session_state.rondejaar = st.selectbox(
                "Rondejaar",
                list(range(current_year, current_year - 6, -1)),
                index=list(range(current_year, current_year - 6, -1)).index(
                    st.session_state.get("rondejaar", current_year)
                ) if st.session_state.get("rondejaar", current_year) in list(range(current_year, current_year - 6, -1)) else 0,
                key="ronde_jaar"
            )
            st.session_state.rondenummer = st.number_input(
                "Rondenummer", 1, 100,
                value=int(st.session_state.get("rondenummer", 1)),
                key="selected_rondenummer"
            )
            st.session_state.vak = st.number_input(
                "Vak", 1, 100,
                value=int(st.session_state.get("vak", 1)),
                key="selected_vak"
            )
    
            ronde_key = f"Ronde {st.session_state.rondejaar}-{st.session_state.rondenummer}"
            vak_value = st.session_state.vak
            df = st.session_state.excel_data
            matched = df[(df["Ronde"] == ronde_key) & (df["Vak"] == vak_value)]
    
            if not matched.empty:
                if len(matched) == 1:
                    st.success("✅ Using loaded planting data")
                    st.dataframe(matched)
                    st.session_state.selected_row = matched.iloc[0].to_dict()
                else:
                    st.warning("⚠️ Multiple matches found. Please select cultivar to continue.")
                    options = matched["Cultivar"].unique().tolist()
                    # Widget persistence for Cultivar selection
                    st.session_state.selected_cultivar = st.selectbox(
                        "Select Cultivar",
                        options,
                        index=options.index(st.session_state.get("selected_cultivar", options[0])) if st.session_state.get("selected_cultivar") in options else 0,
                        key="selectedcultivar"
                    )
                    filtered = matched[matched["Cultivar"] == st.session_state.selected_cultivar]
                    if not filtered.empty:
                        st.success("✅ Selection complete")
                        st.dataframe(filtered)
                        st.session_state.selected_row = filtered.iloc[0].to_dict()
            else:
                st.warning("⚠️ No matching row found in Excel file for given Ronde and Vak.")


        else:
            st.subheader("🏡 Step 1: Greenhouse Settings")
            st.session_state.transmission = st.number_input(
                "Transmission (%)", 40, 100,
                value=st.session_state.get("transmission", 75), key="selected__transmission"
            )
            st.session_state.lighting_type = st.selectbox(
                "Lighting Type", ["LED", "SON-T", "Hybrid"],
                index=["LED", "SON-T", "Hybrid"].index(st.session_state.get("lighting_type", "LED")),
                key="selected_lighting_type"
            )
            st.session_state.lighting_intensity = st.number_input(
                "Lighting Intensity (µmol/m²/s)", 0, 2000,
                value=st.session_state.get("lighting_intensity", 200), key="selected_lighting_intensity"
            )
        col_prev, col_next = st.columns(2)
        with col_prev:
            if not st.session_state.get("use_excel", False):
                if st.button("🔄 Crop", type="secondary"):
                    del st.session_state["crop"]
                    st.rerun()
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 1:
        st.subheader("🌱 Step 2: Crop Info")

        row = st.session_state.get("selected_row", {})

        default_density = float(row.get("[#/m²]", 50))
        try:
            year, week, day = int(row["Plantdatum_jaar"]), int(row["Plantdatum_W"]), int(row["Plantdatum_D"])
            default_date = datetime.strptime(f"{year}-W{week}-{day}", "%G-W%V-%u").date()
        except:
            default_date = date.today()

        # --- Inject custom CSS if values came from Excel ---
        css = "<style>"
        if "[#/m²]" in row:
            css += """
                div[data-testid="stNumberInput"] input[type='number'] {
                    color: green !important;
                }
            """
        if all(k in row for k in ["Plantdatum_jaar", "Plantdatum_W", "Plantdatum_D"]):
            css += """
                div[data-testid="stDateInput"] input {
                    color: green !important;
                }
            """
        css += "</style>"
        st.markdown(css, unsafe_allow_html=True)

        # --- Inputs (Cultivar removed) ---
        st.session_state.plant_density = st.number_input(
            "Plant Density (#/m²)", 10.0, 100.0,
            value=float(st.session_state.get("plant_density", default_density)),
            step=0.1, format="%.1f", key="selected_plant_density"
        )
        st.session_state.plant_date = st.date_input(
            "Plant Date", value=st.session_state.get("plant_date", default_date), key="selected_plant_date"
        )

        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 2:
        st.subheader("🌞 Step 3a: Long Day Settings")

        row = st.session_state.get("selected_row", {})
        default_long_days = int(row.get("Lange Dagen", 11))

        st.session_state.long_days = st.number_input(
            "Long Days", 0, 16,
            value=int(st.session_state.get("long_days", default_long_days)), key="selected_long_days"
        )
        st.session_state.long_day_start = st.number_input(
            "Long Day Start Lighting (hour)", 0, 23,
            value=int(st.session_state.get("long_day_start", 6)), key="selected_long_day_start"
        )
        st.session_state.long_day_end = st.number_input(
            "Long Day End Lighting (hour)", 0, 23,
            value=int(st.session_state.get("long_day_end", 22)), key="selected_long_day_end"
        )
        
        st.markdown("🌞 Long Day Dark Screen Settings")
        st.session_state.long_day_dark_screen_rad = st.number_input(
            "Straling (Watt)", 0, 1000,
            value=int(st.session_state.get("long_day_dark_screen_rad", 500)), key="selected_long_day_dark_screen_rad"
        )
        st.session_state.long_day_dark_screen_percentage = st.number_input(
            "percentage dicht (%)", 0, 100,
            value=int(st.session_state.get("long_day_dark_screen_percentage", 95)), key="selected_long_day_dark_screen_percentage"
        )
        
        st.markdown("🌞 Long Day Energy Screen Settings")
        st.session_state.long_day_energy_screen_rad = st.number_input(
            "Straling (Watt)", 0, 1000,
            value=int(st.session_state.get("long_day_energy_screen_rad", 0)), key="selected_long_day_energy_screen_rad"
        )
        st.session_state.long_day_energy_screen_percentage = st.number_input(
            "percentage dicht (%)", 0, 100,
            value=int(st.session_state.get("long_day_energy_screen_percentage", 0)), key="selected_long_day_energy_screen_percentage"
        )

        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 3:
        st.subheader("🌞 Step 3b: Long Day Table Radiation")
        if "long_day_rad_table" not in st.session_state:
            st.session_state.long_day_rad_table = [
                {"Stralingsniveau": 800, "% dimmen": "100%"},
                {"Stralingsniveau": 600, "% dimmen": "50%"},
                {"Stralingsniveau": 500, "% dimmen": "20%"},
                *[{"Stralingsniveau": 0, "% dimmen": ""} for _ in range(2)]
            ]
        st.session_state.long_day_rad_table = st.data_editor(
            st.session_state.long_day_rad_table,
            column_config={
                "Stralingsniveau": st.column_config.NumberColumn("Stralingsniveau", step=50),
                "% dimmen": dimming_column()
            },
            num_rows="dynamic",
            use_container_width =True,
            key="selected_long_day_rad_editor"
        )
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 4:
        st.subheader("🌞 Step 3c: Long Day Table Energy")
        if "long_day_energy_table" not in st.session_state:
            st.session_state.long_day_energy_table = [
                {"Energieprijs per KwH": 0.35, "% dimmen": "100%"},
                {"Energieprijs per KwH": 0.25, "% dimmen": "50%"},
                {"Energieprijs per KwH": 0.20, "% dimmen": "20%"},
                *[{"Energieprijs per KwH": 0.0, "% dimmen": ""} for _ in range(2)]
            ]
        st.session_state.long_day_energy_table = st.data_editor(
            st.session_state.long_day_energy_table,
            column_config={
                "Energieprijs per KwH": st.column_config.NumberColumn("Energieprijs per KwH", format="%.2f"),
                "% dimmen": dimming_column()
            },
            num_rows="dynamic",
            use_container_width=True,
            key="selected_long_day_energy_editor"
        )
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 5:
        st.subheader("🌑 Step 4a: Short Day Settings")

        row = st.session_state.get("selected_row", {})
        default_short_days = int(row.get("# Netto-reactietijd", 56))

        st.session_state.short_days = st.number_input(
            "# Short days", 1, 120,
            value=int(st.session_state.get("short_days", default_short_days)), key="selected_short_days"
        )
        st.session_state.short_day_start = st.number_input(
            "Short Day Start Lighting (hour)", 0, 23,
            value=int(st.session_state.get("short_day_start", 7)), key="selected_short_day_start"
        )
        st.session_state.short_day_end = st.number_input(
            "Short Day End Lighting (hour)", 0, 23,
            value=int(st.session_state.get("short_day_end", 19)), key="selected_short_day_end"
        )
        
        st.markdown("🌑 Short Day Dark Screen Settings")
        st.session_state.short_day_dark_screen_rad = st.number_input(
            "Straling (Watt)", 0, 1000,
            value=int(st.session_state.get("short_day_dark_screen_rad", 700)), key="selected_short_day_dark_screen_rad"
        )
        st.session_state.short_day_dark_screen_percentage = st.number_input(
            "percentage dicht (%)", 0, 100,
            value=int(st.session_state.get("short_day_dark_screen_percentage", 70)), key="selected_short_day_dark_screen_percentage"
        )
        st.markdown("🌑 Short Day Energy Screen Settings")
        st.session_state.short_day_energy_screen_temp_dif = st.number_input(
            "Temp dif. inside > outside (C)", 0, 15,
            value=int(st.session_state.get("short_day_energy_screen_temp_dif", 8)), key="selected_short_day_energy_screen_temp_dif"
        )
        st.session_state.short_day_energy_screen_percentage = st.number_input(
            "percentage dicht (%)", 0, 100,
            value=int(st.session_state.get("short_day_energy_screen_percentage", 100)), key="selected_short_day_energy_screen_percentage"
        )
        st.session_state.short_day_energy_screen_rad = st.number_input(
            "Radiation outside (Watt)", 0, 250,
            value=int(st.session_state.get("short_day_energy_screen_rad", 120)), key="selected_short_day_energy_screen_rad"
        )
        st.session_state.short_day_energy_screen_percentage = st.number_input(
            "percentage dicht (%)", 0, 100, 
            value=int(st.session_state.get("percentage dicht (%)", 0)), key="selected_percentage dicht (%)"
            )

        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 6:
        st.subheader("🌑 Step 4b: Short Day Table Radiation")
        if "short_day_rad_table" not in st.session_state:
            st.session_state.short_day_rad_table = [
                {"Stralingsniveau": 800, "% dimmen": "100%"},
                {"Stralingsniveau": 600, "% dimmen": "50%"},
                {"Stralingsniveau": 500, "% dimmen": "20%"},
                *[{"Stralingsniveau": 0, "% dimmen": ""} for _ in range(2)]
            ]
        st.session_state.short_day_rad_table = st.data_editor(
            st.session_state.short_day_rad_table,
            column_config={
                "Stralingsniveau": st.column_config.NumberColumn("Stralingsniveau", step=50),
                "% dimmen": dimming_column()
            },
            num_rows="dynamic",
            use_container_width=True,
            key="selected_short_day_rad_editor"
        )
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 7:
        st.subheader("🌑 Step 4c: Short Day Table Energy")
        if "short_day_energy_table" not in st.session_state:
            st.session_state.short_day_energy_table = [
                {"Energieprijs per KwH": 0.35, "% dimmen": "100%"},
                {"Energieprijs per KwH": 0.25, "% dimmen": "50%"},
                {"Energieprijs per KwH": 0.20, "% dimmen": "20%"},
                *[{"Energieprijs per KwH": 0.0, "% dimmen": ""} for _ in range(2)]
            ]
        st.session_state.short_day_energy_table = st.data_editor(
            st.session_state.short_day_energy_table,
            column_config={
                "Energieprijs per KwH": st.column_config.NumberColumn("Energieprijs per KwH", format="%.2f"),
                "% dimmen": dimming_column()
            },
            num_rows="dynamic",
            use_container_width=True,
            key="selected_short_day_energy_editor"
        )
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 8:
        st.subheader("💰 Step 5: Economics")
        st.session_state.target_weight = st.number_input(
            "Target Weight (g)", 0, 500,
            value=safe_int(st.session_state.get("target_weight"), 70), key="selected_target_weight"
        )
        st.session_state.taxes = st.number_input(
            "Grid energy tax/delivery surcharge (€/kWh)", 0.00, 0.10,
            value=safe_float(st.session_state.get("taxes"), 0.05), step=0.01, key="selected_taxes"
        )
        st.session_state.expected_price = st.number_input(
            "Crop Price (€ / plant)", 0.0, 10.0,
            value=safe_float(st.session_state.get("expected_price"), 0.50), step=0.01, key="selected_expected_price"
        )
        st.session_state.bonus = st.number_input(
            "Bonus (€ / g)", 0.0, 1.0,
            value=safe_float(st.session_state.get("bonus"), 0.02), step=0.001, key="selected_bonus"
        )
        st.session_state.penalty = st.number_input(
            "Penalty (€ / g)", min_value=-1.0, max_value=0.0,
            value=safe_float(st.session_state.get("penalty"), -0.04), step=0.001, key="selected_penalty"
        )
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 9:
        st.subheader("🕒 Step 6: Simulation Timing")
        st.session_state.sim_date = st.date_input(
            "Simulation Date", value=st.session_state.get("sim_date", date.today()), key="selected_sim_date"
        )
        st.session_state.sim_time = st.time_input(
            "Simulation Time", value=st.session_state.get("sim_time", round_time_to_nearest_15(datetime.now())), key="selected_sim_time"
        )
        simulation_datetime = datetime.combine(st.session_state.sim_date, st.session_state.sim_time)
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            calculate_clicked = st.button("Calculate Light Intensity")

        if calculate_clicked:
            umol = 125.0 + st.session_state.long_days
            percent = min((umol / st.session_state.lighting_intensity) * 100, 100) if st.session_state.lighting_intensity > 0 else 0
            st.success("✅ Calculation Complete")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Light Intensity", f"{umol} µmol/m²/s")
            with col_b:
                st.metric("Relative Intensity", f"{percent:.1f}%")

        save_user_settings_sidebar()

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none !important;}
    </style>
""", unsafe_allow_html=True)
