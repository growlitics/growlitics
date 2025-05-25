import streamlit as st
from datetime import date, datetime, time

st.set_page_config(page_title="Growlytics", layout="wide")

st.markdown("""
    <style>
        html, body, [data-testid="stApp"] {
            overflow: hidden;
            height: 100vh;
        }
        .main .block-container {
            padding-right: 0 !important;
        }
        .full-height-image {
            height: 100vh;
            object-fit: cover;
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

# --- Layout: Left = Content (logo, name, form), Right = Image ---
left_col, right_col = st.columns([2, 1], gap="medium")

def calculate_light_intensity(
    cultivar, plant_date, simulation_date, long_days, long_day_start, long_day_end,
    cultivation_length, short_day_start, short_day_end, plant_density,
    lighting_type, lighting_intensity, expected_price, target_weight, bonus, penalty
):
    umol = 125.0 + long_days
    percent = min((umol / lighting_intensity) * 100, 100) if lighting_intensity > 0 else 0
    return umol, percent

with left_col:
    # Header section
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("logo.png", width=100)
    with col2:
        st.markdown("## **Growlytics**")
        st.markdown("AI-driven lighting optimization for greenhouses")

    st.markdown("---")

    # Inputs
    st.subheader("🌿 Input Parameters")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Transmission")
    with col2:
        transmission = st.number_input("transmission", min_value=40, max_value=100, value=75, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Cultivar")
    with col2:
        cultivar = st.selectbox("cultivar", ["Baltica", "Zembla", "Delianne", "Other"], label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Plant Date")
    with col2:
        plant_date = st.date_input("plant_date", date.today(), label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Simulation Date")
    with col2:
        sim_date = st.date_input("simulation_date", date.today(), label_visibility="collapsed")
    
    col1, col2 = st.columns([1, 2])
    with col1: st.write("Simulation Time")
    with col2:
        sim_time = st.time_input("simulation_time", value=time(8, 0), label_visibility="collapsed")
    
    simulation_datetime = datetime.combine(sim_date, sim_time)

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Long Days (days)")
    with col2:
        long_days = st.number_input("long_days", min_value=0, max_value=16, value=11, label_visibility="collapsed")

    # Long Day Lighting Start and End
    col1, col2 = st.columns([1, 2])
    with col1: st.write("Long Day Start (hour)")
    with col2:
        long_day_start = st.number_input("long_day_start", min_value=0, max_value=23, value=6, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Long Day End (hour)")
    with col2:
        long_day_end = st.number_input("long_day_end", min_value=0, max_value=23, value=22, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Cultivation Length (days)")
    with col2:
        cultivation_length = st.number_input("length", min_value=1, value=56, label_visibility="collapsed")

    # Short Day Lighting Start and End
    col1, col2 = st.columns([1, 2])
    with col1: st.write("Short Day Start (hour)")
    with col2:
        short_day_start = st.number_input("short_day_start", min_value=0, max_value=23, value=7, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Short Day End (hour)")
    with col2:
        short_day_end = st.number_input("short_day_end", min_value=0, max_value=23, value=19, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Plant Density (#/m2)")
    with col2:
        plant_density = st.number_input("plant_density", min_value=45, value=50, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Lighting Type")
    with col2:
        lighting_type = st.selectbox("lighting", ["LED", "SON-T", "Hybrid"], label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Lighting Setup (µmol/m²/s)")
    with col2:
        lighting_intensity = st.number_input("intensity", min_value=0, value=200, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Crop Price (€ / plant)")
    with col2:
        expected_price = st.number_input("price", min_value=0.0, value=0.50, step=0.01, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Target Weight (g)")
    with col2:
        target_weight = st.number_input("target", min_value=0, value=70, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Bonus (€ / g)")
    with col2:
        bonus = st.number_input("bonus", min_value=0.0, max_value=1.0, value=0.02, step=0.001, label_visibility="collapsed")

    col1, col2 = st.columns([1, 2])
    with col1: st.write("Penalty (€ / g)")
    with col2:
        penalty = st.number_input("penalty", min_value=-10.0, max_value=0.0, value=-0.04, step=0.001, label_visibility="collapsed")

    # --- Calculate Button and Output Placeholder ---
    st.markdown("### 💡 Lighting Calculation")
    if st.button("Calculate Light Intensity"):
        umol, percent = calculate_light_intensity(
            cultivar, plant_date, simulation_datetime, long_days, long_day_start, long_day_end,
            cultivation_length, short_day_start, short_day_end, plant_density,
            lighting_type, lighting_intensity, expected_price, target_weight, bonus, penalty
        )

        st.success("✅ Calculation Complete")
        col_a, col_b = st.columns(2)
        col_a.metric("Light Intensity", f"{umol} µmol/m²/s")
        col_b.metric("Relative Intensity", f"{percent:.1f}%")

with right_col:
    st.image("GH_image.png", use_container_width=True, output_format="auto")
