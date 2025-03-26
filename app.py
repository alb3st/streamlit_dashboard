import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import os

# Konfigurasi awal
st.set_page_config(layout="wide")
print("Current working directory:", os.getcwd())

# Judul Dashboard
st.title("📊 E-Commerce Performance Dashboard")

# Fungsi Load Data dengan caching
@st.cache_data(ttl=300)  # Cache 5 menit
def load_data():
    # Load data
    orders = pd.read_csv("C:/Users/POLYBEST/Desktop/streamlit/orders_dataset.csv")
    customers = pd.read_csv("C:/Users/POLYBEST/Desktop/streamlit/customers_dataset.csv")
    
    # Preprocessing
    orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
    orders['year'] = orders['order_purchase_timestamp'].dt.year
    orders['month'] = orders['order_purchase_timestamp'].dt.month
    
    return orders, customers

orders_df, customers_df = load_data()

# Sidebar Filter
with st.sidebar:
    st.header("Filter Data")
    
    # Filter Tahun
    available_years = sorted(orders_df['year'].unique())
    year_range = st.slider(
        "Pilih Rentang Tahun",
        min_value=min(available_years),
        max_value=max(available_years),
        value=(min(available_years), max(available_years))
    )
    
    # Filter Negara Bagian
    selected_state = st.selectbox(
        "Pilih Negara Bagian",
        options=["All"] + sorted(customers_df["customer_state"].unique()),
        index=0
    )

# Tab untuk Analisis
tab1, tab2 = st.tabs(["Tren Pesanan per Bulan", "Analisis Kota Pembeli"])

# Tab 1: Tren Pesanan
with tab1:
    st.header(f"Tren Volume Pesanan Delivered ({year_range[0]}-{year_range[1]})")
    
    # Filter data
    delivered_orders = orders_df[
        (orders_df["order_status"] == "delivered") &
        (orders_df["year"].between(year_range[0], year_range[1]))
    ].copy()
    
    # Hitung pesanan per bulan
    delivered_orders["purchase_month"] = delivered_orders["order_purchase_timestamp"].dt.to_period("M")
    monthly_orders = delivered_orders.groupby("purchase_month")["order_id"].nunique().reset_index()
    monthly_orders["purchase_month"] = monthly_orders["purchase_month"].astype(str)
    
    # Plot
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    sns.lineplot(
        data=monthly_orders, 
        x="purchase_month", 
        y="order_id", 
        marker="o", 
        linewidth=2.5,
        color="#1f77b4",
        ax=ax1
    )
    plt.xticks(rotation=45)
    ax1.set_title(f"Tren Pesanan Delivered {year_range[0]}-{year_range[1]}", pad=20)
    ax1.set_xlabel("Bulan-Tahun")
    ax1.set_ylabel("Jumlah Pesanan")
    ax1.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig1)
    
    # Statistik
    st.subheader("Statistik Utama")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pesanan", len(delivered_orders))
    with col2:
        growth = (monthly_orders["order_id"].iloc[-1] - monthly_orders["order_id"].iloc[0]) / monthly_orders["order_id"].iloc[0] * 100
        st.metric("Pertumbuhan", f"{growth:.1f}%")
    with col3:
        peak_month = monthly_orders.loc[monthly_orders["order_id"].idxmax(), "purchase_month"]
        st.metric("Bulan Puncak", peak_month)

# Tab 2: Analisis Kota
with tab2:
    st.header(f"Distribusi Pesanan per Kota ({year_range[0]}-{year_range[1]})")
    
    # Gabungkan data
    orders_customers = pd.merge(
        orders_df[
            (orders_df["order_status"] == "delivered") &
            (orders_df["year"].between(year_range[0], year_range[1]))
        ][["order_id", "customer_id"]],
        customers_df[["customer_id", "customer_city", "customer_state"]],
        on="customer_id"
    )
    
    # Filter negara bagian jika dipilih
    if selected_state != "All":
        orders_customers = orders_customers[orders_customers["customer_state"] == selected_state]
        st.subheader(f"Analisis untuk Negara Bagian: {selected_state}")
    
    # Hitung pesanan per kota
    city_orders = orders_customers.groupby(["customer_city", "customer_state"])["order_id"].count().reset_index()
    city_orders.columns = ["city", "state", "orders"]
    city_orders_sorted = city_orders.sort_values("orders", ascending=False)
    city_orders_filtered = city_orders_sorted[city_orders_sorted["orders"] > 0]
    
    # Visualisasi Best & Worst Cities
    st.subheader("Kinerja Kota")
    
    fig2, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 10))
    colors = ["#1f77b4", "#d3d3d3", "#d3d3d3", "#d3d3d3", "#d3d3d3"]
    
    # Plot Top Cities
    sns.barplot(
        x="orders", 
        y="city", 
        data=city_orders_filtered.head(5),
        palette=colors,
        ax=ax[0]
    )
    ax[0].set_title(f"Top 5 Kota", fontsize=16)
    ax[0].set_xlabel("Jumlah Pesanan", fontsize=12)
    ax[0].set_ylabel("")
    
    # Plot Bottom Cities
    sns.barplot(
        x="orders", 
        y="city", 
        data=city_orders_filtered.tail(5),
        palette=colors[::-1],
        ax=ax[1]
    )
    ax[1].set_title(f"Bottom 5 Kota", fontsize=16)
    ax[1].set_xlabel("Jumlah Pesanan", fontsize=12)
    ax[1].set_ylabel("")
    ax[1].invert_xaxis()
    ax[1].yaxis.tick_right()
    
    plt.tight_layout()
    st.pyplot(fig2)
    
    # Peta Distribusi
    st.subheader("Peta Distribusi")
    state_orders = city_orders.groupby("state")["orders"].sum().reset_index()
    
    if not state_orders.empty:
        fig3 = px.choropleth(
            state_orders,
            locations="state",
            locationmode="ISO-3",
            color="orders",
            scope="south america",
            color_continuous_scale="Blues",
            labels={'orders':'Pesanan'},
            hover_name="state",
            hover_data=["orders"]
        )
        fig3.update_layout(height=600)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("Tidak ada data untuk ditampilkan dengan filter saat ini")

# Catatan Kaki
st.caption("""
Dashboard ini menggunakan dataset Brazilian E-Commerce (Olist).  
Update terakhir: Juli 2024.
""")