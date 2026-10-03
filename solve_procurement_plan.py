"""
Procurement Budget and Purchasing Plan for ABC Company (Saigon Hi-Tech Park)
Case Study: 2027 CPU Assembly Line
"""

import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. PARAMETERS & INPUT DATA
# ==========================================
CAPACITY_PER_QUARTER = 1_000_000  # 1 million CPUs per quarter
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
ANNUAL_CAPACITY = CAPACITY_PER_QUARTER * len(QUARTERS)  # 4 million CPUs
LEAD_TIME_WEEKS = 5
LEAD_TIME_DAYS = LEAD_TIME_WEEKS * 7  # 35 days

# Bill of Materials (BOM)
bom_data = [
    {"item": "Substrate", "qty_per_cpu": 1, "unit_price": 3.00},
    {"item": "Capacitor A", "qty_per_cpu": 10, "unit_price": 0.10},
    {"item": "Capacitor B", "qty_per_cpu": 4, "unit_price": 0.10},
    {"item": "Solder ball", "qty_per_cpu": 30, "unit_price": 0.05},
    {"item": "Die", "qty_per_cpu": 1, "unit_price": 10.00},
]

df_bom = pd.DataFrame(bom_data)
df_bom["cost_per_cpu"] = df_bom["qty_per_cpu"] * df_bom["unit_price"]

unit_material_cost = df_bom["cost_per_cpu"].sum()

# ==========================================
# 2. BUDGET CALCULATION
# ==========================================
# Quarterly budget per item
df_budget = df_bom.copy()
df_budget["quarterly_qty"] = df_budget["qty_per_cpu"] * CAPACITY_PER_QUARTER
df_budget["quarterly_cost"] = df_budget["quarterly_qty"] * df_budget["unit_price"]

# Annual budget per item (4 quarters)
df_budget["annual_qty"] = df_budget["quarterly_qty"] * len(QUARTERS)
df_budget["annual_cost"] = df_budget["quarterly_cost"] * len(QUARTERS)

quarterly_total_cost = df_budget["quarterly_cost"].sum()
annual_total_cost = df_budget["annual_cost"].sum()

# ==========================================
# 3. PURCHASING PLAN (QUARTERLY SCHEDULE)
# ==========================================
# Schedule dates for 2027:
# Lead time = 5 weeks (35 days) before production start
quarter_dates = [
    {"quarter": "Q1 2027", "required_date": datetime(2027, 1, 1)},
    {"quarter": "Q2 2027", "required_date": datetime(2027, 4, 1)},
    {"quarter": "Q3 2027", "required_date": datetime(2027, 7, 1)},
    {"quarter": "Q4 2027", "required_date": datetime(2027, 10, 1)},
]

quarterly_po_schedule = []
for q in quarter_dates:
    po_date = q["required_date"] - timedelta(days=LEAD_TIME_DAYS)
    quarterly_po_schedule.append({
        "Quarter": q["quarter"],
        "CPU Production (Units)": CAPACITY_PER_QUARTER,
        "PO Release Date (-5 wks)": po_date.strftime("%Y-%m-%d (%A)"),
        "Material Arrival / Production Date": q["required_date"].strftime("%Y-%m-%d (%A)"),
        "Quarterly Purchasing Budget (USD)": quarterly_total_cost
    })

df_quarterly_schedule = pd.DataFrame(quarterly_po_schedule)

# Detailed Quarterly Purchase Quantity by Item
detailed_orders = []
for q in quarter_dates:
    po_date = q["required_date"] - timedelta(days=LEAD_TIME_DAYS)
    for _, row in df_bom.iterrows():
        detailed_orders.append({
            "Quarter": q["quarter"],
            "PO Release Date": po_date.strftime("%Y-%m-%d"),
            "Arrival Date": q["required_date"].strftime("%Y-%m-%d"),
            "Item": row["item"],
            "Unit Price (USD)": row["unit_price"],
            "Order Quantity": row["qty_per_cpu"] * CAPACITY_PER_QUARTER,
            "Total Amount (USD)": row["qty_per_cpu"] * CAPACITY_PER_QUARTER * row["unit_price"]
        })

df_detailed_orders = pd.DataFrame(detailed_orders)

# ==========================================
# 4. PURCHASING PLAN (MONTHLY REPLENISHMENT ALTERNATIVE)
# ==========================================
monthly_capacity = CAPACITY_PER_QUARTER / 3  # ~333,333.33 CPUs per month
monthly_dates = [datetime(2027, m, 1) for m in range(1, 13)]
monthly_po_schedule = []

for m_date in monthly_dates:
    po_date = m_date - timedelta(days=LEAD_TIME_DAYS)
    monthly_po_schedule.append({
        "Month": m_date.strftime("%B %Y"),
        "PO Release Date (-5 wks)": po_date.strftime("%Y-%m-%d"),
        "Required Date": m_date.strftime("%Y-%m-%d"),
        "Production Target (CPUs)": round(monthly_capacity),
        "Estimated Spend (USD)": monthly_capacity * unit_material_cost
    })

df_monthly_schedule = pd.DataFrame(monthly_po_schedule)

# ==========================================
# 5. PRINT REPORT TO CONSOLE
# ==========================================
def print_report():
    print("=" * 80)
    print("      CASE STUDY: DIRECT MATERIAL BUDGET & PURCHASING PLAN (2027)")
    print("      ABC Company - Saigon Hi-Tech Park | Assembly Line Setup")
    print("=" * 80)
    print(f"Capacity per quarter: {CAPACITY_PER_QUARTER:,.0f} CPUs")
    print(f"Total 2027 capacity (4 quarters): {ANNUAL_CAPACITY:,.0f} CPUs")
    print(f"Lead time: {LEAD_TIME_WEEKS} weeks ({LEAD_TIME_DAYS} days)")
    print(f"Unit Direct Material Cost: ${unit_material_cost:.2f} USD / CPU\n")

    print("-" * 80)
    print("1. BILL OF MATERIALS (BOM) & UNIT COST BREAKDOWN")
    print("-" * 80)
    bom_display = df_bom[["item", "qty_per_cpu", "unit_price", "cost_per_cpu"]].copy()
    bom_display.columns = ["Item", "Qty / CPU", "Unit Price ($)", "Cost / CPU ($)"]
    print(bom_display.to_string(index=False))
    print(f"\n>>> Total Material Cost per CPU: ${unit_material_cost:.2f} USD\n")

    print("-" * 80)
    print("2. DIRECT MATERIAL BUDGET (QUARTERLY & ANNUAL 2027)")
    print("-" * 80)
    budget_display = df_budget[["item", "qty_per_cpu", "unit_price", "quarterly_qty", "quarterly_cost", "annual_qty", "annual_cost"]].copy()
    budget_display.columns = ["Item", "Qty/CPU", "Unit Price", "Qtr Qty", "Qtr Budget ($)", "Annual Qty", "Annual Budget ($)"]
    
    # Format numbers
    budget_display["Unit Price"] = budget_display["Unit Price"].map("${:,.2f}".format)
    budget_display["Qtr Qty"] = budget_display["Qtr Qty"].map("{:,.0f}".format)
    budget_display["Qtr Budget ($)"] = budget_display["Qtr Budget ($)"].map("${:,.2f}".format)
    budget_display["Annual Qty"] = budget_display["Annual Qty"].map("{:,.0f}".format)
    budget_display["Annual Budget ($)"] = budget_display["Annual Budget ($)"].map("${:,.2f}".format)
    
    print(budget_display.to_string(index=False))
    print("-" * 80)
    print(f"Total Quarterly Budget : ${quarterly_total_cost:,.2f} USD")
    print(f"Total Annual Budget    : ${annual_total_cost:,.2f} USD\n")

    print("-" * 80)
    print("3. QUARTERLY PURCHASING PLAN & PO RELEASE TIMELINE (5-WEEK LEAD TIME)")
    print("-" * 80)
    sched_display = df_quarterly_schedule.copy()
    sched_display["CPU Production (Units)"] = sched_display["CPU Production (Units)"].map("{:,.0f}".format)
    sched_display["Quarterly Purchasing Budget (USD)"] = sched_display["Quarterly Purchasing Budget (USD)"].map("${:,.2f}".format)
    print(sched_display.to_string(index=False))
    print("\n* Note: To start production on Jan 1, 2027, the initial PO must be placed on Nov 27, 2026.")

    print("\n" + "-" * 80)
    print("4. MONTHLY REPLENISHMENT SCHEDULE (ALTERNATIVE FOR JIT/SMOOTHER CASH FLOW)")
    print("-" * 80)
    monthly_display = df_monthly_schedule.copy()
    monthly_display["Production Target (CPUs)"] = monthly_display["Production Target (CPUs)"].map("{:,.0f}".format)
    monthly_display["Estimated Spend (USD)"] = monthly_display["Estimated Spend (USD)"].map("${:,.2f}".format)
    print(monthly_display.to_string(index=False))

# ==========================================
# 6. EXPORT TO EXCEL
# ==========================================
def export_to_excel(filename="procurement_budget_plan_2027.xlsx"):
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df_bom.to_excel(writer, sheet_name="BOM & Unit Cost", index=False)
        df_budget.to_excel(writer, sheet_name="Material Budget", index=False)
        df_quarterly_schedule.to_excel(writer, sheet_name="Quarterly Purchasing Plan", index=False)
        df_detailed_orders.to_excel(writer, sheet_name="PO Order Details", index=False)
        df_monthly_schedule.to_excel(writer, sheet_name="Monthly Purchasing Plan", index=False)
    print(f"\n[OK] Excel workbook exported successfully to '{filename}'")

if __name__ == "__main__":
    print_report()
    export_to_excel()
