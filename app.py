import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from sklearn.linear_model import LinearRegression

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="PS-01 Digital Twin", layout="wide")

st.title("🛢 PS-01 Digital Twin – Asset Integrity & Risk Platform")

# ==============================
# SESSION STATE (HISTORY)
# ==============================
if "history" not in st.session_state:
    st.session_state.history = []

# ==============================
# ASSET REGISTRY (STATIC MODEL)
# ==============================
assets = {
    "P101": {"type": "Pump", "criticality": 4},
    "P102": {"type": "Pump", "criticality": 4},
    "PL301": {"type": "Pipeline", "criticality": 5},
    "T201": {"type": "Tank", "criticality": 4.5},
    "C401": {"type": "Compressor", "criticality": 5},
}

# ==============================
# SCORE FUNCTIONS
# ==============================

def vib_score(v):
    if v < 3: return 0.1
    elif v < 4.5: return 0.3
    elif v < 7: return 0.7
    return 1.0


def temp_score(t):
    if t < 70: return 0.1
    elif t < 85: return 0.3
    elif t < 100: return 0.7
    return 1.0


def pressure_score(p):
    if p < 0.6: return 0.1
    elif p < 0.75: return 0.3
    elif p < 0.9: return 0.7
    return 1.0


def corrosion_score(c):
    if c < 0.1: return 0.1
    elif c < 0.3: return 0.3
    elif c < 0.5: return 0.7
    return 1.0


def maintenance_score(d):
    if d < 30: return 0.1
    elif d < 90: return 0.3
    elif d < 180: return 0.7
    return 1.0


# ==============================
# ENGINE MODELS
# ==============================

def compute_pof(asset_type, vals):

    if asset_type == "Pump":
        return (
            0.45 * vib_score(vals["vibration"]) +
            0.35 * temp_score(vals["temperature"]) +
            0.20 * maintenance_score(vals["maintenance"])
        )

    elif asset_type == "Pipeline":
        return (
            0.45 * corrosion_score(vals["corrosion"]) +
            0.35 * pressure_score(vals["pressure"]) +
            0.20 * maintenance_score(vals["maintenance"])
        )

    elif asset_type == "Tank":
        return (
            0.50 * corrosion_score(vals["corrosion"]) +
            0.20 * corrosion_score(vals["settlement"]) +
            0.20 * maintenance_score(vals["maintenance"]) +
            0.10 * corrosion_score(vals["age"])
        )

    elif asset_type == "Compressor":
        return (
            0.40 * vib_score(vals["vibration"]) +
            0.30 * temp_score(vals["temperature"]) +
            0.20 * pressure_score(vals["pressure_ratio"]) +
            0.10 * maintenance_score(vals["maintenance"])
        )

    return 0


def compute_cof(asset_type, criticality):

    base = {
        "Pump": 0.55,
        "Pipeline": 0.95,
        "Tank": 0.70,
        "Compressor": 0.75
    }

    return base[asset_type] * (criticality / 5)


def compute_health(pof):
    return max(0, (1 - pof) * 100)


def decision(risk):
    if risk < 0.2:
        return "NORMAL"
    elif risk < 0.4:
        return "MONITOR"
    elif risk < 0.6:
        return "INSPECT"
    elif risk < 0.8:
        return "URGENT INSPECTION"
    return "SHUTDOWN"


# ==============================
# UI — ASSET SELECTION
# ==============================
asset_id = st.selectbox("Select Asset", list(assets.keys()))
asset = assets[asset_id]

st.subheader(f"Asset: {asset_id} ({asset['type']})")

# ==============================
# INPUT MODELS
# ==============================

if asset["type"] == "Pump":

    temperature = st.slider("Temperature (°C)", 40, 120, 75)
    vibration = st.slider("Vibration (mm/s)", 1.0, 10.0, 3.5)
    maintenance = st.slider("Maintenance Delay (days)", 0, 365, 60)

    values = {
        "temperature": temperature,
        "vibration": vibration,
        "maintenance": maintenance
    }

elif asset["type"] == "Pipeline":

    corrosion = st.slider("Corrosion Rate (mm/year)", 0.0, 0.6, 0.2)
    pressure = st.slider("Pressure Utilization (0-1)", 0.4, 1.2, 0.8)
    maintenance = st.slider("Maintenance Delay (days)", 0, 365, 60)

    values = {
        "corrosion": corrosion,
        "pressure": pressure,
        "maintenance": maintenance
    }

elif asset["type"] == "Tank":

    corrosion = st.slider("Bottom Corrosion Rate", 0.0, 0.6, 0.2)
    settlement = st.slider("Settlement Index", 0.0, 1.0, 0.3)
    maintenance = st.slider("Maintenance Delay (days)", 0, 365, 90)
    age = st.slider("Age Factor", 0.0, 1.0, 0.5)

    values = {
        "corrosion": corrosion,
        "settlement": settlement,
        "maintenance": maintenance,
        "age": age
    }

elif asset["type"] == "Compressor":

    temperature = st.slider("Temperature (°C)", 40, 130, 80)
    vibration = st.slider("Vibration (mm/s)", 1.0, 10.0, 4.0)
    pressure_ratio = st.slider("Pressure Ratio", 1.0, 2.5, 1.5)
    maintenance = st.slider("Maintenance Delay (days)", 0, 365, 60)

    values = {
        "temperature": temperature,
        "vibration": vibration,
        "pressure_ratio": pressure_ratio,
        "maintenance": maintenance
    }

# ==============================
# COMPUTATION ENGINE
# ==============================

pof = compute_pof(asset["type"], values)
cof = compute_cof(asset["type"], asset["criticality"])
risk = pof * cof
health = compute_health(pof)
action = decision(risk)

# ==============================
# DISPLAY KPIs
# ==============================

col1, col2, col3, col4 = st.columns(4)

col1.metric("PoF", round(pof, 3))
col2.metric("CoF", round(cof, 3))
col3.metric("Risk", round(risk, 3))
col4.metric("Health %", round(health, 1))

st.subheader(f"Decision: {action}")

# ==============================
# SAVE TO HISTORY
# ==============================
if st.button("Apply & Save Snapshot"):

    st.session_state.history.append({
        "time": datetime.now(),
        "asset": asset_id,
        "pof": pof,
        "cof": cof,
        "risk": risk,
        "health": health
    })

    st.success("Snapshot saved to history")

# ==============================
# HISTORY ANALYTICS
# ==============================
if len(st.session_state.history) > 0:

    df = pd.DataFrame(st.session_state.history)

    st.subheader("Historical Risk Trend")

    st.line_chart(df.groupby("asset")["risk"].mean())

    st.subheader("Historical Health Trend")

    st.line_chart(df.groupby("asset")["health"].mean())

# ==============================
# SIMPLE FORECAST ENGINE
# ==============================

if len(st.session_state.history) > 5:

    st.subheader("30-Day Risk Forecast (Simple Linear Model)")

    df = pd.DataFrame(st.session_state.history)
    df = df[df["asset"] == asset_id]

    if len(df) > 2:

        df["t"] = np.arange(len(df))

        model = LinearRegression()
        model.fit(df[["t"]], df["risk"])

        future = np.array([[len(df) + 30]])
        pred = model.predict(future)[0]

        st.metric("Forecasted Risk (30 days)", round(pred, 3))
