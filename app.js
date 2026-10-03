/**
 * ABC Company — Direct Material Procurement & Budget Simulation Engine
 * Vanilla JavaScript (ES6+)
 */

// ==============================================================================
// 1. DEFAULT STATE & DATA
// ==============================================================================
const DEFAULT_BOM = [
  { id: 1, name: "Substrate", qty: 1.0, price: 3.00 },
  { id: 2, name: "Capacitor A", qty: 10.0, price: 0.10 },
  { id: 3, name: "Capacitor B", qty: 4.0, price: 0.10 },
  { id: 4, name: "Solder ball", qty: 30.0, price: 0.05 },
  { id: 5, name: "Die", qty: 1.0, price: 10.00 }
];

const SCENARIO_PRESETS = {
  base: {
    name: "Base Case (Case Study)",
    capacity: 1000000,
    leadTime: 5,
    scrap: 0.0,
    safety: 0.0,
    priceVar: 0,
    cadence: "Quarterly",
    desc: "Base case study: 1,000,000 CPUs/quarter at 100% capacity, 5 weeks overseas lead time, standard BOM pricing."
  },
  high_demand: {
    name: "High Demand (+25%)",
    capacity: 1250000,
    leadTime: 5,
    scrap: 0.0,
    safety: 0.0,
    priceVar: 0,
    cadence: "Quarterly",
    desc: "Production scale-up to 1,250,000 CPUs/quarter (+25% capacity) to satisfy rising market demand."
  },
  shipping_delay: {
    name: "Supply Chain Delay (8 wks)",
    capacity: 1000000,
    leadTime: 8,
    scrap: 0.0,
    safety: 5.0,
    priceVar: 0,
    cadence: "Quarterly",
    desc: "Port congestion increases overseas lead time to 8 weeks; procurement adds 5% safety stock buffer."
  },
  price_surge: {
    name: "Component Price Surge (+15%)",
    capacity: 1000000,
    leadTime: 5,
    scrap: 0.0,
    safety: 0.0,
    priceVar: 15,
    cadence: "Quarterly",
    desc: "Global raw material shortage causes +15% price spike across all electronic components."
  },
  scrap_buffer: {
    name: "Scrap (3%) & Buffer (5%)",
    capacity: 1000000,
    leadTime: 5,
    scrap: 3.0,
    safety: 5.0,
    priceVar: 0,
    cadence: "Quarterly",
    desc: "Assembly line runs at 97% first-pass yield (3% defect rate) requiring 3% scrap allowance + 5% buffer."
  },
  jit_monthly: {
    name: "Monthly Replenishment (12 Cycles)",
    capacity: 1000000,
    leadTime: 5,
    scrap: 0.0,
    safety: 0.0,
    priceVar: 0,
    cadence: "Monthly",
    desc: "Lean JIT monthly ordering (~333,333 CPUs/month) to smooth out warehouse holding costs and cash outlay."
  }
};

let currentBOM = JSON.parse(JSON.stringify(DEFAULT_BOM));
let chartDonut = null;
let chartBar = null;
let chartMatrix = null;

// ==============================================================================
// 2. HELPER FORMATTING FUNCTIONS
// ==============================================================================
const formatCurrency = (val) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(val);
};

const formatNumber = (val) => {
  return new Intl.NumberFormat('en-US').format(Math.round(val));
};

const formatDate = (dateObj) => {
  const options = { year: 'numeric', month: 'short', day: '2-digit', weekday: 'short' };
  return dateObj.toLocaleDateString('en-US', options);
};

const formatDateISO = (dateObj) => {
  return dateObj.toISOString().split('T')[0];
};

// Add days to date
const subtractDays = (date, days) => {
  const res = new Date(date);
  res.setDate(res.getDate() - days);
  return res;
};

// ==============================================================================
// 3. CORE CALCULATION LOGIC
// ==============================================================================
function getFormValues() {
  return {
    capacity: parseFloat(document.getElementById('input-capacity').value) || 1000000,
    startDateStr: document.getElementById('input-start-date').value || '2027-01-01',
    cadence: document.querySelector('input[name="cadence"]:checked').value,
    leadTimeWeeks: parseInt(document.getElementById('slider-lead-time').value, 10) || 5,
    scrapPct: parseFloat(document.getElementById('slider-scrap').value) || 0,
    safetyPct: parseFloat(document.getElementById('slider-safety').value) || 0,
    priceVarPct: parseFloat(document.getElementById('slider-price-variance').value) || 0
  };
}

function calculatePlan() {
  const values = getFormValues();
  const bufferMultiplier = (1 + values.scrapPct / 100.0) * (1 + values.safetyPct / 100.0);
  const priceMultiplier = 1 + values.priceVarPct / 100.0;

  const annualCapacity = values.capacity * 4;
  let baseUnitCost = 0;
  let grossUnitCost = 0;

  // Process BOM items
  const processedBOM = currentBOM.map(item => {
    const adjPrice = item.price * priceMultiplier;
    const grossQty = item.qty * bufferMultiplier;
    const baseCost = item.qty * adjPrice;
    const grossCost = grossQty * adjPrice;

    baseUnitCost += baseCost;
    grossUnitCost += grossCost;

    const qtrQty = grossQty * values.capacity;
    const qtrCost = qtrQty * adjPrice;
    const annQty = grossQty * annualCapacity;
    const annCost = annQty * adjPrice;

    return {
      ...item,
      adjPrice,
      grossQty,
      baseCost,
      grossCost,
      qtrQty,
      qtrCost,
      annQty,
      annCost
    };
  });

  const totalAnnualBudget = grossUnitCost * annualCapacity;
  const totalQuarterlyBudget = grossUnitCost * values.capacity;

  // Compute Cost Share %
  processedBOM.forEach(item => {
    item.share = totalAnnualBudget > 0 ? (item.annCost / totalAnnualBudget) * 100 : 0;
  });

  // Calculate Order Schedule
  const leadTimeDays = values.leadTimeWeeks * 7;
  const [startYear, startMonth, startDay] = values.startDateStr.split('-').map(Number);
  const baseYear = startYear || 2027;

  let schedule = [];
  if (values.cadence === "Quarterly") {
    const quarters = [
      { name: "Q1 " + baseYear, arr: new Date(baseYear, 0, 1) },
      { name: "Q2 " + baseYear, arr: new Date(baseYear, 3, 1) },
      { name: "Q3 " + baseYear, arr: new Date(baseYear, 6, 1) },
      { name: "Q4 " + baseYear, arr: new Date(baseYear, 9, 1) },
    ];

    schedule = quarters.map(q => {
      const poDate = subtractDays(q.arr, leadTimeDays);
      const spend = values.capacity * grossUnitCost;
      return {
        period: q.name,
        targetCPUs: values.capacity,
        arrivalDate: q.arr,
        poReleaseDate: poDate,
        leadTimeStr: `${values.leadTimeWeeks} weeks (${leadTimeDays}d)`,
        spend: spend
      };
    });
  } else {
    // Monthly
    const monthlyCPUs = annualCapacity / 12;
    for (let m = 0; m < 12; m++) {
      const arr = new Date(baseYear, m, 1);
      const poDate = subtractDays(arr, leadTimeDays);
      const monthName = arr.toLocaleString('en-US', { month: 'short' });
      schedule.push({
        period: `${monthName} ${baseYear}`,
        targetCPUs: monthlyCPUs,
        arrivalDate: arr,
        poReleaseDate: poDate,
        leadTimeStr: `${values.leadTimeWeeks} weeks (${leadTimeDays}d)`,
        spend: monthlyCPUs * grossUnitCost
      });
    }
  }

  return {
    values,
    processedBOM,
    baseUnitCost,
    grossUnitCost,
    annualCapacity,
    totalAnnualBudget,
    totalQuarterlyBudget,
    schedule
  };
}

// ==============================================================================
// 4. UI RENDERING & DOM UPDATES
// ==============================================================================
function updateUI() {
  const plan = calculatePlan();

  // 1. KPI Cards
  document.getElementById('kpi-unit-cost').textContent = formatCurrency(plan.grossUnitCost);
  document.getElementById('kpi-unit-base').textContent = `Base: ${formatCurrency(plan.baseUnitCost)} / CPU`;

  document.getElementById('kpi-annual-budget').textContent = formatCurrency(plan.totalAnnualBudget);
  document.getElementById('kpi-annual-volume').textContent = `For ${formatNumber(plan.annualCapacity)} CPUs in 2027`;

  const initialPO = plan.schedule[0].poReleaseDate;
  document.getElementById('kpi-initial-po').textContent = initialPO.toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' });
  document.getElementById('kpi-initial-lead').textContent = `${plan.values.leadTimeWeeks} weeks before production start`;

  const cadenceTitle = plan.values.cadence === "Quarterly" ? "Quarterly Batch Spend" : "Monthly Batch Spend";
  document.getElementById('kpi-batch-title').textContent = cadenceTitle;
  document.getElementById('kpi-batch-cost').textContent = formatCurrency(plan.schedule[0].spend);
  document.getElementById('kpi-batch-sub').textContent = `Per ${plan.values.cadence.toLowerCase()} delivery (${plan.schedule.length} cycles/yr)`;

  // Badge updates
  document.getElementById('budget-badge-summary').textContent = `${formatNumber(plan.annualCapacity)} CPUs • ${plan.schedule.length} Delivery Cycles`;
  document.getElementById('badge-lead-info').textContent = `${plan.values.leadTimeWeeks} Weeks Transit Window`;

  // 2. Budget Breakdown Table
  const tbodyBudget = document.getElementById('tbody-budget');
  tbodyBudget.innerHTML = '';

  plan.processedBOM.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.name}</strong></td>
      <td class="text-right">${item.qty}</td>
      <td class="text-right">${formatCurrency(item.adjPrice)}</td>
      <td class="text-right">${item.grossQty.toFixed(2)}</td>
      <td class="text-right">${formatNumber(item.qtrQty)}</td>
      <td class="text-right">${formatCurrency(item.qtrCost)}</td>
      <td class="text-right">${formatNumber(item.annQty)}</td>
      <td class="text-right">${formatCurrency(item.annCost)}</td>
      <td class="text-right">${item.share.toFixed(1)}%</td>
    `;
    tbodyBudget.appendChild(tr);
  });

  // Footer Totals
  const tfootBudget = document.getElementById('tfoot-budget');
  tfootBudget.innerHTML = `
    <tr>
      <td>TOTAL</td>
      <td class="text-right">—</td>
      <td class="text-right">—</td>
      <td class="text-right">—</td>
      <td class="text-right">—</td>
      <td class="text-right">${formatCurrency(plan.totalQuarterlyBudget)}</td>
      <td class="text-right">—</td>
      <td class="text-right">${formatCurrency(plan.totalAnnualBudget)}</td>
      <td class="text-right">100.0%</td>
    </tr>
  `;

  // 3. Purchasing Schedule Table
  const tbodySched = document.getElementById('tbody-schedule');
  tbodySched.innerHTML = '';

  plan.schedule.forEach((row, idx) => {
    let urgencyClass = "status-planned";
    let urgencyText = "Scheduled";
    if (idx === 0) {
      urgencyClass = "status-urgent";
      urgencyText = "PO Required";
    } else if (idx === 1) {
      urgencyClass = "status-upcoming";
      urgencyText = "Next Cycle";
    }

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${row.period}</strong></td>
      <td>${formatNumber(row.targetCPUs)} CPUs</td>
      <td><span class="value-badge highlight">${formatDate(row.poReleaseDate)}</span></td>
      <td>${formatDate(row.arrivalDate)}</td>
      <td class="text-center">${row.leadTimeStr}</td>
      <td class="text-right"><strong>${formatCurrency(row.spend)}</strong></td>
      <td class="text-center"><span class="status-pill ${urgencyClass}">${urgencyText}</span></td>
    `;
    tbodySched.appendChild(tr);
  });

  // 4. Visual Gantt Timeline
  renderVisualTimeline(plan.schedule, plan.values.leadTimeWeeks);

  // 5. BOM Editor Table
  renderBOMEditorTable();

  // 6. Charts
  renderCharts(plan);

  // 7. Sensitivity Comparison Matrix
  renderSensitivityMatrix();
}

// ==============================================================================
// 5. TIMELINE VISUAL (GANTT BARS)
// ==============================================================================
function renderVisualTimeline(schedule, leadWeeks) {
  const container = document.getElementById('timeline-container');
  container.innerHTML = '';

  schedule.forEach(item => {
    const row = document.createElement('div');
    row.className = 'timeline-row';

    const poStr = formatDateISO(item.poReleaseDate);
    const arrStr = formatDateISO(item.arrivalDate);

    row.innerHTML = `
      <div class="timeline-period-lbl">${item.period}</div>
      <div class="timeline-track">
        <div class="timeline-transit-bar" style="width: 100%;">
          <span>🚢 PO: ${poStr} ➔ Factory Delivery: ${arrStr} (${leadWeeks} wks transit)</span>
        </div>
      </div>
      <div class="timeline-spend-lbl">${formatCurrency(item.spend)}</div>
    `;
    container.appendChild(row);
  });
}

// ==============================================================================
// 6. BOM EDITOR TABLE
// ==============================================================================
function renderBOMEditorTable() {
  const tbody = document.getElementById('tbody-bom-editor');
  tbody.innerHTML = '';

  currentBOM.forEach((item, index) => {
    const cost = item.qty * item.price;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.name}</strong></td>
      <td class="text-right">
        <input type="number" class="table-input" value="${item.qty}" min="0.01" step="0.1" data-index="${index}" data-field="qty" />
      </td>
      <td class="text-right">
        <input type="number" class="table-input" value="${item.price.toFixed(4)}" min="0.0001" step="0.01" data-index="${index}" data-field="price" />
      </td>
      <td class="text-right">${formatCurrency(cost)}</td>
      <td class="text-center">
        <button class="btn btn-sm btn-danger btn-delete-item" data-index="${index}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Add event listeners to table inputs
  tbody.querySelectorAll('.table-input').forEach(input => {
    input.addEventListener('change', (e) => {
      const idx = parseInt(e.target.dataset.index, 10);
      const field = e.target.dataset.field;
      const val = parseFloat(e.target.value);
      if (!isNaN(val) && val > 0) {
        currentBOM[idx][field] = val;
        updateUI();
      }
    });
  });

  tbody.querySelectorAll('.btn-delete-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.dataset.index, 10);
      if (currentBOM.length <= 1) {
        alert("BOM must contain at least one item.");
        return;
      }
      currentBOM.splice(idx, 1);
      updateUI();
    });
  });
}

// ==============================================================================
// 7. CHARTS RENDERING (CHART.JS)
// ==============================================================================
function renderCharts(plan) {
  // Chart 1: Donut (BOM Cost Share)
  const ctxDonut = document.getElementById('chart-bom-pie').getContext('2d');
  const labels = plan.processedBOM.map(i => i.name);
  const dataValues = plan.processedBOM.map(i => i.annCost);
  const colors = ['#0284c7', '#38bdf8', '#818cf8', '#34d399', '#f59e0b', '#f43f5e', '#a855f7'];

  if (chartDonut) chartDonut.destroy();
  chartDonut = new Chart(ctxDonut, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: dataValues,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: '#141d2e',
        borderWidth: 2,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              const pct = (val / plan.totalAnnualBudget * 100).toFixed(1);
              return ` ${context.label}: ${formatCurrency(val)} (${pct}%)`;
            }
          }
        }
      },
      cutout: '65%'
    }
  });

  // Chart 2: Spend By Order Cycle (Bar)
  const ctxBar = document.getElementById('chart-spend-bar').getContext('2d');
  const schedLabels = plan.schedule.map(s => s.period);
  const spendValues = plan.schedule.map(s => s.spend);

  if (chartBar) chartBar.destroy();
  chartBar = new Chart(ctxBar, {
    type: 'bar',
    data: {
      labels: schedLabels,
      datasets: [{
        label: 'Purchasing Spend ($ USD)',
        data: spendValues,
        backgroundColor: '#0284c7',
        hoverBackgroundColor: '#38bdf8',
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Spend: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 10 } },
          grid: { display: false }
        },
        y: {
          ticks: {
            color: '#94a3b8',
            font: { family: 'JetBrains Mono', size: 10 },
            callback: (v) => '$' + (v / 1000000).toFixed(1) + 'M'
          },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

// ==============================================================================
// 8. SENSITIVITY MATRIX (TAB 4)
// ==============================================================================
function renderSensitivityMatrix() {
  const tbody = document.getElementById('tbody-matrix');
  tbody.innerHTML = '';

  const matrixData = [];
  const baseBudgetStandard = 4000000 * 15.90;

  Object.entries(SCENARIO_PRESETS).forEach(([key, sc]) => {
    const annCap = sc.capacity * 4;
    const buf = (1 + sc.scrap / 100.0) * (1 + sc.safety / 100.0);
    const pMult = 1 + sc.priceVar / 100.0;

    // Calculate unit cost for standard BOM
    const unitCost = DEFAULT_BOM.reduce((sum, item) => sum + (item.qty * buf * item.price * pMult), 0);
    const annBudget = annCap * unitCost;
    const variance = annBudget - baseBudgetStandard;

    const poDate = subtractDays(new Date(2027, 0, 1), sc.leadTime * 7);

    matrixData.push({
      key,
      name: sc.name,
      qtrQty: sc.capacity,
      annQty: annCap,
      leadTime: sc.leadTime,
      bufferStr: `${((buf - 1) * 100).toFixed(1)}%`,
      priceVarStr: `${sc.priceVar >= 0 ? '+' : ''}${sc.priceVar}%`,
      unitCost,
      annBudget,
      variance,
      poDateStr: formatDateISO(poDate)
    });

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${sc.name}</strong></td>
      <td class="text-right">${formatNumber(sc.capacity)}</td>
      <td class="text-right">${formatNumber(annCap)}</td>
      <td class="text-center">${sc.leadTime} wks</td>
      <td class="text-center">${((buf - 1) * 100).toFixed(1)}%</td>
      <td class="text-center">${sc.priceVar >= 0 ? '+' : ''}${sc.priceVar}%</td>
      <td class="text-right">${formatCurrency(unitCost)}</td>
      <td class="text-right"><strong>${formatCurrency(annBudget)}</strong></td>
      <td class="text-right" style="color: ${variance >= 0 ? (variance === 0 ? '#94a3b8' : '#f43f5e') : '#34d399'}">
        ${variance >= 0 ? (variance === 0 ? '$0.00' : '+' + formatCurrency(variance)) : '-' + formatCurrency(Math.abs(variance))}
      </td>
      <td><span class="value-badge">${formatDate(poDate)}</span></td>
    `;
    tbody.appendChild(tr);
  });

  // Render Matrix Comparison Chart
  const ctxMatrix = document.getElementById('chart-matrix-bar').getContext('2d');
  const scLabels = matrixData.map(m => m.name);
  const scBudgets = matrixData.map(m => m.annBudget);

  if (chartMatrix) chartMatrix.destroy();
  chartMatrix = new Chart(ctxMatrix, {
    type: 'bar',
    data: {
      labels: scLabels,
      datasets: [{
        label: 'Annual Spend ($ USD)',
        data: scBudgets,
        backgroundColor: ['#0284c7', '#38bdf8', '#818cf8', '#f59e0b', '#f43f5e', '#10b981'],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Budget: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 10 } },
          grid: { display: false }
        },
        y: {
          ticks: {
            color: '#94a3b8',
            font: { family: 'JetBrains Mono', size: 10 },
            callback: (v) => '$' + (v / 1000000).toFixed(0) + 'M'
          },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

// ==============================================================================
// 9. EVENT LISTENERS & PRESETS
// ==============================================================================
function setupEventListeners() {
  // Synchronize range sliders with badges and inputs
  const sliderCapacity = document.getElementById('slider-capacity');
  const inputCapacity = document.getElementById('input-capacity');
  const lblCapacity = document.getElementById('lbl-capacity');

  sliderCapacity.addEventListener('input', (e) => {
    inputCapacity.value = e.target.value;
    lblCapacity.textContent = formatNumber(e.target.value);
    updateUI();
  });

  inputCapacity.addEventListener('change', (e) => {
    sliderCapacity.value = e.target.value;
    lblCapacity.textContent = formatNumber(e.target.value);
    updateUI();
  });

  // Lead Time
  const sliderLead = document.getElementById('slider-lead-time');
  const lblLead = document.getElementById('lbl-lead-time');
  sliderLead.addEventListener('input', (e) => {
    lblLead.textContent = `${e.target.value} Weeks`;
    updateUI();
  });

  // Scrap
  const sliderScrap = document.getElementById('slider-scrap');
  const lblScrap = document.getElementById('lbl-scrap');
  sliderScrap.addEventListener('input', (e) => {
    lblScrap.textContent = `${parseFloat(e.target.value).toFixed(1)}%`;
    updateUI();
  });

  // Safety
  const sliderSafety = document.getElementById('slider-safety');
  const lblSafety = document.getElementById('lbl-safety');
  sliderSafety.addEventListener('input', (e) => {
    lblSafety.textContent = `${parseFloat(e.target.value).toFixed(1)}%`;
    updateUI();
  });

  // Price Variance
  const sliderPrice = document.getElementById('slider-price-variance');
  const lblPrice = document.getElementById('lbl-price-variance');
  sliderPrice.addEventListener('input', (e) => {
    lblPrice.textContent = `${e.target.value >= 0 ? '+' : ''}${e.target.value}%`;
    updateUI();
  });

  // Start Date
  document.getElementById('input-start-date').addEventListener('change', () => updateUI());

  // Cadence Radios
  document.querySelectorAll('input[name="cadence"]').forEach(radio => {
    radio.addEventListener('change', () => updateUI());
  });

  // Tab switching
  document.querySelectorAll('.tab-link').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.tab-link').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      
      const targetTab = btn.dataset.tab;
      btn.classList.add('active');
      document.getElementById(targetTab).classList.add('active');
      
      // Resize charts if tab becomes visible
      if (chartDonut) chartDonut.resize();
      if (chartBar) chartBar.resize();
      if (chartMatrix) chartMatrix.resize();
    });
  });

  // Preset Scenario Pills
  document.querySelectorAll('.pill-btn').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.pill-btn').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      
      const presetKey = pill.dataset.preset;
      applyPreset(presetKey);
    });
  });

  // Reset Parameters Button
  document.getElementById('btn-reset-params').addEventListener('click', () => {
    applyPreset('base');
  });

  // Reset BOM Buttons
  document.getElementById('btn-reset-bom-tab').addEventListener('click', () => {
    currentBOM = JSON.parse(JSON.stringify(DEFAULT_BOM));
    updateUI();
  });

  // Add Item to BOM Form
  document.getElementById('btn-add-bom-item').addEventListener('click', () => {
    const nameInput = document.getElementById('add-item-name');
    const qtyInput = document.getElementById('add-item-qty');
    const priceInput = document.getElementById('add-item-price');

    const name = nameInput.value.trim();
    const qty = parseFloat(qtyInput.value);
    const price = parseFloat(priceInput.value);

    if (!name) {
      alert("Please enter a valid component name.");
      return;
    }
    if (isNaN(qty) || qty <= 0) {
      alert("Please enter a positive quantity per CPU.");
      return;
    }
    if (isNaN(price) || price <= 0) {
      alert("Please enter a positive unit price.");
      return;
    }

    currentBOM.push({
      id: Date.now(),
      name,
      qty,
      price
    });

    nameInput.value = '';
    qtyInput.value = '1';
    priceInput.value = '0.50';

    updateUI();
  });

  // Export CSV Button
  document.getElementById('btn-export-csv').addEventListener('click', exportCSV);

  // Print Report Button
  document.getElementById('btn-print').addEventListener('click', () => {
    window.print();
  });

  // Mobile Sidebar Parameters Toggle
  const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
  const sidebarPanel = document.querySelector('.sidebar-panel');
  if (btnToggleSidebar && sidebarPanel) {
    btnToggleSidebar.addEventListener('click', () => {
      sidebarPanel.classList.toggle('show-mobile');
      btnToggleSidebar.classList.toggle('active');
    });
  }

  // Automatic window scaling & chart resize listener
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (chartDonut) chartDonut.resize();
      if (chartBar) chartBar.resize();
      if (chartMatrix) chartMatrix.resize();
    }, 120);
  });
}

function applyPreset(key) {
  const sc = SCENARIO_PRESETS[key];
  if (!sc) return;

  // Set values
  document.getElementById('slider-capacity').value = sc.capacity;
  document.getElementById('input-capacity').value = sc.capacity;
  document.getElementById('lbl-capacity').textContent = formatNumber(sc.capacity);

  document.getElementById('slider-lead-time').value = sc.leadTime;
  document.getElementById('lbl-lead-time').textContent = `${sc.leadTime} Weeks`;

  document.getElementById('slider-scrap').value = sc.scrap;
  document.getElementById('lbl-scrap').textContent = `${sc.scrap.toFixed(1)}%`;

  document.getElementById('slider-safety').value = sc.safety;
  document.getElementById('lbl-safety').textContent = `${sc.safety.toFixed(1)}%`;

  document.getElementById('slider-price-variance').value = sc.priceVar;
  document.getElementById('lbl-price-variance').textContent = `${sc.priceVar >= 0 ? '+' : ''}${sc.priceVar}%`;

  const radio = document.querySelector(`input[name="cadence"][value="${sc.cadence}"]`);
  if (radio) radio.checked = true;

  document.getElementById('scenario-desc-text').textContent = sc.desc;

  updateUI();
}

// ==============================================================================
// 10. CSV EXPORT FUNCTIONALITY
// ==============================================================================
function exportCSV() {
  const plan = calculatePlan();
  let csv = "\uFEFF"; // UTF-8 BOM for Microsoft Excel

  // Header
  csv += "ABC COMPANY - SAIGON HI-TECH PARK\r\n";
  csv += "DIRECT MATERIAL PROCUREMENT BUDGET & PURCHASING SCHEDULE (2027)\r\n\r\n";

  // Summary Parameters
  csv += `Capacity per Quarter,${plan.values.capacity},CPUs\r\n`;
  csv += `Annual Capacity,${plan.annualCapacity},CPUs\r\n`;
  csv += `Lead Time,${plan.values.leadTimeWeeks},weeks\r\n`;
  csv += `Scrap Rate,${plan.values.scrapPct}%\r\n`;
  csv += `Safety Stock,${plan.values.safetyPct}%\r\n`;
  csv += `Unit Material Cost,$${plan.grossUnitCost.toFixed(2)},USD\r\n`;
  csv += `Total Annual Budget,$${plan.totalAnnualBudget.toFixed(2)},USD\r\n\r\n`;

  // BOM Table
  csv += "--- BILL OF MATERIALS & MATERIAL BUDGET ---\r\n";
  csv += "Item,Net Qty/CPU,Price (USD),Gross Qty/CPU,Quarterly Qty,Quarterly Budget (USD),Annual Qty,Annual Budget (USD),Cost Share (%)\r\n";
  plan.processedBOM.forEach(b => {
    csv += `"${b.name}",${b.qty},${b.adjPrice.toFixed(4)},${b.grossQty.toFixed(2)},${b.qtrQty},${b.qtrCost.toFixed(2)},${b.annQty},${b.annCost.toFixed(2)},${b.share.toFixed(1)}%\r\n`;
  });
  csv += `TOTAL,,,,,$${plan.totalQuarterlyBudget.toFixed(2)},,$${plan.totalAnnualBudget.toFixed(2)},100.0%\r\n\r\n`;

  // Schedule Table
  csv += "--- PURCHASING SCHEDULE (MRP) ---\r\n";
  csv += "Period,Target CPUs,PO Release Date,Factory Delivery Date,Lead Time,Purchasing Spend (USD)\r\n";
  plan.schedule.forEach(s => {
    csv += `"${s.period}",${s.targetCPUs},"${formatDateISO(s.poReleaseDate)}","${formatDateISO(s.arrivalDate)}","${s.leadTimeStr}",${s.spend.toFixed(2)}\r\n`;
  });

  // Create download link
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Procurement_Plan_2027_${plan.values.cadence}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ==============================================================================
// INITIALIZATION
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  updateUI();
});
