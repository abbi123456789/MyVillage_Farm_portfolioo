import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Rajupalem Land Dashboard", layout="wide")

# ----------------- LOAD DATA -----------------
df = pd.read_excel("Rajupalem Land Records.xlsx")

# ----------------- CLEANUP -----------------
df.columns = df.columns.str.strip()
df['Land owner name'] = df['Land owner name'].astype(str).str.strip()
df['Land nature'] = df['Land nature'].astype(str).str.strip()
df['Land classification'] = df['Land classification'].astype(str).str.strip()
df['Account No.'] = pd.to_numeric(df['Account No.'], errors='coerce')
df['Land Parcel Number'] = pd.to_numeric(df['Land Parcel Number'], errors='coerce')
df['Land Extent (in acres)'] = pd.to_numeric(df['Land Extent (in acres)'], errors='coerce')

# ----------------- SHARED LAND PARCEL LOGIC -----------------
shared_parcels = df['Land Parcel Number'].value_counts()
shared_parcels = shared_parcels[shared_parcels > 1].index.dropna().astype(int).tolist()

# ----------------- FILTER OPTIONS -----------------
land_owner_options = sorted(df['Land owner name'].dropna().unique().tolist())
account_no_options = sorted(df['Account No.'].dropna().astype(int).unique().tolist())
land_parcel_options = sorted(df['Land Parcel Number'].dropna().astype(int).unique().tolist())
shared_parcel_options = sorted(shared_parcels)

# ----------------- SESSION STATE INIT -----------------
if "land_owner" not in st.session_state:
    st.session_state["land_owner"] = []
if "account_no" not in st.session_state:
    st.session_state["account_no"] = []
if "land_parcel" not in st.session_state:
    st.session_state["land_parcel"] = []
if "shared_parcel" not in st.session_state:
    st.session_state["shared_parcel"] = []

# ----------------- SIDEBAR FILTERS -----------------
with st.sidebar:
    st.title("🔍 Filters")

    if st.button("🔁 Reset Filters"):
        st.session_state["land_owner"] = []
        st.session_state["account_no"] = []
        st.session_state["land_parcel"] = []
        st.session_state["shared_parcel"] = []
        st.rerun()

    st.multiselect(
        "Land Owner Name (Search & Select)",
        options=land_owner_options,
        default=st.session_state["land_owner"],
        key="land_owner"
    )

    st.multiselect(
        "Account Number",
        options=account_no_options,
        default=st.session_state["account_no"],
        key="account_no"
    )

    st.multiselect(
        "Land Parcel Number",
        options=land_parcel_options,
        default=st.session_state["land_parcel"],
        key="land_parcel"
    )

    st.multiselect(
        "Shared Parcel Numbers",
        options=shared_parcel_options,
        default=st.session_state["shared_parcel"],
        key="shared_parcel"
    )

# ----------------- APPLY FILTERS -----------------
filtered_df = df.copy()

if st.session_state["land_owner"]:
    filtered_df = filtered_df[filtered_df["Land owner name"].isin(st.session_state["land_owner"])]

if st.session_state["account_no"]:
    filtered_df = filtered_df[filtered_df["Account No."].astype('Int64').isin(st.session_state["account_no"])]

if st.session_state["land_parcel"]:
    filtered_df = filtered_df[filtered_df["Land Parcel Number"].astype('Int64').isin(st.session_state["land_parcel"])]

if st.session_state["shared_parcel"]:
    filtered_df = filtered_df[filtered_df["Land Parcel Number"].astype('Int64').isin(st.session_state["shared_parcel"])]

# ----------------- DAX-STYLE KPI CALCULATIONS -----------------
parcel_max = filtered_df.groupby('Land Parcel Number')['Land Extent (in acres)'].max()
total_extent = parcel_max.sum()

patta_df = filtered_df[filtered_df["Land nature"].str.lower().str.contains("patta")]
patta_parcel_max = patta_df.groupby('Land Parcel Number')['Land Extent (in acres)'].max()
patta_extent = patta_parcel_max.sum()

govt_df = filtered_df[filtered_df["Land nature"].str.lower().str.contains("govt")]
govt_parcel_max = govt_df.groupby('Land Parcel Number')['Land Extent (in acres)'].max()
govt_extent = govt_parcel_max.sum()

distinct_owners = filtered_df["Land owner name"].nunique()
total_parcels = filtered_df["Land Parcel Number"].nunique()

dax_df = (
    filtered_df.groupby(["Land classification", "Land Parcel Number"])["Land Extent (in acres)"]
    .max()
    .reset_index()
)


# ----------------- KPI CARD FUNCTION -----------------
def kpi_card(title, value, color="#4CAF50", icon="📊"):
    st.markdown(f"""
        <div style="
            background-color: #ffffff;
            border: 2px solid {color};
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        ">
            <div style="font-size: 18px; font-weight: 600; color: #333;">{icon} {title}</div>
            <div style="font-size: 30px; color: {color}; font-weight: bold; margin-top: 10px;">
                {value}
            </div>
        </div>
    """, unsafe_allow_html=True)

# ----------------- TITLE -----------------
st.title("📊 Rajupalem Land Dashboard")
st.markdown("**Village: Rajupalem, Mandal: Kothapatnam, District: Prakasam 523280**")

# ----------------- KPI DISPLAY -----------------
col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Total Land Extent", f"{total_extent:.2f} acres", "#4CAF50", "🌾")
with col2:
    kpi_card("Patta Land Extent", f"{patta_extent:.2f} acres", "#2196F3", "📜")
with col3:
    kpi_card("Govt. Land Extent", f"{govt_extent:.2f} acres", "#FF5722", "🏛️")

col4, col5 = st.columns(2)
with col4:
    kpi_card("Distinct Owners", f"{distinct_owners}", "#9C27B0", "👥")
with col5:
    kpi_card("Total Parcels", f"{total_parcels}", "#FFC107", "🧾")

# ----------------- CHARTS -----------------
if not filtered_df.empty:
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        pie_chart = px.pie(
            filtered_df,
            names="Land nature",
            title="Land Parcel Distribution by Nature",
            hole=0.4
        )
        st.plotly_chart(pie_chart, use_container_width=True)

    with col_chart2:
        bar_data = dax_df.groupby("Land classification")["Land Extent (in acres)"].sum().reset_index()
        bar_chart = px.bar(
            bar_data,
            x="Land classification",
            y="Land Extent (in acres)",
            title="Total Land by Classification",
            labels={"Land Extent (in acres)": "Acres"}
        )
        st.plotly_chart(bar_chart, use_container_width=True)

# ----------------- TABLE -----------------
st.markdown("### 📋 Detailed Land Records")
st.dataframe(
    filtered_df[[
        "Account No.", "Land owner name", "Land Parcel Number", "Land nature",
        "Land classification", "Land sub-classification", "Land Extent (in acres)"
    ]]
)

# ----------------- TOP OWNERS -----------------
top_owners = (
    df.groupby("Land owner name")["Land Extent (in acres)"]
    .sum()
    .reset_index()
    .sort_values(by="Land Extent (in acres)", ascending=False)
    .head(5)
)

st.markdown("### 🏆 Top 5 Land Owners by Total Extent")
st.dataframe(top_owners.rename(columns={"Land Extent (in acres)": "Total Land in Acres"}))
