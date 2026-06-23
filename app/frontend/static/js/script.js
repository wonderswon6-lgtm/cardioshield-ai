// script.js — CardioShield AI global JS

// ── Utilities ─────────────────────────────────────────────────────────────
function $(id) { return document.getElementById(id); }
function showSpinner()  { document.querySelector('.spinner-overlay')?.classList.add('show'); }
function hideSpinner()  { document.querySelector('.spinner-overlay')?.classList.remove('show'); }
function fmtPct(v)      { return parseFloat(v).toFixed(1) + '%'; }
function fmtDate(iso)   { return iso ? new Date(iso).toLocaleString() : '—'; }

// ── Local Explanations rendering helper ────────────────────────────────────
function setupExplanationSelector(predictions, selectEl, riskListEl, protectiveListEl, sectionEl) {
  if (!selectEl || !riskListEl || !protectiveListEl || !sectionEl || !predictions || !predictions.length) return;

  const validPreds = predictions.filter(p => p.feature_contributions && p.feature_contributions.length > 0);
  if (!validPreds.length) {
    sectionEl.style.display = 'none';
    return;
  }

  sectionEl.style.display = 'block';
  
  // Populate model dropdown
  selectEl.innerHTML = validPreds.map(p => {
    const name = (p.model_used || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    return `<option value="${p.model_used}">${name}</option>`;
  }).join('');

  // Default selection: random_forest, or best model, or first valid
  const defaultModel = validPreds.some(p => p.model_used === 'random_forest') ? 'random_forest' : validPreds[0].model_used;
  selectEl.value = defaultModel;

  const renderSelected = () => {
    const selectedVal = newSelectEl.value;
    const pred = validPreds.find(p => p.model_used === selectedVal);
    if (pred) {
      renderExplanations(pred.feature_contributions, riskListEl, protectiveListEl);
    }
  };

  // Re-bind listener without duplicating
  const newSelectEl = selectEl.cloneNode(true);
  selectEl.parentNode.replaceChild(newSelectEl, selectEl);
  newSelectEl.addEventListener('change', renderSelected);
  renderSelected();
}

function renderExplanations(contributions, riskListEl, protectiveListEl) {
  const riskFactors = contributions.filter(c => c.contribution > 0);
  const protectiveFactors = contributions.filter(c => c.contribution < 0);

  const maxVal = Math.max(...contributions.map(c => Math.abs(c.contribution)), 1);

  const buildHtml = (factors, isRisk) => {
    if (!factors.length) {
      return `<div class="text-muted small py-2 text-center">No significant ${isRisk ? 'risk-increasing' : 'protective'} factors.</div>`;
    }
    return factors.map(c => {
      const pctWidth = Math.max(5, (Math.abs(c.contribution) / maxVal * 100)).toFixed(0);
      const sign = c.contribution > 0 ? '+' : '';
      const impactClass = isRisk ? 'text-risk' : 'text-protective';
      const barClass = isRisk ? 'bg-risk' : 'bg-protective';
      return `
        <div class="explanation-item">
          <div class="explanation-meta">
            <span class="explanation-name">${c.label}</span>
            <span class="explanation-values">${c.value} <span class="text-muted" style="font-size:0.7rem;">(avg: ${c.baseline})</span></span>
            <span class="explanation-impact ${impactClass}">${sign}${c.contribution.toFixed(1)}%</span>
          </div>
          <div class="explanation-bar-bg">
            <div class="explanation-bar ${barClass}" style="width: ${pctWidth}%"></div>
          </div>
        </div>
      `;
    }).join('');
  };

  riskListEl.innerHTML = buildHtml(riskFactors, true);
  protectiveListEl.innerHTML = buildHtml(protectiveFactors, false);
}

// ── Navbar active link ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === path || (href !== '/' && path.startsWith(href))) {
      link.classList.add('active');
    }
  });
  initPage();
});

// ── Route-specific initialization ─────────────────────────────────────────
function initPage() {
  const path = window.location.pathname;
  if (path === '/' || path === '/index')     initHome();
  if (path === '/predict')                   initPredictForm();
  if (path === '/result')                    initResultPage();
  if (path === '/dashboard')                 initDashboard();
}

// ════════════════════════════════════════════════════════════════
// HOME PAGE
// ════════════════════════════════════════════════════════════════
function initHome() {
  // Animate stat numbers
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count);
    const isFloat = el.dataset.count.includes('.');
    const suffix  = el.dataset.suffix || '';
    let current = 0;
    const step  = target / 60;
    const timer = setInterval(() => {
      current += step;
      if (current >= target) { current = target; clearInterval(timer); }
      el.textContent = isFloat
        ? current.toFixed(1) + suffix
        : Math.floor(current) + suffix;
    }, 16);
  });
}

// ════════════════════════════════════════════════════════════════
// PREDICTION FORM
// ════════════════════════════════════════════════════════════════
function initPredictForm() {
  const form = $('prediction-form');
  if (!form) return;

  // Progress indicator
  const inputs = form.querySelectorAll('input[required], select[required]');
  const steps  = document.querySelectorAll('.progress-step');
  const perStep = Math.ceil(inputs.length / (steps.length || 1));

  function updateProgress() {
    let filled = 0;
    inputs.forEach(i => { if (i.value !== '') filled++; });
    steps.forEach((s, idx) => {
      s.classList.toggle('active', filled > idx * perStep);
    });
  }
  inputs.forEach(i => i.addEventListener('input', updateProgress));
  inputs.forEach(i => i.addEventListener('change', updateProgress));

  // Form submit
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const body = {};
    fd.forEach((v, k) => body[k] = isNaN(v) ? v : Number(v));

    showSpinner();
    try {
      const res  = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      hideSpinner();

      if (!res.ok || data.error) {
        showAlert('danger', data.error || 'Prediction failed. Check if models are trained.');
        return;
      }
      // Store & redirect
      sessionStorage.setItem('predResult', JSON.stringify(data));
      window.location.href = '/result';
    } catch (err) {
      hideSpinner();
      showAlert('danger', 'Network error: ' + err.message);
    }
  });
}

function showAlert(type, msg) {
  let box = $('form-alert');
  if (!box) {
    box = document.createElement('div');
    box.id = 'form-alert';
    document.querySelector('.predict-section')?.prepend(box);
  }
  box.className = `alert alert-${type} fade-in`;
  box.textContent = msg;
  box.style.display = 'block';
  setTimeout(() => { box.style.display = 'none'; }, 6000);
}

// ════════════════════════════════════════════════════════════════
// RESULT PAGE
// ════════════════════════════════════════════════════════════════
function initResultPage() {
  const raw = sessionStorage.getItem('predResult');
  if (!raw) { window.location.href = '/predict'; return; }

  const data = JSON.parse(raw);
  
  // Set Patient Metadata
  const metaText = `Patient Name: <strong>${data.patient_name || 'Anonymous'}</strong> &nbsp;|&nbsp; Age: <strong>${data.patient_age || '—'}</strong> &nbsp;|&nbsp; Sex: <strong>${data.patient_sex || '—'}</strong>`;
  const metaEl = $('patient-meta');
  if (metaEl) {
    metaEl.innerHTML = metaText;
  }
  
  const idBadge = $('patient-id-badge');
  if (idBadge) {
    idBadge.textContent = `ID: ${data.patient_id || '—'}`;
  }

  // Populate predictions comparison table
  const tbody = $('result-table-tbody');
  if (tbody && data.predictions) {
    tbody.innerHTML = data.predictions.map(p => {
      const name = (p.model_used || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      const predLbl = p.prediction === 1 ? 'Heart Disease' : 'No Disease';
      const predCls = p.prediction === 1 ? 'badge-disease' : 'badge-healthy';
      const riskCls = (p.risk_level || 'Low').toLowerCase();
      const riskBadgeCls = `badge-${riskCls}`;
      
      return `<tr>
        <td><strong>${name}</strong></td>
        <td><span class="badge ${predCls}">${predLbl}</span></td>
        <td><span class="fw-bold" style="font-size: 0.95rem;">${parseFloat(p.probability).toFixed(1)}%</span></td>
        <td><span class="badge ${riskBadgeCls}">${p.risk_level}</span></td>
        <td class="text-muted small" style="line-height: 1.4; max-width: 350px;">${p.recommendation}</td>
      </tr>`;
    }).join('');

    // Setup Local Feature Explanations
    setupExplanationSelector(
      data.predictions,
      $('explain-model-select'),
      $('risk-factors-list'),
      $('protective-factors-list'),
      $('explanation-section')
    );
  }
}

function setText(id, val) { if ($(id)) $(id).textContent = val; }

function drawGauge(percent, risk) {
  const canvas = $('riskGauge');
  if (!canvas) return;
  const ctx    = canvas.getContext('2d');
  const cx     = canvas.width  / 2;
  const cy     = canvas.height / 2;
  const r      = 80;

  const colorMap = { low: '#10b981', moderate: '#f59e0b', high: '#ef4444' };
  const color    = colorMap[risk] || '#e84393';

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Background arc
  ctx.beginPath();
  ctx.arc(cx, cy, r, Math.PI * 0.75, Math.PI * 0.25, false);
  ctx.strokeStyle = 'rgba(255,255,255,0.07)';
  ctx.lineWidth   = 16;
  ctx.lineCap     = 'round';
  ctx.stroke();

  // Value arc
  const startAngle = Math.PI * 0.75;
  const endAngle   = startAngle + (Math.PI * 1.5) * (percent / 100);
  ctx.beginPath();
  ctx.arc(cx, cy, r, startAngle, endAngle, false);
  ctx.strokeStyle = color;
  ctx.lineWidth   = 16;
  ctx.lineCap     = 'round';
  ctx.shadowColor = color;
  ctx.shadowBlur  = 20;
  ctx.stroke();
  ctx.shadowBlur  = 0;

  // Centre text
  ctx.fillStyle   = '#f1f5f9';
  ctx.font        = 'bold 1.8rem Inter, sans-serif';
  ctx.textAlign   = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(percent.toFixed(1) + '%', cx, cy - 8);

  ctx.fillStyle   = color;
  ctx.font        = '700 0.8rem Inter, sans-serif';
  ctx.fillText(risk.toUpperCase(), cx, cy + 22);
}

// ════════════════════════════════════════════════════════════════
// DASHBOARD
// ════════════════════════════════════════════════════════════════
function initDashboard() {
  loadStats();
  loadRecentPredictions();
  loadMetricsCharts();
}

async function loadStats() {
  try {
    const res  = await fetch('/api/analytics/stats');
    const json = await res.json();
    const d    = json.data || {};
    setText('kpi-total',      d.total         ?? 0);
    setText('kpi-disease',    d.disease        ?? 0);
    setText('kpi-no-disease', d.no_disease     ?? 0);
    setText('kpi-high-risk',  d.high_risk      ?? 0);
    setText('kpi-rate',       fmtPct(d.disease_rate ?? 0));

    // Donut chart
    renderDonut('riskDonut', [d.low_risk||0, d.moderate_risk||0, d.high_risk||0],
      ['Low','Moderate','High'], ['#10b981','#f59e0b','#ef4444']);
  } catch(e) { console.warn('Stats error:', e); }
}

let currentRecentPredictions = [];

async function loadRecentPredictions() {
  try {
    const res  = await fetch('/api/analytics/recent');
    const json = await res.json();
    const tbody = $('predictions-tbody');
    if (!tbody) return;

    if (!json.predictions?.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No predictions yet</td></tr>';
      return;
    }

    currentRecentPredictions = json.predictions;
    tbody.innerHTML = json.predictions.map((p, idx) => {
      const riskCls = p.risk_level?.toLowerCase() || 'low';
      const predLbl = p.prediction === 1 ? 'Disease' : 'Healthy';
      const predCls = p.prediction === 1 ? 'disease' : 'healthy';
      const outcomeVal = p.actual_outcome;
      let outcomeSelect = `<select class="form-select form-select-sm" style="width:100px; font-size:0.75rem; background-color: var(--bg-card); color: var(--text-100); border: 1px solid var(--border);" onchange="updateOutcome(${p.patient_id}, this.value)">
          <option value="" ${outcomeVal === null ? 'selected' : ''}>Unknown</option>
          <option value="0" ${outcomeVal === 0 ? 'selected' : ''}>Healthy</option>
          <option value="1" ${outcomeVal === 1 ? 'selected' : ''}>Disease</option>
        </select>`;

      return `<tr>
        <td><input type="checkbox" class="pred-checkbox" value="${p.id}" onclick="updateBulkDeleteBtn()"></td>
        <td>${p.id}</td>
        <td>${p.patient_name || '—'}</td>
        <td>${(p.model_used||'').replace(/_/g,' ')}</td>
        <td><span class="badge badge-${predCls}">${predLbl}</span></td>
        <td>${fmtPct(p.probability)}</td>
        <td><span class="badge badge-${riskCls}">${p.risk_level}</span></td>
        <td>${outcomeSelect}</td>
        <td>${fmtDate(p.predicted_at)}</td>
        <td>
          <button class="btn btn-sm btn-outline me-1 py-0 px-2" style="font-size:0.75rem;" onclick="viewReport(${idx})">👁️ View</button>
          <button class="btn btn-sm btn-outline me-1 py-0 px-2" style="font-size:0.75rem;" onclick="openEditModal(${p.id}, '${(p.patient_name || '').replace(/'/g, "\\'")}', '${p.risk_level}')">✏️ Edit</button>
          <button class="btn btn-sm btn-outline text-danger py-0 px-2" style="font-size:0.75rem;" onclick="deletePrediction(${p.id})">🗑️ Delete</button>
        </td>
      </tr>`;
    }).join('');
    updateBulkDeleteBtn(); // Reset button state
  } catch(e) { console.warn('Recent predictions error:', e); }
}

function toggleSelectAll(masterCb) {
  const cbs = document.querySelectorAll('.pred-checkbox');
  cbs.forEach(cb => cb.checked = masterCb.checked);
  updateBulkDeleteBtn();
}

function updateBulkDeleteBtn() {
  const cbs = document.querySelectorAll('.pred-checkbox:checked');
  const btn = $('bulk-delete-btn');
  if (btn) btn.style.display = cbs.length > 0 ? 'inline-block' : 'none';
  updateSelectedComparison();
}

let comparisonChartInstance = null;

async function updateSelectedComparison() {
  const cbs = document.querySelectorAll('.pred-checkbox:checked');
  const compCard = $('comparison-card');
  if (!compCard) return;

  if (cbs.length === 0) {
    compCard.style.display = 'none';
    if (comparisonChartInstance) {
      comparisonChartInstance.destroy();
      comparisonChartInstance = null;
    }
    return;
  }

  compCard.style.display = 'block';
  const countBadge = $('comparison-count-badge');
  if (countBadge) countBadge.textContent = `${cbs.length} Selected`;

  const selectedItems = [];
  cbs.forEach(cb => {
    const predId = Number(cb.value);
    const item = currentRecentPredictions.find(p => p.id === predId);
    if (item) {
      selectedItems.push(item);
    }
  });

  const tbody = $('comparison-tbody');
  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Fetching multi-model details...</td></tr>';
  }

  try {
    const promises = selectedItems.map(item => 
      fetch(`/api/patient/${item.patient_id}/predictions`)
        .then(r => r.json())
        .then(json => ({
          patient_name: item.patient_name || 'Anonymous',
          patient_id: item.patient_id,
          age: item.patient_data ? item.patient_data.age : '—',
          sex: item.patient_data ? (item.patient_data.sex === 1 ? 'M' : 'F') : '—',
          predictions: json.status === 'ok' ? json.predictions : []
        }))
    );

    const patientsData = await Promise.all(promises);
    
    // 1. Render Table Rows
    const modelsList = ['logistic_regression', 'decision_tree', 'random_forest', 'neural_network'];
    
    tbody.innerHTML = patientsData.map(p => {
      const cols = modelsList.map(m => {
        const pred = p.predictions.find(x => x.model_used === m);
        if (!pred) return `<td><span class="text-muted">—</span></td>`;
        
        const isDisease = pred.prediction === 1;
        const colorCls = isDisease ? 'text-danger' : 'text-success';
        const symbol = isDisease ? '🔴' : '🟢';
        const label = isDisease ? 'Disease' : 'Healthy';
        return `<td>
          <span class="fw-bold ${colorCls}">${symbol} ${label}</span>
          <div class="small text-muted" style="font-size:0.75rem;">Prob: ${pred.probability.toFixed(1)}%</div>
        </td>`;
      }).join('');

      // Calculate consensus
      const diseaseCount = p.predictions.filter(x => x.prediction === 1).length;
      const totalCount = p.predictions.length;
      let consensusCls = 'badge-low';
      let consensusLbl = 'Low Risk (Healthy)';
      if (diseaseCount >= 3) {
        consensusCls = 'badge-high';
        consensusLbl = 'High Risk (Disease)';
      } else if (diseaseCount === 2) {
        consensusCls = 'badge-moderate';
        consensusLbl = 'Moderate Risk';
      }

      const consensusCol = `<td>
        <span class="badge ${consensusCls}">${consensusLbl}</span>
        <div class="small text-muted" style="font-size:0.72rem; margin-top:2px;">${diseaseCount}/${totalCount} models agree</div>
      </td>`;

      return `<tr>
        <td>
          <div class="fw-bold text-white">${p.patient_name}</div>
          <div class="small text-muted" style="font-size:0.75rem;">Age: ${p.age} | Sex: ${p.sex} | ID: ${p.patient_id}</div>
        </td>
        ${cols}
        ${consensusCol}
      </tr>`;
    }).join('');

    // 2. Render Probability Comparison Chart
    const chartRow = $('comparison-chart-row');
    const canvas = $('comparisonChart');
    
    if (chartRow && canvas && patientsData.length > 0) {
      chartRow.style.display = 'block';
      const labels = patientsData.map(p => p.patient_name);
      
      const datasets = [
        { label: 'Logistic Regression', data: [], color: '#3b82f6' },
        { label: 'Decision Tree',       data: [], color: '#6c63ff' },
        { label: 'Random Forest',       data: [], color: '#e84393' },
        { label: 'Neural Network',      data: [], color: '#10b981' }
      ];

      patientsData.forEach(p => {
        modelsList.forEach((m, idx) => {
          const pred = p.predictions.find(x => x.model_used === m);
          datasets[idx].data.push(pred ? pred.probability / 100 : 0);
        });
      });

      if (comparisonChartInstance) {
        comparisonChartInstance.destroy();
      }

      const ctx = canvas.getContext('2d');
      comparisonChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: datasets.map(d => ({
            label: d.label,
            data: d.data,
            backgroundColor: d.color + 'cc',
            borderColor: d.color,
            borderWidth: 1,
            borderRadius: 4
          }))
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              min: 0, max: 1,
              grid: { color: 'rgba(255,255,255,0.05)' },
              ticks: { color: '#94a3b8', callback: v => (v*100).toFixed(0)+'%' }
            },
            x: {
              grid: { display: false },
              ticks: { color: '#94a3b8' }
            }
          },
          plugins: {
            legend: { position: 'top', labels: { color: '#94a3b8', font: { family:'Inter' } } }
          }
        }
      });
    } else if (chartRow) {
      chartRow.style.display = 'none';
    }

  } catch (err) {
    console.error('Error loading comparison details:', err);
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">Error loading comparison: ${err.message}</td></tr>`;
    }
  }
}

async function bulkDeletePredictions() {
  const cbs = document.querySelectorAll('.pred-checkbox:checked');
  if (!cbs.length) return;
  const ids = Array.from(cbs).map(cb => Number(cb.value));
  
  if (!confirm(`Are you sure you want to delete ${ids.length} selected prediction(s)?`)) return;

  try {
    const res = await fetch('/api/predictions/bulk', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids })
    });
    const json = await res.json();
    if (res.ok && json.status === 'success') {
      const masterCb = $('select-all-preds');
      if (masterCb) masterCb.checked = false;
      loadRecentPredictions();
      loadStats();
    } else {
      alert('Error bulk deleting predictions: ' + (json.message || 'Unknown error'));
    }
  } catch (err) {
    alert('Error bulk deleting predictions: ' + err.message);
  }
}

let reportModalInstance = null;

async function viewReport(idx) {
  const p = currentRecentPredictions[idx];
  if (!p) return;
  
  const nameEl = $('report-meta-name');
  const ageEl = $('report-meta-age');
  const sexEl = $('report-meta-sex');
  const idEl = $('report-meta-id');
  
  if (nameEl) nameEl.textContent = p.patient_name || 'Anonymous';
  if (ageEl) ageEl.textContent = p.patient_data ? p.patient_data.age : '—';
  if (sexEl) sexEl.textContent = p.patient_data ? (p.patient_data.sex === 1 ? 'Male' : 'Female') : '—';
  if (idEl) idEl.textContent = p.patient_id || '—';
  
  const detailsEl = $('report-patient-details');
  const recEl = $('report-recommendation');
  
  if (p.patient_data) {
    const d = p.patient_data;
    const sexStr = d.sex === 1 ? 'Male' : 'Female';
    const cpMap = {0: 'Typical Angina', 1: 'Atypical Angina', 2: 'Non-Anginal', 3: 'Asymptomatic'};
    const cpStr = cpMap[d.cp] || d.cp;
    const fbsStr = d.fbs === 1 ? 'Yes' : 'No';
    const restecgMap = {0: 'Normal', 1: 'ST-T Abnormality', 2: 'LV Hypertrophy'};
    const restecgStr = restecgMap[d.restecg] || d.restecg;
    const exangStr = d.exang === 1 ? 'Yes' : 'No';
    const slopeMap = {0: 'Upsloping', 1: 'Flat', 2: 'Downsloping'};
    const slopeStr = slopeMap[d.slope] || d.slope;
    const thalMap = {1: 'Normal', 2: 'Fixed Defect', 3: 'Reversible Defect'};
    const thalStr = thalMap[d.thal] || d.thal;

    detailsEl.innerHTML = `
      <div class="form-grid" style="pointer-events: none;">
        <div class="form-group">
          <label class="small text-muted mb-1">Age <span class="unit">yrs</span></label>
          <input class="form-control form-control-sm" value="${d.age}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Sex</label>
          <input class="form-control form-control-sm" value="${sexStr}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Chest Pain Type</label>
          <input class="form-control form-control-sm" value="${cpStr}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Resting BP <span class="unit">mmHg</span></label>
          <input class="form-control form-control-sm" value="${d.trestbps}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Cholesterol <span class="unit">mg/dl</span></label>
          <input class="form-control form-control-sm" value="${d.chol}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Fasting BS &gt; 120</label>
          <input class="form-control form-control-sm" value="${fbsStr}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Resting ECG</label>
          <input class="form-control form-control-sm" value="${restecgStr}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Max Heart Rate <span class="unit">bpm</span></label>
          <input class="form-control form-control-sm" value="${d.thalach}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Exercise Angina</label>
          <input class="form-control form-control-sm" value="${exangStr}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">ST Depression (Oldpeak)</label>
          <input class="form-control form-control-sm" value="${d.oldpeak}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">ST Slope</label>
          <input class="form-control form-control-sm" value="${slopeStr}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Major Vessels (CA)</label>
          <input class="form-control form-control-sm" value="${d.ca}" disabled/>
        </div>
        <div class="form-group">
          <label class="small text-muted mb-1">Thalassemia (Thal)</label>
          <input class="form-control form-control-sm" value="${thalStr}" disabled/>
        </div>
      </div>
    `;
  } else {
    detailsEl.innerHTML = `<div class="col-12 text-muted">No patient details available.</div>`;
  }
  
  const tbody = $('report-comparison-tbody');
  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center py-2">Loading...</td></tr>';
  }
  
  if (!reportModalInstance) {
    reportModalInstance = new bootstrap.Modal($('reportModal'));
  }
  reportModalInstance.show();

  if (p.patient_id && tbody) {
    try {
      const res = await fetch(`/api/patient/${p.patient_id}/predictions`);
      const json = await res.json();
      if (json.status === 'ok' && json.predictions) {
        tbody.innerHTML = json.predictions.map(pred => {
          const mName = (pred.model_used||'').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          const predLbl = pred.prediction === 1 ? 'Heart Disease' : 'No Disease';
          const predCls = pred.prediction === 1 ? 'badge-disease' : 'badge-healthy';
          const riskCls = (pred.risk_level||'Low').toLowerCase();
          const rec = pred.recommendation || '<span class="text-muted">No recommendation available.</span>';
          return `<tr>
            <td><strong>${mName}</strong></td>
            <td><span class="badge ${predCls}">${predLbl}</span></td>
            <td>${fmtPct(pred.probability)}</td>
            <td><span class="badge badge-${riskCls}">${pred.risk_level}</span></td>
            <td style="white-space: normal; max-width: 400px; font-size: 0.8rem; line-height: 1.4;">${rec}</td>
          </tr>`;
        }).join('');

        // Setup Local Feature Explanations in modal
        setupExplanationSelector(
          json.predictions,
          $('modal-explain-model-select'),
          $('modal-risk-factors-list'),
          $('modal-protective-factors-list'),
          $('modal-explanation-section')
        );
      } else {
        tbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center py-2">Failed to load</td></tr>';
      }
    } catch (e) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center py-2">Error loading</td></tr>';
    }
  } else if (tbody) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center py-2">No patient ID</td></tr>';
  }
}

// ── Edit/Delete Predictions ────────────────────────────────────────────────
let editModalInstance = null;

function openEditModal(id, name, risk) {
  $('edit-pred-id').value = id;
  $('edit-patient-name').value = name;
  $('edit-risk-level').value = risk;
  
  if (!editModalInstance) {
    editModalInstance = new bootstrap.Modal($('editModal'));
  }
  editModalInstance.show();
}

async function submitEdit() {
  const id = $('edit-pred-id').value;
  const patient_name = $('edit-patient-name').value;
  const risk_level = $('edit-risk-level').value;

  try {
    const res = await fetch(`/api/prediction/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_name, risk_level })
    });
    const json = await res.json();
    if (res.ok && json.status === 'success') {
      if (editModalInstance) editModalInstance.hide();
      loadRecentPredictions();
      loadStats();
    } else {
      alert('Error updating prediction: ' + (json.message || 'Unknown error'));
    }
  } catch (err) {
    alert('Error updating prediction: ' + err.message);
  }
}

async function deletePrediction(id) {
  if (!confirm(`Are you sure you want to delete prediction record #${id}?`)) return;

  try {
    const res = await fetch(`/api/prediction/${id}`, { method: 'DELETE' });
    const json = await res.json();
    if (res.ok && json.status === 'success') {
      loadRecentPredictions();
      loadStats();
    } else {
      alert('Error deleting prediction: ' + (json.message || 'Unknown error'));
    }
  } catch (err) {
    alert('Error deleting prediction: ' + err.message);
  }
}

async function loadMetricsCharts() {
  try {
    const res  = await fetch('/api/analytics/metrics');
    const json = await res.json();
    const m    = json.metrics || [];
    if (!m.length) return;

    const labels  = m.map(x => (x.model_name||x.model||'').replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()));
    const acc     = m.map(x => +(x.accuracy||0));
    const f1      = m.map(x => +(x.f1_score||0));
    const auc     = m.map(x => +(x.roc_auc||0));

    renderGroupedBar('metricsBar', labels,
      [{ label:'Accuracy', data: acc, color:'#e84393' },
       { label:'F1 Score', data: f1,  color:'#6c63ff' },
       { label:'ROC AUC',  data: auc, color:'#10b981' }]);
  } catch(e) { console.warn('Metrics error:', e); }
}



// ════════════════════════════════════════════════════════════════
// CHART HELPERS (Chart.js)
// ════════════════════════════════════════════════════════════════
const CHART_DEFAULTS = {
  responsive: true,
  plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } } },
};

function renderDonut(canvasId, data, labels, colors) {
  const ctx = $(canvasId)?.getContext('2d');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors, borderWidth: 0, hoverOffset: 6 }]
    },
    options: {
      ...CHART_DEFAULTS,
      cutout: '72%',
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 16, font: { family: 'Inter' } } }
      }
    }
  });
}

function renderGroupedBar(canvasId, labels, datasets) {
  const ctx = $(canvasId)?.getContext('2d');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: datasets.map(d => ({
        label: d.label,
        data: d.data,
        backgroundColor: d.color + 'cc',
        borderColor: d.color,
        borderWidth: 1,
        borderRadius: 4,
      }))
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        y: {
          min: 0, max: 1,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#94a3b8', callback: v => (v*100).toFixed(0)+'%' },
        },
        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
      },
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: { position: 'top', labels: { color: '#94a3b8', font: { family:'Inter' }, padding: 16 } }
      }
    }
  });
}

// ── Models Comparison Modal ───────────────────────────────────────────────
let modelsModalInstance = null;

function openModelsComparisonModal() {
  if (!modelsModalInstance) {
    modelsModalInstance = new bootstrap.Modal($('modelsModal'));
  }
  modelsModalInstance.show();
  loadModelsMetrics();
}

async function loadModelsMetrics() {
  const tbody = $('models-metrics-tbody');
  const notice = $('models-best-notice');
  if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">Loading metrics...</td></tr>';
  if (notice) notice.style.display = 'none';

  try {
    const res = await fetch('/api/evaluation/metrics');
    const json = await res.json();
    
    if (res.ok && json.status === 'ok') {
      const metrics = json.metrics;
      if (Object.keys(metrics).length === 0) {
         if (tbody) tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No patients have actual outcomes recorded. Set actual outcomes in the Recent Predictions table.</td></tr>';
         return;
      }

      let bestModel = null;
      let maxAcc = -1;

      tbody.innerHTML = Object.entries(metrics).map(([model, m]) => {
        const name = model.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        const acc = (m.accuracy * 100).toFixed(1) + '%';
        const prec = (m.precision * 100).toFixed(1) + '%';
        const rec = (m.recall * 100).toFixed(1) + '%';
        const f1 = (m.f1_score * 100).toFixed(1) + '%';
        const auc = m.roc_auc ? (m.roc_auc * 100).toFixed(1) + '%' : 'N/A';
        
        if (m.accuracy > maxAcc) {
            maxAcc = m.accuracy;
            bestModel = name;
        }

        return `<tr>
          <td><strong>${name}</strong></td>
          <td>${acc}</td>
          <td>${prec}</td>
          <td>${rec}</td>
          <td>${f1}</td>
          <td>${auc}</td>
          <td>${m.samples}</td>
        </tr>`;
      }).join('');
      
      if (notice && bestModel) {
          notice.innerHTML = `<strong>Best Performing Model:</strong> ${bestModel} with ${ (maxAcc * 100).toFixed(1) }% accuracy.`;
          notice.style.display = 'block';
      }

    } else {
      if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error: ${json.message}</td></tr>`;
    }
  } catch (err) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error loading metrics: ${err.message}</td></tr>`;
  }
}

async function updateOutcome(patient_id, outcomeValue) {
    let actual_outcome = outcomeValue === "" ? null : Number(outcomeValue);
    try {
        const res = await fetch(`/api/patient/${patient_id}/outcome`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ actual_outcome })
        });
        const json = await res.json();
        if (!res.ok || json.status !== 'success') {
            alert('Failed to update actual outcome: ' + (json.message || 'Unknown error'));
            loadRecentPredictions(); // reload to revert select
        }
    } catch (err) {
        alert('Error updating outcome: ' + err.message);
        loadRecentPredictions();
    }
}
