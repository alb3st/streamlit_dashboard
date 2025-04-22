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
    # Ganti dengan ID file Google Drive Anda
    orders_id = "1EXGtV9wU1Zw3oomsbX_cZfbjdKsNrNML"
    customers_id = "19wQFMuzT_fAZTz8NPZxA_klgA2hXP0LP"
    
    # Format URL unduhan langsung
    orders_url = f"https://drive.google.com/uc?export=download&id={orders_id}"
    customers_url = f"https://drive.google.com/uc?export=download&id={customers_id}"
    
    try:
        # Load data
        orders = pd.read_csv(orders_url)
        customers = pd.read_csv(customers_url)
        
        # Validasi kolom yang diperlukan
        if 'order_purchase_timestamp' not in orders.columns:
            raise ValueError("Kolom 'order_purchase_timestamp' tidak ditemukan di data orders.")
        if 'customer_state' not in customers.columns:
            raise ValueError("Kolom 'customer_state' tidak ditemukan di data customers.")
        
        # Preprocessing
        orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
        orders['year'] = orders['order_purchase_timestamp'].dt.year
        orders['month'] = orders['order_purchase_timestamp'].dt.month
        
        return orders, customers
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

# Load data
orders_df, customers_df = load_data()

# Validasi apakah data berhasil dimuat
if orders_df.empty or customers_df.empty:
    st.error("Data gagal dimuat. Periksa URL atau format file.")
else:
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
        
        if delivered_orders.empty:
            st.warning("Tidak ada data pesanan yang sesuai dengan filter.")
        else:
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
    delivered_orders = orders_df[
        (orders_df["order_status"] == "delivered") &
        (orders_df["year"].between(year_range[0], year_range[1]))
    ].copy()
    
    all_orders = orders_df[
        orders_df["year"].between(year_range[0], year_range[1])
    ].copy()
    
    orders_customers_delivered = pd.merge(
        delivered_orders[["order_id", "customer_id"]],
        customers_df[["customer_id", "customer_city", "customer_state"]],
        on="customer_id"
    )
    
    orders_customers_all = pd.merge(
        all_orders[["order_id", "customer_id"]],
        customers_df[["customer_id", "customer_city", "customer_state"]],
        on="customer_id"
    )
    
    if orders_customers_delivered.empty:
        st.warning("Tidak ada data untuk analisis kota.")
    else:
        # Filter negara bagian jika dipilih
        if selected_state != "All":
            orders_customers_delivered = orders_customers_delivered[orders_customers_delivered["customer_state"] == selected_state]
            orders_customers_all = orders_customers_all[orders_customers_all["customer_state"] == selected_state]
            st.subheader(f"Analisis untuk Negara Bagian: {selected_state}")
        
        # Hitung pesanan per kota untuk delivered dan total
        delivered_city_orders = orders_customers_delivered.groupby("customer_city")["order_id"].count().reset_index()
        delivered_city_orders.columns = ["city", "delivered_orders"]
        
        all_city_orders = orders_customers_all.groupby("customer_city")["order_id"].count().reset_index()
        all_city_orders.columns = ["city", "total_orders"]
        
        # Gabungkan data
        city_comparison = pd.merge(delivered_city_orders, all_city_orders, on="city", how="outer").fillna(0)
        city_comparison = city_comparison.sort_values("delivered_orders", ascending=False)
        
        # Visualisasi dengan overlay seperti di Google Colab
        st.subheader("Perbandingan Pesanan Delivered vs Total Orders")
        
        fig2, ax = plt.subplots(figsize=(12, 6))
        
        # Plot untuk top 10 kota berdasarkan jumlah delivered orders
        sns.barplot(
            data=city_comparison.nlargest(10, "delivered_orders"),
            x="delivered_orders",
            y="city",
            color="teal",
            label="Delivered",
            ax=ax
        )
        
        sns.barplot(
            data=city_comparison.nlargest(10, "delivered_orders"),
            x="total_orders",
            y="city",
            color="red",
            alpha=0.3,
            label="Total Orders",
            ax=ax
        )
        
        ax.set_title("Perbandingan Total Pesanan vs Delivered per Kota", pad=20)
        ax.set_xlabel("Jumlah Pesanan")
        ax.set_ylabel("Kota")
        ax.legend()
        
        st.pyplot(fig2)
        
        # Tambahkan insight
        st.write("### Insight:")
        top_city = city_comparison.iloc[0]["city"]
        top_delivery_rate = (city_comparison.iloc[0]["delivered_orders"] / city_comparison.iloc[0]["total_orders"]) * 100 if city_comparison.iloc[0]["total_orders"] > 0 else 0
        
        st.write(f"- {top_city} adalah kota dengan jumlah pesanan terkirim terbanyak dengan tingkat keberhasilan pengiriman {top_delivery_rate:.1f}%.")
        
        # Problem cities (rendah rasio delivered/total)
        city_comparison["delivery_rate"] = (city_comparison["delivered_orders"] / city_comparison["total_orders"] * 100).fillna(0)
        problem_cities = city_comparison[city_comparison["total_orders"] > 10].nsmallest(3, "delivery_rate")
        
        if not problem_cities.empty:
            st.write("- Kota dengan tingkat keberhasilan pengiriman terendah:")
            for _, city in problem_cities.iterrows():
                st.write(f"  • {city['city']}: {city['delivery_rate']:.1f}% ({int(city['delivered_orders'])} dari {int(city['total_orders'])} pesanan)")
        
        # Tambahkan peta distribusi yang sudah ada sebelumnya
        st.subheader("Peta Distribusi")
        state_orders = orders_customers_delivered.groupby("customer_state")["order_id"].count().reset_index()
        state_orders.columns = ["state", "orders"]
        
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