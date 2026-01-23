import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from streamlit_folium import st_folium
import folium
import os

sns.set_theme(style='dark')

def create_daily_trend_df(df):
    daily_trend = df.resample(rule='D', on='datetime').agg({
        "PM2.5": "mean",
        "PM10": "mean",
        "SO2": "mean",
        "NO2": "mean"
    })
    return daily_trend

def create_by_station_df(df):
    by_station = df.groupby(by="station").agg({
        "PM2.5": "mean"
    }).sort_values(by="PM2.5", ascending=False)
    return by_station

def create_yearly_trend_df(df):
    df['year_num'] = df['datetime'].dt.year
    yearly_df = df.groupby('year_num')[['PM2.5', 'PM10', 'SO2', 'NO2']].mean().reset_index()
    return yearly_df

# Load data
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, 'main_data.csv') 
all_data = pd.read_csv(csv_path)
all_data['datetime'] = pd.to_datetime(all_data['datetime'])
all_data.sort_values(by="datetime", inplace=True)
all_data.reset_index(inplace=True)

# Filter sidebar
min_date = all_data["datetime"].min()
max_date = all_data["datetime"].max()

with st.sidebar:
    st.header("Filter Data")
    
    # Filter rentang waktu
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

    # Filter stasiun
    station_list = all_data['station'].unique().tolist()
    selected_stations = st.multiselect('Pilih Stasiun', station_list, default=station_list)

# Logic filter
if not selected_stations:
    selected_stations = station_list # Jika kosong, pilih semua

main_df = all_data[(all_data["datetime"] >= str(start_date)) & 
                (all_data["datetime"] <= str(end_date)) &
                (all_data["station"].isin(selected_stations))]

# Dashboard
st.title('Air Quality Dashboard ☁️')
st.markdown("Dashboard ini menampilkan analisis kualitas udara historis (2013-2017).")

# KPI
col1, col2, col3 = st.columns(3)
with col1:
    avg_pm25 = main_df['PM2.5'].mean()
    st.metric("Rata-rata PM2.5", value=f"{avg_pm25:.2f} ug/m³")
with col2:
    max_pm25 = main_df['PM2.5'].max()
    st.metric("PM2.5 Tertinggi", value=f"{max_pm25:.2f} ug/m³")
with col3:
    total_records = main_df.shape[0]
    st.metric("Total Data Record", value=total_records)

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Tren Waktu", "Analisis Lokasi", "Peta Geospatial"])
with tab1:
    st.header("Analisis Tren Waktu")
    st.subheader("Tren Tahunan Kualitas Udara")
    yearly_df = create_yearly_trend_df(main_df)
    fig, ax = plt.subplots(figsize=(10, 5))
    # Linechart
    sns.lineplot(
        data=yearly_df, 
        x='year_num', 
        y='PM2.5', 
        marker='o', 
        linewidth=2.5, 
        color='red', 
        label='PM2.5 Tahunan',
        ax=ax
    )
    ax.set_title('Tren Tahunan Kualitas Udara', fontsize=14)
    ax.set_xlabel('Tahun', fontsize=12)
    ax.set_ylabel('PM2.5 (ug/m3)', fontsize=12)
    ax.set_xticks(yearly_df['year_num'])
    ax.grid(True)
    st.pyplot(fig)
    
with tab2:
    st.header("Peringkat Polusi per Stasiun")
    by_station_df = create_by_station_df(main_df)
    # Bar Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        x=by_station_df["PM2.5"], 
        y=by_station_df.index, 
        hue=by_station_df["PM2.5"], 
        palette="viridis_r",
        ax=ax
    )
    ax.set_title("Rata-rata PM2.5 per Stasiun", loc="center", fontsize=15)
    ax.set_ylabel(None)
    ax.set_xlabel("Konsentrasi PM2.5 (ug/m3)", fontsize=12)
    ax.tick_params(axis='y', labelsize=12)
    st.pyplot(fig)
    st.caption("Semakin gelap warnanya, semakin tinggi rata-rata polusinya.")

with tab3:
    st.header("Peta Persebaran Stasiun")
    # Koordinat stasiun
    station_coords = {
        'Aotizhongxin': [39.982, 116.397], 'Changping': [40.217, 116.230],
        'Dingling': [40.292, 116.220], 'Dongsi': [39.929, 116.417],
        'Guanyuan': [39.929, 116.339], 'Gucheng': [39.914, 116.184],
        'Huairou': [40.328, 116.628], 'Nongzhanguan': [39.937, 116.461],
        'Shunyi': [40.127, 116.655], 'Tiantan': [39.886, 116.407],
        'Wanliu': [39.987, 116.287], 'Wanshouxigong': [39.878, 116.352]
    }

    m = folium.Map(location=[40.0, 116.4], zoom_start=10)
    filtered_map_data = main_df.groupby('station')['PM2.5'].mean().reset_index()

    for index, row in filtered_map_data.iterrows():
        station = row['station']
        pm_value = row['PM2.5']
        
        if station in station_coords:
            lat, lon = station_coords[station]
            
            if pm_value < 75:
                color = 'green' # baik
            elif pm_value < 85:
                color = 'orange' # sedang
            else:
                color = 'red' # buruk
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=15,
                popup=f"{station}: {pm_value:.2f}",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                tooltip=station
            ).add_to(m)

    st_folium(m, width=700, height=500)