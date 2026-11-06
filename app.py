
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# App Configuration
# =========================================================

st.set_page_config(
    page_title="COTTONIL Business Dashboard",
    page_icon="📊",
    layout="wide",
)

DATA_DIR = Path(__file__).resolve().parent / "data"

YEARLY_PATH = DATA_DIR / "yearly_profit_gross_sales.csv"
BRANCHES_PATH = DATA_DIR / "branches.csv"
ORDERS_PATH = DATA_DIR / "sales_order_items.csv"

PERFORMANCE_PATH = Path(__file__).resolve().parent / "branch_performance.csv"


# =========================================================
# Data Loading
# =========================================================

@st.cache_data
def load_csv(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    return df


def validate_columns(df, required_columns, file_name):
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        st.error(
            f"Missing columns in {file_name}: "
            f"{', '.join(sorted(missing_columns))}"
        )
        st.stop()


# =========================================================
# Overview Page
# =========================================================

def overview_page():

    st.title("📊 Business Overview")
    st.caption("COTTONIL Business Performance Dashboard")

    try:
        yearly_df = load_csv(YEARLY_PATH)
    except FileNotFoundError:
        st.error(f"File not found: {YEARLY_PATH}")
        return

    validate_columns(
        yearly_df,
        {"year", "gross_sales", "profit"},
        YEARLY_PATH.name,
    )

    yearly_df["year"] = pd.to_numeric(
        yearly_df["year"], errors="coerce"
    )

    yearly_df["gross_sales"] = pd.to_numeric(
        yearly_df["gross_sales"], errors="coerce"
    )

    yearly_df["profit"] = pd.to_numeric(
        yearly_df["profit"], errors="coerce"
    )

    yearly_df = yearly_df.dropna(
        subset=["year", "gross_sales"]
    ).sort_values("year")

    yearly_df["year"] = yearly_df["year"].astype(int)

    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Total Margin (EGP)",
        f"{305281924.01:,.2f}",
    )

    col2.metric(
        "Number of Branches",
        "80",
    )

    col3.metric(
        "Customers in Database",
        "85,000",
    )

    col4.metric(
        "Unique Products",
        "695",
    )

    col5.metric(
        "Number of Categories",
        "16",
    )

    st.divider()

    # Gross Sales by Year
    st.subheader("Gross Sales by Year")

    fig = px.line(
        yearly_df,
        x="year",
        y="gross_sales",
        markers=True,
        labels={
            "year": "Year",
            "gross_sales": "Gross Sales (EGP)",
        },
        template="plotly_white",
    )

    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        hovertemplate=(
            "Year: %{x}<br>"
            "Gross Sales: %{y:,.2f} EGP"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=450,
        xaxis=dict(
            title="Year",
            tickmode="linear",
            dtick=1,
        ),
        yaxis=dict(
            title="Gross Sales (EGP)",
            tickformat=",",
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Sales data period: January 1 – October 18, "
        "according to the source dataset."
    )


# =========================================================
# Branches Page
# =========================================================

def branches_page():

    st.title("🏢 Branch Performance")
    st.caption("Branch distribution, profitability, and margin trends")

    try:
        branches = load_csv(BRANCHES_PATH)
        performance = load_csv(PERFORMANCE_PATH)
        orders = load_csv(ORDERS_PATH)

    except FileNotFoundError as error:
        st.error(f"File not found: {error.filename}")
        return

    validate_columns(
        branches,
        {
            "branch_id",
            "branch_name_ar",
            "governorate_ar",
        },
        BRANCHES_PATH.name,
    )

    validate_columns(
        performance,
        {
            "branch_id",
            "branch_name_ar",
            "profit",
            "completed_orders",
            "returned_orders",
            "governorate_ar",
        },
        PERFORMANCE_PATH.name,
    )

    validate_columns(
        orders,
        {
            "branch_id",
            "order_date",
            "margin_egp",
        },
        ORDERS_PATH.name,
    )

    # Normalize branch IDs to consistent strings for matching.
    branches["branch_id"] = branches["branch_id"].astype("string").str.strip()
    performance["branch_id"] = (
        performance["branch_id"].astype("string").str.strip()
    )
    orders["branch_id"] = orders["branch_id"].astype("string").str.strip()

    branches["branch_name_ar"] = (
        branches["branch_name_ar"].astype("string").str.strip()
    )
    branches["governorate_ar"] = (
        branches["governorate_ar"].astype("string").str.strip()
    )

    performance["profit"] = pd.to_numeric(
        performance["profit"], errors="coerce"
    )
    performance["returned_orders"] = pd.to_numeric(
        performance["returned_orders"], errors="coerce"
    )

    orders["order_date"] = pd.to_datetime(
        orders["order_date"], errors="coerce"
    )
    orders["margin_egp"] = pd.to_numeric(
        orders["margin_egp"], errors="coerce"
    )

    # -----------------------------------------------------
    # 1. Branch Count by Governorate
    # -----------------------------------------------------

    st.subheader("Branch Distribution by Governorate")

    governorate_counts = (
        branches.dropna(subset=["governorate_ar", "branch_id"])
        .groupby("governorate_ar", as_index=False)["branch_id"]
        .nunique()
        .rename(columns={"branch_id": "branch_count"})
        .sort_values("branch_count", ascending=True)
    )

    if not governorate_counts.empty:

        fig_governorates = px.bar(
            governorate_counts,
            x="branch_count",
            y="governorate_ar",
            orientation="h",
            text="branch_count",
            labels={
                "branch_count": "Number of Branches",
                "governorate_ar": "Governorate",
            },
            template="plotly_white",
        )

        fig_governorates.update_traces(
            textposition="outside",
            hovertemplate=(
                "Governorate: %{y}<br>"
                "Branches: %{x}"
                "<extra></extra>"
            ),
        )

        fig_governorates.update_layout(
            height=max(450, len(governorate_counts) * 28),
            xaxis_title="Number of Branches",
            yaxis_title="Governorate",
        )

        st.plotly_chart(
            fig_governorates,
            use_container_width=True,
        )
    else:
        st.info("No governorate data is available.")

    st.divider()

    # -----------------------------------------------------
    # 2. Top 5 Branches
    # Sort: Profit descending, returns ascending, branch ID
    # -----------------------------------------------------

    st.subheader("🏆 Top 5 Branches")

    ranking = (
        performance.dropna(subset=["profit"])
        .sort_values(
            ["profit", "returned_orders", "branch_id"],
            ascending=[False, True, True],
            na_position="last",
        )
        .drop_duplicates(subset=["branch_id"])
        .head(5)
        .copy()
    )

    if not ranking.empty:

        ranking.insert(
            0,
            "Rank",
            range(1, len(ranking) + 1),
        )

        ranking_display = ranking[
            [
                "Rank",
                "branch_name_ar",
                "profit",
                "returned_orders",
            ]
        ].rename(
            columns={
                "branch_name_ar": "Branch",
                "profit": "Profit (EGP)",
                "returned_orders": "Returned Orders",
            }
        )

        st.dataframe(
            ranking_display,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Rank": st.column_config.NumberColumn(
                    "Rank",
                    format="%d",
                ),
                "Profit (EGP)": st.column_config.NumberColumn(
                    "Profit (EGP)",
                    format="%,.2f",
                ),
                "Returned Orders": st.column_config.NumberColumn(
                    "Returned Orders",
                    format="%d",
                ),
            },
        )

        best_branch = ranking.iloc[0]

        st.metric(
            label=f"Highest-Profit Branch: {best_branch['branch_name_ar']}",
            value=f"{best_branch['profit']:,.2f} EGP",
            delta=f"{int(best_branch['returned_orders'])} returned orders",
            delta_color="off",
        )

    else:
        st.info("No branch performance data is available.")

    st.divider()

    # -----------------------------------------------------
    # 3. Profit Share by Governorate
    # Top 3 governorates + Others
    # -----------------------------------------------------

    st.subheader("Profit Share by Governorate")

    profit_by_governorate = (
        performance.dropna(subset=["governorate_ar", "profit"])
        .groupby("governorate_ar", as_index=False)["profit"]
        .sum()
        .sort_values("profit", ascending=False)
    )

    if not profit_by_governorate.empty:

        top_three = profit_by_governorate.head(5).copy()
        remaining_profit = profit_by_governorate.iloc[3:]["profit"].sum()

        if remaining_profit != 0:
            others_row = pd.DataFrame(
                {
                    "governorate_ar": ["Others"],
                    "profit": [remaining_profit],
                }
            )

            pie_df = pd.concat(
                [top_three, others_row],
                ignore_index=True,
            )
        else:
            pie_df = top_three

        fig_pie = px.pie(
            pie_df,
            names="governorate_ar",
            values="profit",
            hole=0.4,
            labels={
                "governorate_ar": "Governorate",
                "profit": "Profit (EGP)",
            },
            template="plotly_white",
        )

        fig_pie.update_traces(
            textposition="inside",
            textinfo="label+percent",
            hovertemplate=(
                "Governorate: %{label}<br>"
                "Profit: %{value:,.2f} EGP<br>"
                "Share: %{percent}"
                "<extra></extra>"
            ),
        )

        fig_pie.update_layout(height=450)

        st.plotly_chart(
            fig_pie,
            use_container_width=True,
        )

    else:
        st.info("No profit-by-governorate data is available.")

    st.divider()

    # -----------------------------------------------------
    # 4. Searchable Branch Selector + Yearly Margin
    # -----------------------------------------------------

    st.subheader("📈 Branch Margin Trend by Year")

    branch_options = (
        branches.dropna(subset=["branch_id", "branch_name_ar"])
        [["branch_id", "branch_name_ar"]]
        .drop_duplicates(subset=["branch_id"])
        .sort_values("branch_name_ar")
    )

    if branch_options.empty:
        st.info("No branches are available for selection.")
        return

    branch_names = dict(
        zip(
            branch_options["branch_id"],
            branch_options["branch_name_ar"],
        )
    )

    selected_branch_id = st.selectbox(
        "Search and select a branch",
        options=branch_options["branch_id"].tolist(),
        format_func=lambda branch_id: (
            f"{branch_names.get(branch_id, 'Unknown')} "
            f"({branch_id})"
        ),
    )

    selected_branch_name = branch_names.get(
        selected_branch_id,
        selected_branch_id,
    )

    branch_orders = orders[
        (orders["branch_id"] == selected_branch_id)
        & orders["order_date"].notna()
        & orders["margin_egp"].notna()
    ].copy()

    if branch_orders.empty:

        st.warning(
            f"No valid order margin data found for "
            f"{selected_branch_name}."
        )

    else:

        branch_orders["year"] = branch_orders["order_date"].dt.year

        yearly_margin = (
            branch_orders.groupby("year", as_index=False)["margin_egp"]
            .sum()
            .sort_values("year")
        )

        fig_margin = px.line(
            yearly_margin,
            x="year",
            y="margin_egp",
            markers=True,
            title=f"Yearly Margin — {selected_branch_name}",
            labels={
                "year": "Year",
                "margin_egp": "Margin (EGP)",
            },
            template="plotly_white",
        )

        fig_margin.update_traces(
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate=(
                "Year: %{x}<br>"
                "Margin: %{y:,.2f} EGP"
                "<extra></extra>"
            ),
        )

        fig_margin.update_layout(
            height=450,
            xaxis=dict(
                title="Year",
                tickmode="linear",
                dtick=1,
            ),
            yaxis=dict(
                title="Margin (EGP)",
                tickformat=",",
            ),
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_margin,
            use_container_width=True,
        )

        st.caption(
            "Yearly margin is calculated as the sum of margin_EGP "
            "for the selected branch in each calendar year."
        )



from pathlib import Path
import math

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import folium

from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from egygeo import get_coordinates


# =========================================================
# FILE PATHS
# =========================================================

BASE_DIR = Path(r"D:\HVIA\New folder\Cottonil_project\COTTONIL")

BRANCH_PERFORMANCE_PATH = BASE_DIR / "branch_performance.csv"
FACTORIES_PATH = BASE_DIR / "data" / "factories.csv"
WAREHOUSES_PATH = BASE_DIR / "data" / "warehouses.csv"


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def read_csv_clean(path):
    """Read CSV and normalize column names."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip().str.lower()
    return df


def get_coordinates_safe(governorate):
    """Return approximate governorate coordinates."""
    try:
        coords = get_coordinates(str(governorate))

        if coords is None or len(coords) < 2:
            return None

        lat = float(coords[0])
        lon = float(coords[1])

        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon

    except Exception:
        pass

    return None


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance in kilometers."""
    earth_radius = 6371

    lat1, lon1, lat2, lon2 = map(
        math.radians,
        [lat1, lon1, lat2, lon2],
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * earth_radius * math.asin(math.sqrt(a))


def add_locations(df, governorate_column="governorate_ar"):
    """Use existing coordinates when available; otherwise resolve governorates."""
    df = df.copy()

    if "latitude" not in df.columns:
        df["latitude"] = pd.NA

    if "longitude" not in df.columns:
        df["longitude"] = pd.NA

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    for idx, row in df.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]

        if pd.notna(lat) and pd.notna(lon):
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                continue

        coords = get_coordinates_safe(row[governorate_column])

        if coords is not None:
            df.at[idx, "latitude"] = coords[0]
            df.at[idx, "longitude"] = coords[1]

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    return df.dropna(subset=["latitude", "longitude"])


# =========================================================
# PAGE
# =========================================================

def warehouses_factory_recommendations_page():

    st.title("Warehouses and Factory Recommendations")

    # =====================================================
    # 1. PROFIT SHARE BY GOVERNORATE
    # =====================================================

    st.header("Profit Share by Governorate")

    try:
        branches = read_csv_clean(BRANCH_PERFORMANCE_PATH)

        required = {"profit", "governorate_ar"}

        if not required.issubset(branches.columns):
            st.error(
                "branch_performance.csv must contain "
                "'Profit' and 'governorate_ar'."
            )
            return

        branches["profit"] = pd.to_numeric(
            branches["profit"], errors="coerce"
        )

        branches["governorate_ar"] = (
            branches["governorate_ar"]
            .astype("string")
            .str.strip()
        )

        branches = branches.dropna(
            subset=["profit", "governorate_ar"]
        )

        # Aggregate profit by governorate
        profit_by_governorate = (
            branches.groupby("governorate_ar", as_index=False)["profit"]
            .sum()
            .sort_values("profit", ascending=False)
        )

        total_profit = profit_by_governorate["profit"].sum()

        if profit_by_governorate.empty or total_profit <= 0:
            st.warning(
                "Cannot calculate profit share: total profit is zero "
                "or negative."
            )
        else:
            top_7 = profit_by_governorate.head(7).copy()
            others = profit_by_governorate.iloc[7:]

            chart_data = top_7.copy()

            if not others.empty:
                chart_data = pd.concat(
                    [
                        chart_data,
                        pd.DataFrame(
                            {
                                "governorate_ar": ["Other"],
                                "profit": [others["profit"].sum()],
                            }
                        ),
                    ],
                    ignore_index=True,
                )

            chart_data["share"] = (
                chart_data["profit"] / total_profit * 100
            )

            fig = go.Figure()

            for _, row in chart_data.iterrows():
                share = row["share"]

                fig.add_trace(
                    go.Bar(
                        name=str(row["governorate_ar"]),
                        x=[share],
                        y=["Profit Share"],
                        orientation="h",
                        text=f"{share:.1f}%" if share >= 5 else "",
                        textposition="inside",
                        hovertemplate=(
                            f'<b>{row["governorate_ar"]}</b><br>'
                            f'Profit: {row["profit"]:,.2f} EGP<br>'
                            f'Share: {share:.2f}%'
                            "<extra></extra>"
                        ),
                    )
                )

            fig.update_layout(
                barmode="stack",
                title="Profit Share by Governorate",
                xaxis={
                    "title": "Share of Total Profit",
                    "range": [0, 100],
                    "ticksuffix": "%",
                },
                yaxis={"title": ""},
                height=240,
                legend={
                    "title": "Governorate",
                    "orientation": "h",
                    "yanchor": "top",
                    "y": -0.45,
                    "xanchor": "left",
                    "x": 0,
                },
                margin={"l": 20, "r": 20, "t": 60, "b": 110},
            )

            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "The chart shows the top 7 governorates by profit. "
                "All remaining governorates are grouped under Other."
            )

    except Exception as e:
        st.error(f"Could not load branch performance data: {e}")
        return

    st.divider()

    # =====================================================
    # 2. FACTORIES MAP
    # =====================================================

    st.header("Factories Map")

    try:
        factories = read_csv_clean(FACTORIES_PATH)

        if "governorate_ar" not in factories.columns:
            st.error("factories.csv must contain 'governorate_ar'.")
            return

        factories["governorate_ar"] = (
            factories["governorate_ar"]
            .astype("string")
            .str.strip()
        )

        factories = factories.dropna(
            subset=["governorate_ar"]
        )

        factories = add_locations(factories)

        if factories.empty:
            st.warning("No factory locations could be resolved.")
        else:
            factory_map = folium.Map(
                location=[26.8, 30.8],
                zoom_start=6,
                tiles="OpenStreetMap",
            )

            factory_cluster = MarkerCluster(
                name="Factories"
            ).add_to(factory_map)

            for _, factory in factories.iterrows():
                factory_name = factory.get(
                    "factory_name_ar",
                    factory.get("factory_id", "Factory"),
                )

                factory_id = factory.get("factory_id", "N/A")
                governorate = factory["governorate_ar"]
                production = factory.get("production_focus", "N/A")

                popup_html = (
                    f"<b>Factory:</b> {factory_name}<br>"
                    f"<b>ID:</b> {factory_id}<br>"
                    f"<b>Governorate:</b> {governorate}<br>"
                    f"<b>Production:</b> {production}"
                )

                folium.Marker(
                    location=[
                        factory["latitude"],
                        factory["longitude"],
                    ],
                    tooltip=str(factory_name),
                    popup=folium.Popup(
                        popup_html,
                        max_width=350,
                    ),
                    icon=folium.Icon(
                        color="red",
                        icon="industry",
                        prefix="fa",
                    ),
                ).add_to(factory_cluster)

            st_folium(
                factory_map,
                height=500,
                use_container_width=True,
                key="factories_only_map",
            )

    except Exception as e:
        st.error(f"Could not load factory data: {e}")

    st.divider()

    # =====================================================
    # 3. WAREHOUSES MAP AND DISTANCE RANKING
    # =====================================================

    st.header("Warehouses Distance Recommendations")

    try:
        warehouses = read_csv_clean(WAREHOUSES_PATH)

        if "governorate_ar" not in warehouses.columns:
            st.error("warehouses.csv must contain 'governorate_ar'.")
            return

        warehouses["governorate_ar"] = (
            warehouses["governorate_ar"]
            .astype("string")
            .str.strip()
        )

        warehouses = warehouses.dropna(
            subset=["governorate_ar"]
        ).copy()

        warehouses = add_locations(warehouses)

        if warehouses.empty:
            st.warning(
                "No warehouse locations could be resolved. "
                "Check governorate names and coordinates."
            )
        else:
            warehouse_name_column = next(
                (
                    col
                    for col in [
                        "warehouse_name_ar",
                        "warehouse_name",
                        "warehouse_id",
                        "name",
                        "id",
                    ]
                    if col in warehouses.columns
                ),
                None,
            )

            if warehouse_name_column is None:
                warehouses["_warehouse_label"] = [
                    f"Warehouse {i + 1}"
                    for i in range(len(warehouses))
                ]
                warehouse_name_column = "_warehouse_label"

            egypt_governorates = [
                "القاهرة",
                "الجيزة",
                "الإسكندرية",
                "القليوبية",
                "البحيرة",
                "مطروح",
                "دمياط",
                "الدقهلية",
                "كفر الشيخ",
                "الغربية",
                "المنوفية",
                "الشرقية",
                "الإسماعيلية",
                "بورسعيد",
                "السويس",
                "شمال سيناء",
                "جنوب سيناء",
                "بني سويف",
                "الفيوم",
                "المنيا",
                "أسيوط",
                "سوهاج",
                "قنا",
                "الأقصر",
                "أسوان",
                "البحر الأحمر",
                "الوادي الجديد",
            ]

            selected_governorate = st.selectbox(
                "Select a governorate",
                options=egypt_governorates,
                index=None,
                placeholder="Choose any governorate in Egypt",
                key="warehouse_distance_governorate",
            )

            show_lines = st.checkbox(
                "Show distance lines to warehouses",
                value=False,
                key="warehouse_distance_lines",
            )

            warehouse_map = folium.Map(
                location=[26.8, 30.8],
                zoom_start=6,
                tiles="OpenStreetMap",
            )

            warehouse_cluster = MarkerCluster(
                name="Warehouses"
            ).add_to(warehouse_map)

            for _, warehouse in warehouses.iterrows():
                warehouse_name = warehouse[warehouse_name_column]

                folium.Marker(
                    location=[
                        warehouse["latitude"],
                        warehouse["longitude"],
                    ],
                    tooltip=str(warehouse_name),
                    popup=folium.Popup(
                        (
                            f"<b>Warehouse:</b> {warehouse_name}<br>"
                            f"<b>Governorate:</b> "
                            f'{warehouse["governorate_ar"]}'
                        ),
                        max_width=300,
                    ),
                    icon=folium.Icon(
                        color="blue",
                        icon="home",
                        prefix="fa",
                    ),
                ).add_to(warehouse_cluster)

            if selected_governorate is not None:
                selected_coords = get_coordinates_safe(
                    selected_governorate
                )

                if selected_coords is None:
                    st.warning(
                        "Could not find coordinates for the selected "
                        "governorate. Check the governorate name."
                    )
                else:
                    selected_lat, selected_lon = selected_coords

                    folium.Marker(
                        location=[selected_lat, selected_lon],
                        tooltip=f"Selected: {selected_governorate}",
                        popup=f"Starting point: {selected_governorate}",
                        icon=folium.Icon(
                            color="green",
                            icon="star",
                            prefix="fa",
                        ),
                    ).add_to(warehouse_map)

                    warehouses["distance_km"] = warehouses.apply(
                        lambda row: haversine_km(
                            selected_lat,
                            selected_lon,
                            row["latitude"],
                            row["longitude"],
                        ),
                        axis=1,
                    )

                    warehouses = warehouses.sort_values(
                        ["distance_km", warehouse_name_column],
                        ascending=[True, True],
                    ).reset_index(drop=True)

                    warehouses["rank"] = range(
                        1, len(warehouses) + 1
                    )

                    if show_lines:
                        for _, warehouse in warehouses.iterrows():
                            folium.PolyLine(
                                locations=[
                                    [selected_lat, selected_lon],
                                    [
                                        warehouse["latitude"],
                                        warehouse["longitude"],
                                    ],
                                ],
                                color="blue",
                                weight=2,
                                opacity=0.65,
                                dash_array="5, 8",
                            ).add_to(warehouse_map)

                    warehouse_map.location = [
                        selected_lat,
                        selected_lon,
                    ]

            st_folium(
                warehouse_map,
                height=500,
                use_container_width=True,
                key="warehouse_locations_map",
            )

            if (
                selected_governorate is not None
                and "distance_km" in warehouses.columns
            ):
                st.subheader(
                    f"Warehouse Ranking from {selected_governorate}"
                )

                nearest = warehouses.iloc[0]

                col1, col2 = st.columns(2)

                col1.metric(
                    "Nearest Warehouse",
                    str(nearest[warehouse_name_column]),
                )

                col2.metric(
                    "Approx. Distance",
                    f'{nearest["distance_km"]:.2f} km',
                )

                result = warehouses[
                    [
                        "rank",
                        warehouse_name_column,
                        "governorate_ar",
                        "distance_km",
                    ]
                ].rename(
                    columns={
                        "rank": "Rank",
                        warehouse_name_column: "Warehouse",
                        "governorate_ar": "Warehouse Governorate",
                        "distance_km": "Approx. Distance (km)",
                    }
                )

                result["Approx. Distance (km)"] = result[
                    "Approx. Distance (km)"
                ].round(2)

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True,
                )

    except Exception as e:
        st.error(f"Could not load warehouse data: {e}")

    st.divider()

    # =====================================================
    # 4. BUSINESS RECOMMENDATIONS
    # =====================================================

    st.header("Business Recommendations")

    st.markdown(
        """
        ### 1. Manufacturing Strategy

        Our manufacturing facilities are concentrated in the Nile Delta,
        supporting our cotton-based textile operations and benefiting from
        the region's established agricultural and industrial ecosystem.

        ### 2. Distribution Strategy

        Our branch network is concentrated in areas with strong sales
        activity, helping us serve existing demand. However, our presence
        in Upper Egypt remains limited, creating an opportunity to expand
        our geographic coverage.

        ### 3. Recommended Expansion: Minya

        We recommend considering Minya as a strategic distribution hub
        for Upper Egypt. Its location could improve access to nearby
        governorates, expand our customer reach, and support more efficient
        distribution.

        Before implementation, validate this recommendation using
        branch-level sales, customer demand, transportation costs,
        forecast demand, and the availability of suitable locations.
        """
    )

    st.caption(
        "Distances are approximate straight-line distances, not road "
        "travel distances. If only governorate names are available, "
        "locations represent approximate governorate centers."
    )

def customer_segmentation_page():

    import streamlit as st
    import pandas as pd
    import joblib
    import plotly.express as px
    from rfm_utils import calculate_rfm

    st.title("Customer Segmentation")
    st.markdown(
        "Upload new customer transactions to predict their RFM segments."
    )

    # ------------------------------------------
    # Segment Mapping
    # ------------------------------------------

    segment_names = {
        0: 'Lost / Inactive Customers',
        1: 'High-Value Loyal Customers',
        2: 'Regular Customers',
        3: 'VIP / Premium Customers',
        4: 'Potential Loyal Customers'
    }

    # ------------------------------------------
    # Load Trained Pipeline
    # ------------------------------------------

    @st.cache_resource
    def load_pipeline():
        return joblib.load('rfm_segmentation_pipeline.joblib')

    # ------------------------------------------
    # Upload CSV
    # ------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload New Transactions CSV",
        type=["csv"],
        key="segmentation_upload"
    )

    if uploaded_file is None:
        st.info("Upload a transactions CSV file to start.")
        return

    new_transactions = pd.read_csv(uploaded_file)

    st.write(f"**Uploaded Transactions:** {len(new_transactions):,}")

    with st.expander("Preview Uploaded Data"):
        st.dataframe(new_transactions.head(), use_container_width=True)

    # ------------------------------------------
    # Run Segmentation
    # ------------------------------------------

    if st.button("Run Customer Segmentation", type="primary"):

        try:
            with st.spinner("Processing customer transactions..."):

                loaded_pipeline = load_pipeline()

                # Calculate RFM
                new_rfm = calculate_rfm(new_transactions)

                # Predict clusters
                predictions = loaded_pipeline.predict(new_rfm)

                # Generate results
                results = new_rfm.copy()

                results['cluster'] = predictions

                results['segment'] = results['cluster'].map(
                    segment_names
                )

                # Segment distribution
                segment_counts = (
                    results['segment']
                    .value_counts()
                    .reindex(segment_names.values(), fill_value=0)
                    .rename_axis('Segment')
                    .reset_index(name='Customers')
                )

                segment_counts['Percentage'] = (
                    segment_counts['Customers'] /
                    segment_counts['Customers'].sum()
                ) * 100

                # Save results in session state
                st.session_state['segmentation_results'] = results
                st.session_state['segment_counts'] = segment_counts

        except Exception as e:
            st.error(f"Segmentation Error: {e}")

    # ------------------------------------------
    # Display Results
    # ------------------------------------------

    if 'segmentation_results' in st.session_state:

        results = st.session_state['segmentation_results']
        segment_counts = st.session_state['segment_counts']

        st.divider()

        st.subheader("Customer Segment Distribution")

        col1, col2 = st.columns([2, 1])

        with col1:

            fig = px.pie(
                segment_counts,
                names='Segment',
                values='Customers',
                hole=0.4,
                title='Customer Distribution by Segment',
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            fig.update_traces(
                textposition='inside',
                textinfo='percent+label'
            )

            fig.update_layout(height=500)

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col2:

            st.markdown("### Segment Summary")

            st.dataframe(
                segment_counts.style.format({
                    'Customers': '{:,.0f}',
                    'Percentage': '{:.2f}%'
                }),
                use_container_width=True,
                hide_index=True
            )

            st.metric(
                "Total Customers",
                f"{len(results):,}"
            )

            st.metric(
                "Identified Segments",
                results['segment'].nunique()
            )

        # --------------------------------------
        # Results Table
        # --------------------------------------

        st.subheader("Customer Segmentation Results")

        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True
        )

        # --------------------------------------
        # Download Results
        # --------------------------------------

        csv = results.to_csv(index=True).encode('utf-8-sig')

        st.download_button(
            "Download Segmentation Results",
            data=csv,
            file_name="customer_segmentation_results.csv",
            mime="text/csv",
            type="primary"
        )


# =========================================================
# Streamlit Navigation
# =========================================================

pages = [
    st.Page(
        overview_page,
        title="Overview",
        icon="📊",
        default=True,
    ),
    st.Page(
        branches_page,
        title="Branches",
        icon="🏢",
    ),
st.Page(
    warehouses_factory_recommendations_page,
    title="Warehouses and Factory Recommendations",
    icon="🏭",
),
    st.Page(
        customer_segmentation_page,
        title="Customer Segmentation",
        icon="👥",
    )
]

navigation = st.navigation(pages)
navigation.run()


