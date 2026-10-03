# Direct Material Procurement & Budget Simulation Engine

> **Case Study**: ABC Company in Saigon Hi-Tech Park (SHTP) sets up a new assembly line with maximum capacity of **1,000,000 CPUs per quarter**, starting operations on **1st January 2027** at full capacity. All items are imported overseas with a **lead time of 5 weeks**.

---

## 📌 Executive Summary & Key Results

### 1. Bill of Materials (BOM) & Unit Direct Material Cost
| Item | Quantity per CPU | Unit Price (USD) | Cost per CPU (USD) |
| :--- | :---: | :---: | :---: |
| **Substrate** | 1 | $3.00 | $3.00 |
| **Capacitor A** | 10 | $0.10 | $1.00 |
| **Capacitor B** | 4 | $0.10 | $0.40 |
| **Solder ball** | 30 | $0.05 | $1.50 |
| **Die** | 1 | $10.00 | $10.00 |
| **Total Unit Cost** | — | — | **$15.90 USD** |

### 2. Direct Material Budget (2027)
* **Quarterly Budget** (1,000,000 CPUs): **$15,900,000 USD**
* **Annual Budget** (4 Quarters = 4,000,000 CPUs): **$63,600,000 USD**

| Item | Qty / CPU | Price | Quarterly Qty | Quarterly Budget ($) | Annual Qty (2027) | Annual Budget ($) | Budget Share |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Substrate** | 1 | $3.00 | 1,000,000 | $3,000,000 | 4,000,000 | $12,000,000 | 18.9% |
| **Capacitor A** | 10 | $0.10 | 10,000,000 | $1,000,000 | 40,000,000 | $4,000,000 | 6.3% |
| **Capacitor B** | 4 | $0.10 | 4,000,000 | $400,000 | 16,000,000 | $1,600,000 | 2.5% |
| **Solder ball** | 30 | $0.05 | 30,000,000 | $1,500,000 | 120,000,000 | $6,000,000 | 9.4% |
| **Die** | 1 | $10.00 | 1,000,000 | $10,000,000 | 4,000,000 | $40,000,000 | 62.9% |
| **TOTAL** | — | — | — | **$15,900,000** | — | **$63,600,000** | **100.0%** |

### 3. Purchasing Plan & Purchase Order (PO) Timeline (5-Week Lead Time)
With a 5-week (35 days) overseas lead time, orders must be issued prior to the start of each production cycle:

| Order Cycle | PO Release Date (Deadline) | In-Factory Arrival Date | CPU Target | Purchasing Spend |
| :--- | :---: | :---: | :---: | :---: |
| **Q1 2027** | **2026-11-27** (Friday) | **2027-01-01** (Friday) | 1,000,000 | $15,900,000 |
| **Q2 2027** | **2027-02-25** (Thursday) | **2027-04-01** (Thursday) | 1,000,000 | $15,900,000 |
| **Q3 2027** | **2027-05-27** (Thursday) | **2027-07-01** (Thursday) | 1,000,000 | $15,900,000 |
| **Q4 2027** | **2027-08-27** (Friday) | **2027-10-01** (Friday) | 1,000,000 | $15,900,000 |

> **Critical Deadline**: For line startup on **January 1st, 2027**, the initial purchase order must be placed no later than **November 27th, 2026**.

---

## 💻 Applications Included

### 1. Interactive Web Application (HTML / CSS / JS)
* **Files**: `index.html`, `style.css`, `app.js`
* **Features**:
  * Real-time scenario preset pills (`Base Case`, `High Demand +25%`, `Supply Delay 8 wks`, `Price Surge +15%`, `Scrap & Safety Buffer`, `Monthly JIT`).
  * Live parameter sliders (Capacity, Lead Time, Scrap Rate, Safety Buffer, Price Variance, Cadence).
  * Interactive BOM Editor (add, edit, delete items).
  * Visual Gantt Transit Timeline & Chart.js visualizations (Donut Cost Share, Spend by Period, Scenario Matrix).
  * 1-Click CSV / Excel Export & Print-ready executive PDF report.
* **How to Run**:
  Simply open `index.html` in any web browser, or serve locally:
  ```bash
  python -m http.server 3000
  # Open http://localhost:3000
  ```

### 2. Python CLI & Excel Generator
* **File**: `solve_procurement_plan.py`
* Calculates BOM, budget, quarterly & monthly purchasing timelines, and exports to `procurement_budget_plan_2027.xlsx`.
* **Run**:
  ```bash
  python solve_procurement_plan.py
  ```

### 3. Native Desktop GUI (Tkinter)
* **File**: `gui_desktop.py`
* Standalone desktop application with scenario presets, editable BOM, and Excel export.
* **Run**:
  ```bash
  python gui_desktop.py
  ```

### 4. Streamlit Dashboard
* **File**: `app.py`
* Interactive Python web app with Plotly graphs and sensitivity analysis.
* **Run**:
  ```bash
  streamlit run app.py
  ```
