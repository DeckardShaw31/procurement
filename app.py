import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import io

# Page Configuration
st.set_page_config(
    page_title="Procurement & Direct Material Budget Planner",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #38bdf8;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-sub {
        color: #cbd5e1;
        font-size: 0.8rem;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DEFAULT DATA & PRESET SCENARIOS
# ==============================================================================
BASE_BOM = [
    {"Item": "Substrate", "Quantity per CPU": 1, "Price (USD)": 3.00},
    {"Item": "Capacitor A", "Quantity per CPU": 10, "Price (USD)": 0.10},
    {"Item": "Capacitor B", "Quantity per CPU": 4, "Price (USD)": 0.10},
    {"Item": "Solder ball", "Quantity per CPU": 30, "Price (USD)": 0.05},
    {"Item": "Die", "Quantity per CPU": 1, "Price (USD)": 10.00},
]

SCENARIOS = {
    "Base Case (Case Study)": {
        "capacity_per_qtr": 1_000_000,
        "lead_time_weeks": 5,
        "scrap_rate": 0.0,
        "safety_stock": 0.0,
        "price_factor": 0.0,
        "cadence": "Quarterly",
        "description": "Standard case study: 1M CPUs/quarter, 5-week overseas lead time, 100% yield."
    },
    "Scenario 1: High Demand Surge (+25%)": {
        "capacity_per_qtr": 1_250_000,
        "lead_time_weeks": 5,
        "scrap_rate": 0.0,
        "safety_stock": 0.0,
        "price_factor": 0.0,
        "cadence": "Quarterly",
        "description": "Production ramp-up to 1.25M CPUs/quarter due to strong customer orders."
    },
    "Scenario 2: Port & Shipping Congestion (Lead Time 8 wks)": {
        "capacity_per_qtr": 1_000_000,
        "lead_time_weeks": 8,
        "scrap_rate": 0.0,
        "safety_stock": 5.0,
        "price_factor": 0.0,
        "cadence": "Quarterly",
        "description": "Global freight delay increases lead time to 8 weeks, plus 5% safety buffer."
    },
    "Scenario 3: Semiconductor Price Inflation (+15%)": {
        "capacity_per_qtr": 1_000_000,
        "lead_time_weeks": 5,
        "scrap_rate": 0.0,
        "safety_stock": 0.0,
        "price_factor": 15.0,
        "cadence": "Quarterly",
        "description": "Raw material cost surge increases all component prices by 15%."
    },
    "Scenario 4: Production Scrap & Quality Buffer (3% scrap + 5% buffer)": {
        "capacity_per_qtr": 1_000_000,
        "lead_time_weeks": 5,
        "scrap_rate": 3.0,
        "safety_stock": 5.0,
        "price_factor": 0.0,
        "cadence": "Quarterly",
        "description": "Assembly line yields 97% (3% defect rate) requiring 3% extra parts + 5% buffer."
    },
    "Scenario 5: Lean JIT Monthly Replenishment": {
        "capacity_per_qtr": 1_000_000,
        "lead_time_weeks": 5,
        "scrap_rate": 0.0,
        "safety_stock": 0.0,
        "price_factor": 0.0,
        "cadence": "Monthly",
        "description": "Order monthly (~333,333 CPUs/month) to reduce warehouse footprint & cash tie-up."
    }
}

# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    st.title("⚙️ Scenario Controls")
    
    # Preset Selector
    selected_preset = st.selectbox(
        "Load Predefined Scenario:",
        list(SCENARIOS.keys()) + ["Custom Scenario"],
        index=0
    )
    
    if selected_preset != "Custom Scenario":
        preset_info = SCENARIOS[selected_preset]
        st.info(f"💡 **{selected_preset}**:\n{preset_info['description']}")
        default_capacity = preset_info["capacity_per_qtr"]
        default_lead_time = preset_info["lead_time_weeks"]
        default_scrap = preset_info["scrap_rate"]
        default_safety = preset_info["safety_stock"]
        default_price_factor = preset_info["price_factor"]
        default_cadence = preset_info["cadence"]
    else:
        default_capacity = 1_000_000
        default_lead_time = 5
        default_scrap = 0.0
        default_safety = 0.0
        default_price_factor = 0.0
        default_cadence = "Quarterly"

    st.subheader("1. Production Parameters")
    capacity_per_qtr = st.number_input(
        "Capacity per Quarter (CPUs):",
        min_value=10_000,
        max_value=10_000_000,
        value=int(default_capacity),
        step=50_000,
        format="%d"
    )
    
    start_date = st.date_input(
        "Line Startup Date:",
        value=datetime(2027, 1, 1)
    )

    cadence = st.radio(
        "Purchasing Cadence:",
        options=["Quarterly", "Monthly"],
        index=0 if default_cadence == "Quarterly" else 1,
        help="Quarterly batching (4 orders/year) vs Monthly replenishment (12 orders/year)"
    )

    st.subheader("2. Supply Chain & Lead Time")
    lead_time_weeks = st.slider(
        "Overseas Lead Time (Weeks):",
        min_value=1,
        max_value=20,
        value=int(default_lead_time),
        help="Weeks required from PO issuance to factory delivery at Saigon Hi-Tech Park"
    )

    st.subheader("3. Operational Buffers")
    col_scrap, col_safety = st.columns(2)
    with col_scrap:
        scrap_rate_pct = st.number_input(
            "Scrap / Loss %:",
            min_value=0.0,
            max_value=20.0,
            value=float(default_scrap),
            step=0.5
        )
    with col_safety:
        safety_stock_pct = st.number_input(
            "Safety Stock %:",
            min_value=0.0,
            max_value=50.0,
            value=float(default_safety),
            step=1.0
        )

    st.subheader("4. Global Price Adjustment")
    price_adj_pct = st.slider(
        "Material Price Inflation/Deflation %:",
        min_value=-50.0,
        max_value=100.0,
        value=float(default_price_factor),
        step=1.0
    )

# ==============================================================================
# MAIN PAGE HEADER & TABS
# ==============================================================================
st.title("🏭 CPU Production Line: Material Budget & Purchasing Plan")
st.markdown("""
**ABC Company — Saigon Hi-Tech Park (SHTP)** | Dynamic Scenario Modeling Tool for Direct Material Procurement.
""")

tab_overview, tab_bom, tab_schedule, tab_compare = st.tabs([
    "📊 Executive Summary",
    "📋 Interactive BOM & Costing",
    "📅 PO Release Timeline",
    "🔄 Scenario Comparison"
])

# ==============================================================================
# TAB 2: INTERACTIVE BOM (Defined early so users can edit)
# ==============================================================================
with tab_bom:
    st.subheader("Interactive Bill of Materials (BOM)")
    st.caption("You can edit quantities, prices, or add/remove components in the table below to simulate engineering changes.")
    
    # Session state for BOM table
    if "bom_table" not in st.session_state:
        st.session_state.bom_table = pd.DataFrame(BASE_BOM)

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("🔄 Reset BOM to Default"):
            st.session_state.bom_table = pd.DataFrame(BASE_BOM)
            st.rerun()

    edited_bom = st.data_editor(
        st.session_state.bom_table,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Item": st.column_config.TextColumn("Direct Material Item", required=True),
            "Quantity per CPU": st.column_config.NumberColumn("Qty per CPU", min_value=0.01, format="%.2f", required=True),
            "Price (USD)": st.column_config.NumberColumn("Unit Price (USD)", min_value=0.0001, format="$%.4f", required=True),
        }
    )
    st.session_state.bom_table = edited_bom

# ==============================================================================
# CALCULATIONS
# ==============================================================================
df_calc_bom = edited_bom.copy()
# Apply price adjustment percentage
df_calc_bom["Adjusted Price (USD)"] = df_calc_bom["Price (USD)"] * (1 + price_adj_pct / 100.0)

# Multiplier for scrap and safety stock
# Gross Qty = Net Qty * (1 + Scrap%) * (1 + Safety Stock%)
buffer_multiplier = (1 + scrap_rate_pct / 100.0) * (1 + safety_stock_pct / 100.0)

df_calc_bom["Gross Qty per CPU"] = df_calc_bom["Quantity per CPU"] * buffer_multiplier
df_calc_bom["Unit Material Cost (USD)"] = df_calc_bom["Gross Qty per CPU"] * df_calc_bom["Adjusted Price (USD)"]

base_unit_material_cost = (df_calc_bom["Quantity per CPU"] * df_calc_bom["Adjusted Price (USD)"]).sum()
gross_unit_material_cost = df_calc_bom["Unit Material Cost (USD)"].sum()

# Annual Units
annual_cpu_capacity = capacity_per_qtr * 4

# Purchasing calculations
if cadence == "Quarterly":
    cycles_per_year = 4
    batch_cpu_qty = capacity_per_qtr
    cycle_names = ["Q1 2027", "Q2 2027", "Q3 2027", "Q4 2027"]
    arrival_dates = [
        datetime(start_date.year, 1, 1),
        datetime(start_date.year, 4, 1),
        datetime(start_date.year, 7, 1),
        datetime(start_date.year, 10, 1),
    ]
else:
    cycles_per_year = 12
    batch_cpu_qty = annual_cpu_capacity / 12
    cycle_names = [f"Month {m} ({datetime(start_date.year, m, 1).strftime('%b %Y')})" for m in range(1, 13)]
    arrival_dates = [datetime(start_date.year, m, 1) for m in range(1, 13)]

lead_time_td = timedelta(days=lead_time_weeks * 7)

# Build Detailed Schedule DataFrame
schedule_records = []
for name, arr_date in zip(cycle_names, arrival_dates):
    po_date = arr_date - lead_time_td
    cycle_cost = batch_cpu_qty * gross_unit_material_cost
    schedule_records.append({
        "Period": name,
        "Production Target (CPUs)": round(batch_cpu_qty),
        "PO Release Date": po_date.strftime("%Y-%m-%d (%a)"),
        "PO Release (Raw)": po_date,
        "Material Arrival Date": arr_date.strftime("%Y-%m-%d (%a)"),
        "Lead Time": f"{lead_time_weeks} weeks ({lead_time_weeks*7} days)",
        "Purchasing Spend (USD)": cycle_cost
    })

df_schedule = pd.DataFrame(schedule_records)
annual_procurement_budget = df_schedule["Purchasing Spend (USD)"].sum()
first_po_date = df_schedule.iloc[0]["PO Release Date"]

# Component breakdown for annual production
df_calc_bom["Quarterly Requirement (Units)"] = df_calc_bom["Gross Qty per CPU"] * capacity_per_qtr
df_calc_bom["Annual Requirement (Units)"] = df_calc_bom["Gross Qty per CPU"] * annual_cpu_capacity
df_calc_bom["Quarterly Budget (USD)"] = df_calc_bom["Quarterly Requirement (Units)"] * df_calc_bom["Adjusted Price (USD)"]
df_calc_bom["Annual Budget (USD)"] = df_calc_bom["Annual Requirement (Units)"] * df_calc_bom["Adjusted Price (USD)"]
df_calc_bom["Cost Share (%)"] = (df_calc_bom["Annual Budget (USD)"] / annual_procurement_budget) * 100

# ==============================================================================
# TAB 1: EXECUTIVE SUMMARY
# ==============================================================================
with tab_overview:
    # Metric KPI cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Unit Material Cost</div>
            <div class="metric-value">${gross_unit_material_cost:,.2f}</div>
            <div class="metric-sub">Base: ${base_unit_material_cost:,.2f} / CPU</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Annual Budget</div>
            <div class="metric-value">${annual_procurement_budget:,.2f}</div>
            <div class="metric-sub">{annual_cpu_capacity:,.0f} CPUs in {start_date.year}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Initial PO Deadline</div>
            <div class="metric-value" style="color: #f59e0b; font-size: 1.4rem;">{df_schedule.iloc[0]['PO Release (Raw)'].strftime('%d %b %Y')}</div>
            <div class="metric-sub">{lead_time_weeks} weeks prior to {start_date.strftime('%d %b %Y')}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Cadence Spend</div>
            <div class="metric-value">${df_schedule.iloc[0]['Purchasing Spend (USD)']:,.2f}</div>
            <div class="metric-sub">Per {cadence.lower()} batch ({len(df_schedule)} cycles/yr)</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Visual Charts
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Component Cost Breakdown (% Share)")
        fig_donut = px.pie(
            df_calc_bom,
            names="Item",
            values="Annual Budget (USD)",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
        st.plotly_chart(fig_donut, use_container_width=True)

    with c2:
        st.subheader("Purchasing Spend by Period")
        fig_bar = px.bar(
            df_schedule,
            x="Period",
            y="Purchasing Spend (USD)",
            text_auto='.2s',
            color="Purchasing Spend (USD)",
            color_continuous_scale="Blues"
        )
        fig_bar.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=350,
            xaxis_title="",
            yaxis_title="Spend (USD)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Direct Material Annual Budget Table")
    display_budget = df_calc_bom[[
        "Item", "Quantity per CPU", "Adjusted Price (USD)", "Gross Qty per CPU",
        "Quarterly Requirement (Units)", "Annual Requirement (Units)",
        "Quarterly Budget (USD)", "Annual Budget (USD)", "Cost Share (%)"
    ]].copy()
    
    st.dataframe(
        display_budget.style.format({
            "Adjusted Price (USD)": "${:,.4f}",
            "Gross Qty per CPU": "{:,.2f}",
            "Quarterly Requirement (Units)": "{:,.0f}",
            "Annual Requirement (Units)": "{:,.0f}",
            "Quarterly Budget (USD)": "${:,.2f}",
            "Annual Budget (USD)": "${:,.2f}",
            "Cost Share (%)": "{:,.1f}%"
        }),
        use_container_width=True
    )

# ==============================================================================
# TAB 3: PO RELEASE TIMELINE & SCHEDULE
# ==============================================================================
with tab_schedule:
    st.subheader(f"Purchasing Schedule & Milestone Timeline ({cadence} Cadence)")
    st.info(f"🚚 Overseas lead time is **{lead_time_weeks} weeks ({lead_time_weeks * 7} days)**. Orders must be officially issued to suppliers on the **PO Release Date** for materials to arrive at Saigon Hi-Tech Park in time.")

    # Timeline view with Plotly Gantt-style
    df_gantt = []
    for _, row in df_schedule.iterrows():
        df_gantt.append({
            "Task": f"{row['Period']}: Overseas Transit",
            "Start": row["PO Release (Raw)"],
            "Finish": datetime.strptime(row["Material Arrival Date"].split(" ")[0], "%Y-%m-%d"),
            "Phase": "Lead Time Transit",
            "Spend": f"${row['Purchasing Spend (USD)']:,.0f}"
        })
    df_gantt_plot = pd.DataFrame(df_gantt)
    
    fig_timeline = px.timeline(
        df_gantt_plot,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Phase",
        hover_data=["Spend"],
        color_discrete_map={"Lead Time Transit": "#0284c7"}
    )
    fig_timeline.update_yaxes(autorange="reversed")
    fig_timeline.update_layout(height=280, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_timeline, use_container_width=True)

    # Detailed Schedule Table
    st.dataframe(
        df_schedule[[
            "Period", "PO Release Date", "Material Arrival Date",
            "Production Target (CPUs)", "Lead Time", "Purchasing Spend (USD)"
        ]].style.format({
            "Production Target (CPUs)": "{:,.0f}",
            "Purchasing Spend (USD)": "${:,.2f}"
        }),
        use_container_width=True
    )

    # Excel Download
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_calc_bom.to_excel(writer, sheet_name="Material Budget", index=False)
        df_schedule.drop(columns=["PO Release (Raw)"]).to_excel(writer, sheet_name="Purchasing Schedule", index=False)
    
    st.download_button(
        label="📥 Download Procurement Plan as Excel (.xlsx)",
        data=excel_buffer.getvalue(),
        file_name=f"Procurement_Plan_2027_{cadence}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==============================================================================
# TAB 4: SCENARIO COMPARISON MATRIX
# ==============================================================================
with tab_compare:
    st.subheader("Side-by-Side Multi-Scenario Sensitivity Analysis")
    st.caption("Compare how key variables (volume, price spikes, scrap rates, and buffer stocks) alter the total budget and cash requirements.")

    comparison_results = []
    for sc_name, sc_data in SCENARIOS.items():
        sc_cap = sc_data["capacity_per_qtr"]
        sc_ann_cap = sc_cap * 4
        sc_lead = sc_data["lead_time_weeks"]
        sc_buf = (1 + sc_data["scrap_rate"]/100.0) * (1 + sc_data["safety_stock"]/100.0)
        sc_price_factor = 1 + sc_data["price_factor"]/100.0
        
        # Unit cost
        sc_unit_cost = sum(item["Quantity per CPU"] * sc_buf * item["Price (USD)"] * sc_price_factor for item in BASE_BOM)
        sc_ann_budget = sc_ann_cap * sc_unit_cost
        
        # First PO date
        sc_arr = datetime(2027, 1, 1)
        sc_po = sc_arr - timedelta(days=sc_lead * 7)
        
        comparison_results.append({
            "Scenario": sc_name,
            "Quarterly Qty": sc_cap,
            "Annual Qty": sc_ann_cap,
            "Lead Time (wks)": sc_lead,
            "Buffer (Scrap+Safety)": f"{(sc_buf - 1)*100:.1f}%",
            "Price Δ": f"{sc_data['price_factor']:+.0f}%",
            "Unit Material Cost": sc_unit_cost,
            "Annual Budget (USD)": sc_ann_budget,
            "Budget Variance vs Base": sc_ann_budget - (4_000_000 * 15.90),
            "Initial PO Date": sc_po.strftime("%Y-%m-%d")
        })

    df_comp = pd.DataFrame(comparison_results)
    
    st.dataframe(
        df_comp.style.format({
            "Quarterly Qty": "{:,.0f}",
            "Annual Qty": "{:,.0f}",
            "Unit Material Cost": "${:,.2f}",
            "Annual Budget (USD)": "${:,.2f}",
            "Budget Variance vs Base": lambda x: f"{'+' if x>0 else ''}${x:,.2f}"
        }),
        use_container_width=True
    )

    fig_comp = px.bar(
        df_comp,
        x="Scenario",
        y="Annual Budget (USD)",
        color="Annual Budget (USD)",
        text_auto='.3s',
        color_continuous_scale="Viridis",
        title="Annual Budget by Scenario ($ USD)"
    )
    fig_comp.update_layout(xaxis_tickangle=-25, margin=dict(t=40, b=40, l=20, r=20))
    st.plotly_chart(fig_comp, use_container_width=True)
