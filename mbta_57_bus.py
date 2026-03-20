import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import math
import statistics

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="MBTA 57 Bus Analysis", layout="wide")

API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api-v3.mbta.com/"
baseParams = {"api_key": API_KEY}

st.title("🚌 MBTA Route 57 Analysis")
st.markdown("Analyze wait times, variability, and service patterns.")

# -----------------------------
# DATA FUNCTIONS
# -----------------------------
@st.cache_data
def get_stops():
    url = f"{BASE_URL}stops"
    params = {**baseParams, "filter[route]": "57"}
    res = requests.get(url, params=params)
    data = res.json()

    names = [s["attributes"]["name"] for s in data["data"]]
    ids = [s["id"] for s in data["data"]]

    return names, ids


@st.cache_data
def get_departure_times(stop_ids):
    departure_list = []

    for stop_id in stop_ids:
        url = f"{BASE_URL}predictions"
        params = {**baseParams, "filter[stop]": stop_id}
        res = requests.get(url, params=params)

        stop_times = []
        for item in res.json()["data"]:
            t = item["attributes"]["departure_time"]
            if t:
                stop_times.append(t)

        departure_list.append(stop_times)

    return departure_list


def compute_avg_wait(times_list):
    avg_list = []

    for times in times_list:
        clean = [
            datetime.strptime(t[11:19], "%H:%M:%S")
            for t in times if t
        ]

        if len(clean) >= 2:
            arr = np.array(clean, dtype='datetime64[s]')
            diffs = np.diff(arr).astype(float) / 60
            avg_list.append(float(np.mean(np.abs(diffs))))
        else:
            avg_list.append(0)

    return avg_list


# -----------------------------
# LOAD DATA
# -----------------------------
if st.button("🔄 Load & Analyze Data"):

    with st.spinner("Fetching data from MBTA API..."):
        names, ids = get_stops()
        departures = get_departure_times(ids)

    half = len(names) // 2

    inbound_names = names[:half]
    outbound_names = names[half:]

    inbound_times = departures[:half]
    outbound_times = departures[half:]

    inbound_avg = compute_avg_wait(inbound_times)
    outbound_avg = compute_avg_wait(outbound_times)

    # -----------------------------
    # STATS
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Inbound Mean (min)", round(statistics.mean(inbound_avg), 2))
        st.metric("Outbound Mean (min)", round(statistics.mean(outbound_avg), 2))

    with col2:
        st.metric("Inbound Median", round(statistics.median(inbound_avg), 2))
        st.metric("Outbound Median", round(statistics.median(outbound_avg), 2))

    with col3:
        st.metric("Inbound Std Dev", round(np.std(inbound_avg), 2))
        st.metric("Outbound Std Dev", round(np.std(outbound_avg), 2))

    # -----------------------------
    # HISTOGRAMS
    # -----------------------------
    st.subheader("📊 Wait Time Distributions")

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.hist(inbound_avg, bins=int(math.sqrt(len(inbound_avg))))
        ax.set_title("Inbound Wait Times")
        ax.set_xlabel("Minutes")
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.hist(outbound_avg, bins=int(math.sqrt(len(outbound_avg))))
        ax.set_title("Outbound Wait Times")
        ax.set_xlabel("Minutes")
        st.pyplot(fig)

    # -----------------------------
    # BAR CHARTS
    # -----------------------------
    st.subheader("📍 Wait Time by Stop")

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(6, 10))
        ax.barh(inbound_names, inbound_avg)
        ax.set_title("Inbound Stops")
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(6, 10))
        ax.barh(outbound_names, outbound_avg)
        ax.set_title("Outbound Stops")
        st.pyplot(fig)

    # -----------------------------
    # TABLE
    # -----------------------------
    st.subheader("📋 Summary Table")

    df = pd.DataFrame({
        "Stop": inbound_names + outbound_names,
        "Direction": ["Inbound"] * len(inbound_names) + ["Outbound"] * len(outbound_names),
        "Avg Wait (min)": inbound_avg + outbound_avg
    })

    st.dataframe(df)
