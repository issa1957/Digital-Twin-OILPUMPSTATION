import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Libya Oil Digital Twin", layout="wide")

# ==========================================================
# ASSET REGISTRY
# ==========================================================

DEFAULT_ASSETS = [
    {
        "Asset":"P101",
        "Type":"Pump",
        "Criticality":0.8,
        "Temperature":0.60,
        "Vibration":0.70,
        "OperatingHours":0.50,
        "MaintenanceGap":0.40,
        "Corrosion":0.0,
        "Pressure":0.0,
        "Age":0.40
    },

    {
        "Asset":"P102",
        "Type":"Pump",
        "Criticality":0.7,
        "Temperature":0.30,
        "Vibration":0.40,
        "OperatingHours":0.30,
        "MaintenanceGap":0.20,
        "Corrosion":0.0,
        "Pressure":0.0,
        "Age":0.20
    },

    {
        "Asset":"T201",
        "Type":"Tank",
        "Criticality":1.0,
        "Temperature":0.0,
        "Vibration":0.0,
        "OperatingHours":0.0,
        "MaintenanceGap":0.50,
        "Corrosion":0.80,
        "Pressure":0.0,
        "Age":0.70
    },

    {
        "Asset":"PL301",
        "Type":"Pipeline",
        "Criticality":1.0,
        "Temperature":0.0,
        "Vibration":0.0,
        "OperatingHours":0.0,
        "MaintenanceGap":0.0,
        "Corrosion":0.70,
        "Pressure":0.60,
        "Age":0.60
    },

    {
        "Asset":"C401",
        "Type":"Compressor",
        "Criticality":0.9,
        "Temperature":0.70,
        "Vibration":0.60,
        "OperatingHours":0.0,
        "MaintenanceGap":0.40,
        "Corrosion":0.0,
        "Pressure":0.0,
        "Age":0.50
    }
]

if "asset_data" not in st.session_state:
    st.session_state.asset_data = pd.DataFrame(DEFAULT_ASSETS)

# ==========================================================
# RESET
# ==========================================================

def reset_assets():
    st.session_state.asset_data = pd.DataFrame(DEFAULT_ASSETS)

# ==========================================================
# RISK MODEL
# ==========================================================

def compute_pof(row):

    if row["Type"] == "Pump":
        return (
            0.35 * row["Vibration"] +
            0.25 * row["Temperature"] +
            0.20 * row["OperatingHours"] +
            0.20 * row["MaintenanceGap"]
        )

    elif row["Type"] == "Tank":
        return (
            0.40 * row["Corrosion"] +
            0.30 * row["Age"] +
            0.30 * row["MaintenanceGap"]
        )

    elif row["Type"] == "Pipeline":
        return (
            0.35 * row["Corrosion"] +
            0.25 * row["Pressure"] +
            0.40 * row["Age"]
        )

    elif row["Type"] == "Compressor":
        return (
            0.40 * row["Vibration"] +
            0.30 * row["Temperature"] +
            0.30 * row["MaintenanceGap"]
        )

    return 0

# ==========================================================
# CONSEQUENCE MODEL
# ==========================================================

def compute_consequence(row):

    if row["Type"] == "Pump":
        return 0.54

    elif row["Type"] == "Tank":
        return 0.71

    elif row["Type"] == "Pipeline":
        return 0.815

    elif row["Type"] == "Compressor":
        return 0.63

    return 0

# ==========================================================
# DECISION ENGINE
# ==========================================================

def classify(risk):

    if risk > 0.70:
        return "CRITICAL", "STOP OPERATION"

    elif risk > 0.40:
        return "HIGH", "URGENT INSPECTION"

    elif risk > 0.20:
        return "MEDIUM", "MONITOR"

    return "LOW", "NORMAL"

# ==========================================================
# CALCULATION ENGINE
# ==========================================================

def calculate_results(df):

    results = []

    for _, row in df.iterrows():

        pof = compute_pof(row)

        consequence = compute_consequence(row)

        risk = pof * consequence * row["Criticality"]

        health = (1 - pof) * 100

        level, action = classify(risk)

        results.append({

            "Asset": row["Asset"],
            "Type": row["Type"],
            "PoF": round(pof,3),
            "Consequence": round(consequence,3),
            "Risk": round(risk,3),
            "Health": round(health,1),
            "Level": level,
            "Action": action,
            "Criticality": row["Criticality"]

        })

    return pd.DataFrame(results)

# ==========================================================
# TITLE
# ==========================================================

st.title("🛢️ Libya Oil Digital Twin")
st.caption("Training Prototype v2.0")

# ==========================================================
# RESET BUTTON
# ==========================================================

if st.button("Reset Plant"):
    reset_assets()
    st.rerun()

# ==========================================================
# MAIN DATA
# ==========================================================

assets_df = st.session_state.asset_data.copy()

results = calculate_results(assets_df)

# ==========================================================
# KPI
# ==========================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Assets",
    len(results)
)

col2.metric(
    "Average Risk",
    round(results["Risk"].mean(),3)
)

col3.metric(
    "Highest Risk Asset",
    results.loc[
        results["Risk"].idxmax(),
        "Asset"
    ]
)

col4.metric(
    "Average Health %",
    round(results["Health"].mean(),1)
)

# ==========================================================
# RISK RANKING
# ==========================================================

st.subheader("📊 Asset Risk Ranking")

fig1 = px.bar(
    results.sort_values("Risk"),
    x="Risk",
    y="Asset",
    color="Risk",
    orientation="h"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# ==========================================================
# TWO COLUMN LAYOUT
# ==========================================================

left, right = st.columns([2,1])

# ==========================================================
# RISK MATRIX
# ==========================================================

with left:

    st.subheader("📈 Risk Matrix")

    fig2 = px.scatter(
        results,
        x="PoF",
        y="Consequence",
        size="Risk",
        color="Type",
        text="Asset"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

# ==========================================================
# SIMULATOR
# ==========================================================

with right:

    st.subheader("🧪 Digital Twin Simulator")

    asset_choice = st.selectbox(
        "Select Asset",
        assets_df["Asset"]
    )

    selected = assets_df[
        assets_df["Asset"] == asset_choice
    ].iloc[0]

    temp = st.slider(
        "Temperature",
        0.0,1.0,
        float(selected["Temperature"])
    )

    vib = st.slider(
        "Vibration",
        0.0,1.0,
        float(selected["Vibration"])
    )

    corr = st.slider(
        "Corrosion",
        0.0,1.0,
        float(selected["Corrosion"])
    )

    pressure = st.slider(
        "Pressure",
        0.0,1.0,
        float(selected["Pressure"])
    )

    if st.button("Apply Changes"):

        idx = st.session_state.asset_data[
            st.session_state.asset_data["Asset"]
            == asset_choice
        ].index[0]

        st.session_state.asset_data.loc[
            idx,
            "Temperature"
        ] = temp

        st.session_state.asset_data.loc[
            idx,
            "Vibration"
        ] = vib

        st.session_state.asset_data.loc[
            idx,
            "Corrosion"
        ] = corr

        st.session_state.asset_data.loc[
            idx,
            "Pressure"
        ] = pressure

        st.success(
            f"{asset_choice} updated successfully."
        )

        st.rerun()

# ==========================================================
# DECISION CENTER
# ==========================================================

st.subheader("⚠️ Decision Center")

st.dataframe(
    results,
    use_container_width=True
)