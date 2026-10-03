"""
Desktop GUI for Procurement & Direct Material Budget Planner
ABC Company - Saigon Hi-Tech Park
Uses Python's standard library (tkinter + ttk) with pandas/openpyxl
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd

class ProcurementGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Procurement & Direct Material Budget Planner — ABC Company (SHTP)")
        self.geometry("1100x750")
        self.minsize(950, 650)

        # Style configuration
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(".", font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e2e8f0")
        self.style.configure("Treeview", rowheight=24)
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 9, "bold"), padding=[10, 4])
        self.style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), foreground="#ffffff", background="#0284c7")

        # Initial BOM Data
        self.bom_data = [
            {"item": "Substrate", "qty": 1.0, "price": 3.00},
            {"item": "Capacitor A", "qty": 10.0, "price": 0.10},
            {"item": "Capacitor B", "qty": 4.0, "price": 0.10},
            {"item": "Solder ball", "qty": 30.0, "price": 0.05},
            {"item": "Die", "qty": 1.0, "price": 10.00},
        ]

        self.create_widgets()
        self.calculate_and_refresh()

    def create_widgets(self):
        # Top Header
        header_frame = tk.Frame(self, bg="#0f172a", height=50)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        title_lbl = tk.Label(
            header_frame,
            text="🏭 ABC COMPANY (SHTP) — 2027 CPU PRODUCTION PROCUREMENT PLANNER",
            font=("Segoe UI", 12, "bold"),
            fg="#f8fafc",
            bg="#0f172a",
            padx=15,
            pady=10
        )
        title_lbl.pack(side=tk.LEFT)

        # Main Layout: Left Panel (Inputs & Controls), Right Panel (Notebook with Results)
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # --- LEFT PANEL: CONTROLS ---
        left_frame = ttk.LabelFrame(main_paned, text=" Scenario Parameters ", padding=10)
        main_paned.add(left_frame, weight=1)

        # Scenario Presets
        ttk.Label(left_frame, text="Preset Scenario:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 2))
        self.preset_var = tk.StringVar(value="Base Case (Case Study)")
        self.preset_combo = ttk.Combobox(
            left_frame,
            textvariable=self.preset_var,
            state="readonly",
            values=[
                "Base Case (Case Study)",
                "High Demand (+25%)",
                "Shipping Delay (Lead Time 8 wks)",
                "Component Price Surge (+15%)",
                "Scrap (3%) & Safety Stock (5%)",
                "Monthly Replenishment (JIT)"
            ]
        )
        self.preset_combo.pack(fill=tk.X, pady=(0, 10))
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_change)

        # Capacity per quarter
        ttk.Label(left_frame, text="Capacity / Quarter (CPUs):").pack(anchor=tk.W)
        self.cap_var = tk.StringVar(value="1000000")
        self.cap_entry = ttk.Entry(left_frame, textvariable=self.cap_var)
        self.cap_entry.pack(fill=tk.X, pady=(0, 8))

        # Overseas Lead Time (Weeks)
        ttk.Label(left_frame, text="Overseas Lead Time (Weeks):").pack(anchor=tk.W)
        self.lead_time_var = tk.StringVar(value="5")
        self.lead_spin = ttk.Spinbox(left_frame, from_=1, to=26, textvariable=self.lead_time_var)
        self.lead_spin.pack(fill=tk.X, pady=(0, 8))

        # Scrap / Defect Rate %
        ttk.Label(left_frame, text="Scrap / Defect Rate (%):").pack(anchor=tk.W)
        self.scrap_var = tk.StringVar(value="0.0")
        self.scrap_entry = ttk.Entry(left_frame, textvariable=self.scrap_var)
        self.scrap_entry.pack(fill=tk.X, pady=(0, 8))

        # Safety Stock Buffer %
        ttk.Label(left_frame, text="Safety Stock Buffer (%):").pack(anchor=tk.W)
        self.safety_var = tk.StringVar(value="0.0")
        self.safety_entry = ttk.Entry(left_frame, textvariable=self.safety_var)
        self.safety_entry.pack(fill=tk.X, pady=(0, 8))

        # Price Adjustment Factor %
        ttk.Label(left_frame, text="Material Price Variance (%):").pack(anchor=tk.W)
        self.price_factor_var = tk.StringVar(value="0.0")
        self.price_factor_entry = ttk.Entry(left_frame, textvariable=self.price_factor_var)
        self.price_factor_entry.pack(fill=tk.X, pady=(0, 8))

        # Purchasing Cadence
        ttk.Label(left_frame, text="Order Frequency:").pack(anchor=tk.W)
        self.cadence_var = tk.StringVar(value="Quarterly")
        self.cadence_combo = ttk.Combobox(
            left_frame,
            textvariable=self.cadence_var,
            state="readonly",
            values=["Quarterly", "Monthly"]
        )
        self.cadence_combo.pack(fill=tk.X, pady=(0, 12))

        # Action Buttons
        btn_calc = ttk.Button(left_frame, text="⚡ Recalculate Plan", command=self.calculate_and_refresh)
        btn_calc.pack(fill=tk.X, pady=4)

        btn_reset_bom = ttk.Button(left_frame, text="↺ Reset BOM to Default", command=self.reset_bom)
        btn_reset_bom.pack(fill=tk.X, pady=4)

        btn_export = ttk.Button(left_frame, text="💾 Export to Excel (.xlsx)", command=self.export_excel)
        btn_export.pack(fill=tk.X, pady=4)

        # --- RIGHT PANEL: TABS & RESULTS ---
        right_frame = tk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)

        # KPI Summary Cards Bar
        kpi_bar = tk.Frame(right_frame, bg="#f1f5f9", relief=tk.RIDGE, bd=1)
        kpi_bar.pack(fill=tk.X, padx=4, pady=(0, 8))

        self.kpi_unit_cost = tk.Label(kpi_bar, text="Unit Cost: $15.90", font=("Segoe UI", 11, "bold"), fg="#0369a1", bg="#f1f5f9", padx=10, pady=8)
        self.kpi_unit_cost.pack(side=tk.LEFT)

        self.kpi_annual_cost = tk.Label(kpi_bar, text="Annual Budget: $63.60M", font=("Segoe UI", 11, "bold"), fg="#047857", bg="#f1f5f9", padx=10, pady=8)
        self.kpi_annual_cost.pack(side=tk.LEFT)

        self.kpi_first_po = tk.Label(kpi_bar, text="Initial PO: 2026-11-27", font=("Segoe UI", 11, "bold"), fg="#b45309", bg="#f1f5f9", padx=10, pady=8)
        self.kpi_first_po.pack(side=tk.LEFT)

        # Notebook Tabs
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Direct Material Budget
        tab_budget = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_budget, text=" 📊 Direct Material Budget ")
        self.build_budget_tab(tab_budget)

        # Tab 2: Purchasing Plan (MRP Schedule)
        tab_schedule = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_schedule, text=" 📅 Purchasing Schedule & PO Deadlines ")
        self.build_schedule_tab(tab_schedule)

        # Tab 3: BOM Editor
        tab_bom = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_bom, text=" 📝 BOM Editor ")
        self.build_bom_editor_tab(tab_bom)

    def build_budget_tab(self, parent):
        cols = ("item", "qty_cpu", "adj_price", "gross_qty", "qtr_qty", "qtr_cost", "annual_qty", "annual_cost", "share")
        self.tree_budget = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        
        self.tree_budget.heading("item", text="Item")
        self.tree_budget.heading("qty_cpu", text="Qty/CPU")
        self.tree_budget.heading("adj_price", text="Price ($)")
        self.tree_budget.heading("gross_qty", text="Gross Qty/CPU")
        self.tree_budget.heading("qtr_qty", text="Qtr Qty")
        self.tree_budget.heading("qtr_cost", text="Qtr Spend ($)")
        self.tree_budget.heading("annual_qty", text="Annual Qty")
        self.tree_budget.heading("annual_cost", text="Annual Spend ($)")
        self.tree_budget.heading("share", text="Share (%)")

        self.tree_budget.column("item", width=120, anchor=tk.W)
        self.tree_budget.column("qty_cpu", width=70, anchor=tk.E)
        self.tree_budget.column("adj_price", width=80, anchor=tk.E)
        self.tree_budget.column("gross_qty", width=95, anchor=tk.E)
        self.tree_budget.column("qtr_qty", width=95, anchor=tk.E)
        self.tree_budget.column("qtr_cost", width=110, anchor=tk.E)
        self.tree_budget.column("annual_qty", width=105, anchor=tk.E)
        self.tree_budget.column("annual_cost", width=120, anchor=tk.E)
        self.tree_budget.column("share", width=70, anchor=tk.E)

        scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_budget.yview)
        self.tree_budget.configure(yscrollcommand=scroll.set)
        self.tree_budget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def build_schedule_tab(self, parent):
        cols = ("period", "po_date", "arr_date", "cpu_target", "lead_time", "spend")
        self.tree_sched = ttk.Treeview(parent, columns=cols, show="headings", height=12)

        self.tree_sched.heading("period", text="Period / Cycle")
        self.tree_sched.heading("po_date", text="PO Release Date (-Lead Time)")
        self.tree_sched.heading("arr_date", text="Required / Arrival Date")
        self.tree_sched.heading("cpu_target", text="CPU Batch Target")
        self.tree_sched.heading("lead_time", text="Lead Time")
        self.tree_sched.heading("spend", text="Purchasing Spend ($)")

        self.tree_sched.column("period", width=120, anchor=tk.W)
        self.tree_sched.column("po_date", width=180, anchor=tk.W)
        self.tree_sched.column("arr_date", width=180, anchor=tk.W)
        self.tree_sched.column("cpu_target", width=120, anchor=tk.E)
        self.tree_sched.column("lead_time", width=110, anchor=tk.CENTER)
        self.tree_sched.column("spend", width=140, anchor=tk.E)

        scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_sched.yview)
        self.tree_sched.configure(yscrollcommand=scroll.set)
        self.tree_sched.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def build_bom_editor_tab(self, parent):
        top_bar = tk.Frame(parent)
        top_bar.pack(fill=tk.X, pady=(0, 6))

        tk.Label(top_bar, text="Item:").pack(side=tk.LEFT, padx=2)
        self.new_item_var = tk.StringVar()
        ttk.Entry(top_bar, textvariable=self.new_item_var, width=15).pack(side=tk.LEFT, padx=2)

        tk.Label(top_bar, text="Qty/CPU:").pack(side=tk.LEFT, padx=2)
        self.new_qty_var = tk.StringVar(value="1")
        ttk.Entry(top_bar, textvariable=self.new_qty_var, width=8).pack(side=tk.LEFT, padx=2)

        tk.Label(top_bar, text="Price ($):").pack(side=tk.LEFT, padx=2)
        self.new_price_var = tk.StringVar(value="1.00")
        ttk.Entry(top_bar, textvariable=self.new_price_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Button(top_bar, text="➕ Add Component", command=self.add_bom_item).pack(side=tk.LEFT, padx=6)
        ttk.Button(top_bar, text="🗑️ Delete Selected", command=self.delete_bom_item).pack(side=tk.LEFT, padx=2)

        cols = ("item", "qty", "price")
        self.tree_bom = ttk.Treeview(parent, columns=cols, show="headings", height=8)
        self.tree_bom.heading("item", text="Component Name")
        self.tree_bom.heading("qty", text="Quantity per CPU")
        self.tree_bom.heading("price", text="Price (USD)")

        self.tree_bom.column("item", width=180, anchor=tk.W)
        self.tree_bom.column("qty", width=120, anchor=tk.E)
        self.tree_bom.column("price", width=120, anchor=tk.E)

        self.tree_bom.pack(fill=tk.BOTH, expand=True)
        self.refresh_bom_treeview()

    def reset_bom(self):
        self.bom_data = [
            {"item": "Substrate", "qty": 1.0, "price": 3.00},
            {"item": "Capacitor A", "qty": 10.0, "price": 0.10},
            {"item": "Capacitor B", "qty": 4.0, "price": 0.10},
            {"item": "Solder ball", "qty": 30.0, "price": 0.05},
            {"item": "Die", "qty": 1.0, "price": 10.00},
        ]
        self.refresh_bom_treeview()
        self.calculate_and_refresh()

    def refresh_bom_treeview(self):
        for item in self.tree_bom.get_children():
            self.tree_bom.delete(item)
        for row in self.bom_data:
            self.tree_bom.insert("", tk.END, values=(row["item"], f"{row['qty']:,.2f}", f"${row['price']:,.4f}"))

    def add_bom_item(self):
        name = self.new_item_var.get().strip()
        try:
            qty = float(self.new_qty_var.get())
            price = float(self.new_price_var.get())
            if not name:
                messagebox.showerror("Error", "Please specify item name.")
                return
            self.bom_data.append({"item": name, "qty": qty, "price": price})
            self.refresh_bom_treeview()
            self.calculate_and_refresh()
            self.new_item_var.set("")
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric value for Quantity or Price.")

    def delete_bom_item(self):
        selected = self.tree_bom.selection()
        if not selected:
            messagebox.showinfo("Select Item", "Please select an item to delete.")
            return
        idx = self.tree_bom.index(selected[0])
        del self.bom_data[idx]
        self.refresh_bom_treeview()
        self.calculate_and_refresh()

    def on_preset_change(self, event=None):
        preset = self.preset_var.get()
        if preset == "Base Case (Case Study)":
            self.cap_var.set("1000000")
            self.lead_time_var.set("5")
            self.scrap_var.set("0.0")
            self.safety_var.set("0.0")
            self.price_factor_var.set("0.0")
            self.cadence_var.set("Quarterly")
        elif preset == "High Demand (+25%)":
            self.cap_var.set("1250000")
            self.lead_time_var.set("5")
            self.scrap_var.set("0.0")
            self.safety_var.set("0.0")
            self.price_factor_var.set("0.0")
            self.cadence_var.set("Quarterly")
        elif preset == "Shipping Delay (Lead Time 8 wks)":
            self.cap_var.set("1000000")
            self.lead_time_var.set("8")
            self.scrap_var.set("0.0")
            self.safety_var.set("5.0")
            self.price_factor_var.set("0.0")
            self.cadence_var.set("Quarterly")
        elif preset == "Component Price Surge (+15%)":
            self.cap_var.set("1000000")
            self.lead_time_var.set("5")
            self.scrap_var.set("0.0")
            self.safety_var.set("0.0")
            self.price_factor_var.set("15.0")
            self.cadence_var.set("Quarterly")
        elif preset == "Scrap (3%) & Safety Stock (5%)":
            self.cap_var.set("1000000")
            self.lead_time_var.set("5")
            self.scrap_var.set("3.0")
            self.safety_var.set("5.0")
            self.price_factor_var.set("0.0")
            self.cadence_var.set("Quarterly")
        elif preset == "Monthly Replenishment (JIT)":
            self.cap_var.set("1000000")
            self.lead_time_var.set("5")
            self.scrap_var.set("0.0")
            self.safety_var.set("0.0")
            self.price_factor_var.set("0.0")
            self.cadence_var.set("Monthly")
        
        self.calculate_and_refresh()

    def calculate_and_refresh(self):
        try:
            capacity_per_qtr = float(self.cap_var.get())
            lead_weeks = int(self.lead_time_var.get())
            scrap_pct = float(self.scrap_var.get())
            safety_pct = float(self.safety_var.get())
            price_factor = float(self.price_factor_var.get())
            cadence = self.cadence_var.get()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric parameters.")
            return

        buffer_multiplier = (1 + scrap_pct / 100.0) * (1 + safety_pct / 100.0)
        price_multiplier = 1 + price_factor / 100.0
        annual_capacity = capacity_per_qtr * 4

        # Calculate BOM items
        calc_rows = []
        total_unit_cost = 0.0

        for row in self.bom_data:
            adj_price = row["price"] * price_multiplier
            gross_qty_cpu = row["qty"] * buffer_multiplier
            cost_cpu = gross_qty_cpu * adj_price
            total_unit_cost += cost_cpu

            qtr_qty = gross_qty_cpu * capacity_per_qtr
            qtr_cost = qtr_qty * adj_price
            ann_qty = gross_qty_cpu * annual_capacity
            ann_cost = ann_qty * adj_price

            calc_rows.append({
                "item": row["item"],
                "qty_cpu": row["qty"],
                "adj_price": adj_price,
                "gross_qty": gross_qty_cpu,
                "qtr_qty": qtr_qty,
                "qtr_cost": qtr_cost,
                "ann_qty": ann_qty,
                "ann_cost": ann_cost
            })

        annual_total_budget = total_unit_cost * annual_capacity

        # Refresh Budget Treeview
        for item in self.tree_budget.get_children():
            self.tree_budget.delete(item)

        for r in calc_rows:
            share = (r["ann_cost"] / annual_total_budget * 100.0) if annual_total_budget > 0 else 0
            self.tree_budget.insert("", tk.END, values=(
                r["item"],
                f"{r['qty_cpu']:,.2f}",
                f"${r['adj_price']:,.2f}",
                f"{r['gross_qty']:,.2f}",
                f"{r['qtr_qty']:,.0f}",
                f"${r['qtr_cost']:,.2f}",
                f"{r['ann_qty']:,.0f}",
                f"${r['ann_cost']:,.2f}",
                f"{share:.1f}%"
            ))

        # Calculate Schedule
        lead_days = lead_weeks * 7
        lead_td = timedelta(days=lead_days)

        sched_rows = []
        if cadence == "Quarterly":
            periods = ["Q1 2027", "Q2 2027", "Q3 2027", "Q4 2027"]
            arrival_dates = [datetime(2027, 1, 1), datetime(2027, 4, 1), datetime(2027, 7, 1), datetime(2027, 10, 1)]
            batch_qty = capacity_per_qtr
        else:
            periods = [f"Month {m} ({datetime(2027, m, 1).strftime('%b')})" for m in range(1, 13)]
            arrival_dates = [datetime(2027, m, 1) for m in range(1, 13)]
            batch_qty = annual_capacity / 12

        batch_spend = batch_qty * total_unit_cost

        for p_name, arr in zip(periods, arrival_dates):
            po_date = arr - lead_td
            sched_rows.append({
                "period": p_name,
                "po_date": po_date.strftime("%Y-%m-%d (%a)"),
                "arr_date": arr.strftime("%Y-%m-%d (%a)"),
                "cpu_target": round(batch_qty),
                "lead_time": f"{lead_weeks} wks",
                "spend": batch_spend
            })

        # Refresh Schedule Treeview
        for item in self.tree_sched.get_children():
            self.tree_sched.delete(item)

        for s in sched_rows:
            self.tree_sched.insert("", tk.END, values=(
                s["period"],
                s["po_date"],
                s["arr_date"],
                f"{s['cpu_target']:,.0f}",
                s["lead_time"],
                f"${s['spend']:,.2f}"
            ))

        # Update KPIs
        self.kpi_unit_cost.config(text=f"Unit Material Cost: ${total_unit_cost:,.2f} / CPU")
        self.kpi_annual_cost.config(text=f"Annual Budget: ${annual_total_budget:,.2f}")
        first_po_date_str = sched_rows[0]["po_date"].split(" ")[0]
        self.kpi_first_po.config(text=f"Initial PO Release: {first_po_date_str}")

        # Store data for Excel export
        self.last_calc = {
            "calc_rows": calc_rows,
            "sched_rows": sched_rows,
            "annual_total_budget": annual_total_budget,
            "total_unit_cost": total_unit_cost
        }

    def export_excel(self):
        if not hasattr(self, "last_calc"):
            self.calculate_and_refresh()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile="procurement_plan_scenario.xlsx"
        )
        if not file_path:
            return

        df_b = pd.DataFrame(self.last_calc["calc_rows"])
        df_s = pd.DataFrame(self.last_calc["sched_rows"])

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df_b.to_excel(writer, sheet_name="Material Budget", index=False)
            df_s.to_excel(writer, sheet_name="Purchasing Schedule", index=False)

        messagebox.showinfo("Export Successful", f"File saved successfully to:\n{file_path}")

if __name__ == "__main__":
    app = ProcurementGUI()
    app.mainloop()
