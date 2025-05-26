import streamlit as st
from datetime import date, datetime, time, timedelta

st.set_page_config(page_title="Growlitics", layout="wide")

def round_time_to_nearest_15(dt: datetime) -> time:
    discard = timedelta(minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond)
    dt -= discard
    if discard >= timedelta(minutes=7.5):
        dt += timedelta(minutes=15)
    return dt.time()

# --- Wizard State ---
if "step" not in st.session_state:
    st.session_state.step = 0

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
    </style>
""", unsafe_allow_html=True)

# --- Layout: Left = Wizard, Right = Image ---
left_col, right_col = st.columns([2, 1], gap="medium")

with left_col:
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("logo.png", width=100)
    with col2:
        st.markdown("## **Growlitics**")
        st.markdown("AI-driven lighting optimization for greenhouses")

    st.markdown("---")

    # --- Crop selection before the wizard ---
    if "crop" not in st.session_state:
        st.subheader("🌿 Select Your Crop")
    
        col1, col2 = st.columns(2)
    
        with col1:
            if st.button("🌼 Chrysant", use_container_width=True):
                st.session_state.crop = "Chrysant"
                st.session_state.step = 0
    
        with col2:
            if st.button("🌺 Gerbera", use_container_width=True):
                st.session_state.crop = "Gerbera"
                st.session_state.step = 0
    
        st.stop()  # Wait until crop is selected

    step = st.session_state.step

    def dimming_column():
        return st.column_config.TextColumn(
            "% dimmen",
            validate=r"^([0-9]|[1-9][0-9]|100)%?$"
        )

    if step == 0:
        st.subheader("🏡 Step 1: Greenhouse Settings")
        st.session_state.transmission = st.number_input("Transmission (%)", 40, 100, 75)
        st.session_state.lighting_type = st.selectbox("Lighting Type", ["LED", "SON-T", "Hybrid"])
        st.session_state.lighting_intensity = st.number_input("Lighting Intensity (µmol/m²/s)", 0, 2000, 200)
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("🔄 Crop", type="secondary"):
                del st.session_state["crop"]
                st.rerun()
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 1:
        st.subheader("🌱 Step 2: Crop Info")
        st.session_state.cultivar = st.selectbox("Cultivar", ["Baltica", "Zembla", "Delianne", "Other"])
        st.session_state.plant_date = st.date_input("Plant Date", date.today())
        st.session_state.cultivation_length = st.number_input("Cultivation Length (days)", 1, 120, 56)
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 2:
        st.subheader("🌞 Step 3a: Long Day Settings")
        st.session_state.long_days = st.number_input("Long Days (days)", 0, 16, 11)
        st.session_state.long_day_start = st.number_input("Long Day Start (hour)", 0, 23, 6)
        st.session_state.long_day_end = st.number_input("Long Day End (hour)", 0, 23, 22)
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
            use_container_width=True,
            key="long_day_rad_editor"
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
            key="long_day_energy_editor"
        )
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 5:
        st.subheader("🌑 Step 4a: Short Day Settings")
        st.session_state.short_day_start = st.number_input("Short Day Start (hour)", 0, 23, 7)
        st.session_state.short_day_end = st.number_input("Short Day End (hour)", 0, 23, 19)
        st.session_state.plant_density = st.number_input("Plant Density (#/m²)", 10, 100, 50)
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
            key="short_day_rad_editor"
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
            key="short_day_energy_editor"
        )
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 8:
        st.subheader("💰 Step 5: Economic Targets")
        expected_price = st.number_input("Crop Price (€ / plant)", 0.0, 10.0, 0.50, 0.01)
        target_weight = st.number_input("Target Weight (g)", 0, 500, 70)
        bonus = st.number_input("Bonus (€ / g)", 0.0, 1.0, 0.02, 0.001)
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 9:
        st.subheader("🕒 Step 6: Simulation Timing")
        st.session_state.sim_date = st.date_input("Simulation Date", date.today())
        st.session_state.sim_time = st.time_input("Simulation Time", value=round_time_to_nearest_15(datetime.now()))
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

# --- Right Column: Responsive Wrapper ---
with right_col:
    st.markdown('<div class="right-column">', unsafe_allow_html=True)
    st.image("GH_image.png", use_container_width=True, output_format="auto")
    st.markdown('</div>', unsafe_allow_html=True)
