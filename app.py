
import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------
# PAGE CONFIGURATION
# -------------------------------

st.set_page_config(
    page_title="OLA Ride Insights",
    page_icon="🚕",
    layout="wide"
)

# -------------------------------
# LOAD DATA
# -------------------------------

@st.cache_data
def load_data():
    data = pd.read_csv("OLA_Final_Cleaned_Data.csv")

    data["Date"] = pd.to_datetime(
        data["Date"], errors="coerce"
    )

    data["Booking_Value"] = pd.to_numeric(
        data["Booking_Value"], errors="coerce"
    )

    data["Ride_Distance"] = pd.to_numeric(
        data["Ride_Distance"], errors="coerce"
    )

    data["Driver_Ratings"] = pd.to_numeric(
        data["Driver_Ratings"], errors="coerce"
    )

    data["Customer_Rating"] = pd.to_numeric(
        data["Customer_Rating"], errors="coerce"
    )

    return data


df = load_data()

# -------------------------------
# SIDEBAR
# -------------------------------

st.sidebar.title("🚕 OLA Analytics")

page = st.sidebar.selectbox(
    "Select Dashboard",
    [
        "Overview",
        "Vehicle Analysis",
        "Revenue Analysis",
        "Cancellation Analysis",
        "Ratings Analysis",
        "Booking Search",
        "Power BI Dashboard"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

# Date filter
valid_dates = df["Date"].dropna()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

# Vehicle filter
vehicles = sorted(df["Vehicle_Type"].dropna().unique())

selected_vehicles = st.sidebar.multiselect(
    "Vehicle Type",
    vehicles,
    default=vehicles
)

# Booking status filter
statuses = sorted(
    df["Booking_Status"].dropna().unique()
)

selected_status = st.sidebar.multiselect(
    "Booking Status",
    statuses,
    default=statuses
)

# Apply filters
filtered_df = df.copy()

if date_range and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_df = filtered_df[
        (filtered_df["Date"].dt.date >= start_date)
        & (filtered_df["Date"].dt.date <= end_date)
    ]

filtered_df = filtered_df[
    filtered_df["Vehicle_Type"].isin(selected_vehicles)
]

filtered_df = filtered_df[
    filtered_df["Booking_Status"].isin(selected_status)
]

# -------------------------------
# COMMON CALCULATIONS
# -------------------------------

successful = filtered_df[
    filtered_df["Booking_Status"] == "Success"
]

total_bookings = len(filtered_df)

success_count = len(successful)

total_revenue = successful["Booking_Value"].sum()

cancelled_count = filtered_df[
    filtered_df["Booking_Status"].isin(
        ["Canceled by Customer", "Canceled by Driver"]
    )
].shape[0]

# -------------------------------
# PAGE 1: OVERVIEW
# -------------------------------

if page == "Overview":

    st.title("🚕 OLA Ride Insights Dashboard")

    st.caption(
        "Interactive analysis of OLA ride bookings"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Bookings",
        f"{total_bookings:,}"
    )

    col2.metric(
        "Successful Bookings",
        f"{success_count:,}"
    )

    col3.metric(
        "Total Revenue",
        f"₹{total_revenue:,.0f}"
    )

    col4.metric(
        "Cancelled Bookings",
        f"{cancelled_count:,}"
    )

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        status_data = (
            filtered_df["Booking_Status"]
            .value_counts()
            .reset_index()
        )

        status_data.columns = [
            "Booking Status", "Bookings"
        ]

        fig = px.pie(
            status_data,
            names="Booking Status",
            values="Bookings",
            title="Booking Status Breakdown",
            hole=0.4
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        daily = (
            filtered_df.groupby("Date")
            .size()
            .reset_index(name="Bookings")
        )

        fig = px.line(
            daily,
            x="Date",
            y="Bookings",
            title="Daily Ride Volume",
            markers=True
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Booking Records")

    st.dataframe(
        filtered_df.head(20),
        use_container_width=True
    )

# -------------------------------
# PAGE 2: VEHICLE ANALYSIS
# -------------------------------

elif page == "Vehicle Analysis":

    st.title("🚘 Vehicle Analysis")

    vehicle_data = (
        filtered_df.groupby("Vehicle_Type")
        .agg(
            Total_Bookings=("Booking_ID", "count"),
            Total_Distance=("Ride_Distance", "sum"),
            Average_Distance=("Ride_Distance", "mean")
        )
        .reset_index()
    )

    fig = px.bar(
        vehicle_data,
        x="Vehicle_Type",
        y="Total_Distance",
        title="Total Ride Distance by Vehicle Type",
        color="Vehicle_Type"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Vehicle Performance")

    st.dataframe(
        vehicle_data,
        use_container_width=True
    )

# -------------------------------
# PAGE 3: REVENUE ANALYSIS
# -------------------------------

elif page == "Revenue Analysis":

    st.title("💰 Revenue Analysis")

    left, right = st.columns(2)

    with left:
        payment_data = (
            successful.groupby("Payment_Method")
            ["Booking_Value"].sum()
            .reset_index()
        )

        fig = px.bar(
            payment_data,
            x="Payment_Method",
            y="Booking_Value",
            title="Revenue by Payment Method"
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        top_customers = (
            successful.groupby("Customer_ID")
            ["Booking_Value"].sum()
            .nlargest(5)
            .reset_index()
        )

        fig = px.bar(
            top_customers,
            x="Customer_ID",
            y="Booking_Value",
            title="Top 5 Customers by Booking Value"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.metric(
        "Successful Ride Revenue",
        f"₹{total_revenue:,.2f}"
    )

# -------------------------------
# PAGE 4: CANCELLATION ANALYSIS
# -------------------------------

elif page == "Cancellation Analysis":

    st.title("❌ Cancellation Analysis")

    customer_cancel = filtered_df[
        filtered_df["Booking_Status"] == "Canceled by Customer"
    ]

    driver_cancel = filtered_df[
        filtered_df["Booking_Status"] == "Canceled by Driver"
    ]

    col1, col2 = st.columns(2)

    with col1:
        customer_reason = (
            customer_cancel[
                "Canceled_Rides_by_Customer"
            ].dropna().value_counts()
            .reset_index()
        )

        customer_reason.columns = ["Reason", "Count"]

        fig = px.bar(
            customer_reason,
            x="Reason",
            y="Count",
            title="Customer Cancellation Reasons"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        driver_reason = (
            driver_cancel[
                "Canceled_Rides_by_Driver"
            ].dropna().value_counts()
            .reset_index()
        )

        driver_reason.columns = ["Reason", "Count"]

        fig = px.bar(
            driver_reason,
            x="Reason",
            y="Count",
            title="Driver Cancellation Reasons"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.write("Customer cancellations:", len(customer_cancel))
    st.write("Driver cancellations:", len(driver_cancel))

# -------------------------------
# PAGE 5: RATINGS ANALYSIS
# -------------------------------

elif page == "Ratings Analysis":

    st.title("⭐ Ratings Analysis")

    col1, col2 = st.columns(2)

    with col1:
        avg_customer = filtered_df[
            "Customer_Rating"
        ].mean()

        st.metric(
            "Average Customer Rating",
            f"{avg_customer:.2f}"
            if pd.notna(avg_customer) else "N/A"
        )

    with col2:
        avg_driver = filtered_df[
            "Driver_Ratings"
        ].mean()

        st.metric(
            "Average Driver Rating",
            f"{avg_driver:.2f}"
            if pd.notna(avg_driver) else "N/A"
        )

    rating_data = filtered_df[
        ["Customer_Rating", "Driver_Ratings"]
    ].melt(
        var_name="Rating Type",
        value_name="Rating"
    ).dropna()

    fig = px.histogram(
        rating_data,
        x="Rating",
        color="Rating Type",
        barmode="group",
        title="Customer and Driver Ratings Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

    vehicle_ratings = (
        filtered_df.groupby("Vehicle_Type")
        [["Customer_Rating", "Driver_Ratings"]]
        .mean()
        .reset_index()
        .melt(
            id_vars="Vehicle_Type",
            var_name="Rating Type",
            value_name="Average Rating"
        )
    )

    fig = px.bar(
        vehicle_ratings,
        x="Vehicle_Type",
        y="Average Rating",
        color="Rating Type",
        barmode="group",
        title="Average Ratings by Vehicle Type"
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# PAGE 6: BOOKING SEARCH
# -------------------------------

elif page == "Booking Search":

    st.title("🔎 Search Booking Details")

    booking_id = st.text_input(
        "Enter Booking ID"
    )

    if booking_id:
        result = df[
            df["Booking_ID"].astype(str).str.contains(
                booking_id,
                case=False,
                na=False
            )
        ]

        if not result.empty:
            st.dataframe(
                result,
                use_container_width=True
            )
        else:
            st.warning("No matching booking found.")

# -------------------------------
# PAGE 7: POWER BI
# -------------------------------

elif page == "Power BI Dashboard":

    st.title("📊 Power BI Dashboard")

    st.info(
        "Paste your Power BI Publish to Web embed URL "
        "in the application code to display the report here."
    )

    st.write(
        "Power BI embedding is optional until you have "
        "an approved public or authenticated embedding method."
    )

# -------------------------------
# FOOTER
# -------------------------------

st.markdown("---")

st.caption(
    "OLA Ride Insights | Data Analytics Project"
)
