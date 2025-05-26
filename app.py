import streamlit as st
from datetime import date, datetime, time

st.set_page_config(page_title="Growlytics", layout="wide")

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
        html, body, [data-testid="stApp"] {
            overflow: hidden;
            height: 100vh;
        }
        .main .block-container {
            padding-right: 0 !important;
        }
        div.stButton > button:first-child {
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
        st.markdown("## **Growlytics**")
        st.markdown("AI-driven lighting optimization for greenhouses")

    st.markdown("---")

    step = st.session_state.step

    if step == 0:
        st.subheader("🏡 Step 1: Greenhouse Settings")
        transmission = st.number_input("Transmission (%)", 40, 100, 75)
        lighting_type = st.selectbox("Lighting Type", ["LED", "SON-T", "Hybrid"])
        lighting_intensity = st.number_input("Lighting Intensity (µmol/m²/s)", 0, 2000, 200)
        st.button("Next ➡", on_click=next_step)

    elif step == 1:
        st.subheader("🌱 Step 2a: Crop Info")
        cultivar = st.selectbox("Cultivar", ["Baltica", "Zembla", "Delianne", "Other"])
        plant_date = st.date_input("Plant Date", date.today())
        cultivation_length = st.number_input("Cultivation Length (days)", 1, 120, 56)
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 2:
        st.subheader("🌞 Step 2b: Long Day Settings")
        long_days = st.number_input("Long Days (days)", 0, 16, 11)
        long_day_start = st.number_input("Long Day Start (hour)", 0, 23, 6)
        long_day_end = st.number_input("Long Day End (hour)", 0, 23, 22)
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 3:
        st.subheader("🌑 Step 2c: Short Day Settings")
        short_day_start = st.number_input("Short Day Start (hour)", 0, 23, 7)
        short_day_end = st.number_input("Short Day End (hour)", 0, 23, 19)
        plant_density = st.number_input("Plant Density (#/m²)", 10, 100, 50)
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)
            
    elif step == 4:
        st.subheader("🕒 Step 3: Simulation Timing")
        sim_date = st.date_input("Simulation Date", date.today())
        sim_time = st.time_input("Simulation Time", value=time(8, 0))
        simulation_datetime = datetime.combine(sim_date, sim_time)
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            st.button("⬅ Back", on_click=prev_step)
        with col_next:
            st.button("Next ➡", on_click=next_step)

    elif step == 5:
        st.subheader("💰 Step 4: Economic Targets")
        expected_price = st.number_input("Crop Price (€ / plant)", 0.0, 10.0, 0.50, 0.01)
        target_weight = st.number_input("Target Weight (g)", 0, 500, 70)
        bonus = st.number_input("Bonus (€ / g)", 0.0, 1.0, 0.02, 0.001)
        penalty = st.number_input("Penalty (€ / g)", -10.0, 0.0, -0.04, 0.001)

        if st.button("⬅ Back", on_click=prev_step):
            pass
        if st.button("Calculate Light Intensity"):
            umol = 125.0 + long_days
            percent = min((umol / lighting_intensity) * 100, 100) if lighting_intensity > 0 else 0
            st.success("✅ Calculation Complete")
            col_a, col_b = st.columns(2)
            col_a.metric("Light Intensity", f"{umol} µmol/m²/s")
            col_b.metric("Relative Intensity", f"{percent:.1f}%")

with right_col:
    st.image("GH_image.png", use_container_width=True, output_format="auto")
