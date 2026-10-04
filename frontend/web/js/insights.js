/**
 * insights.js — Model performance charts and feature importance visualisations.
 */

let insightsInitDone = false;
const insightCharts = {};

function initInsights() {
  if (insightsInitDone) return;
  insightsInitDone = true;

  _wireInsightsTabs();
  _loadModelMetrics();
  _loadFeatureImportances();
}

function _wireInsightsTabs() {
  document.querySelectorAll('#page-insights .tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#page-insights .tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('#page-insights .tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab)?.classList.add('active');
      Object.values(insightCharts).forEach(c => c?.resize?.());
    });
  });
}

// ── Model metrics ─────────────────────────────────────────────────────────────
async function _loadModelMetrics() {
  try {
    const meta = await Api.getModelMetrics();
    _renderMetricsTable(meta);
    _renderModelComparisonChart(meta);
    _renderErrorChart(meta);
  } catch(e) { console.error('Metrics error', e); }
}

function _renderMetricsTable(meta) {
  const tbody = document.getElementById('metrics-tbody');
  if (!tbody) return;

  const rows = Object.entries(meta.all_results).map(([name, v]) => {
    const isBest = name === meta.best_model;
    return `<tr>
      <td>
        ${name}
        ${isBest ? '<span class="badge badge--best" style="margin-left:8px">Best</span>' : ''}
      </td>
      <td>${v.cv_r2_mean.toFixed(4)} ± ${v.cv_r2_std.toFixed(4)}</td>
      <td style="${isBest ? 'color:var(--clr-accent3);font-weight:700' : ''}">${v.test_r2.toFixed(4)}</td>
      <td>₹${Math.round(v.mae).toLocaleString('en-IN')}</td>
      <td>₹${Math.round(v.rmse).toLocaleString('en-IN')}</td>
      <td style="${isBest ? 'color:var(--clr-accent3)' : ''}">${v.mape.toFixed(2)}%</td>
    </tr>`;
  });
  tbody.innerHTML = rows.join('');
}

function _renderModelComparisonChart(meta) {
  const ctx = document.getElementById('chart-model-r2')?.getContext('2d');
  if (!ctx) return;

  const names  = Object.keys(meta.all_results);
  const cvR2   = names.map(n => meta.all_results[n].cv_r2_mean);
  const testR2 = names.map(n => meta.all_results[n].test_r2);

  insightCharts.modelR2 = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: names,
      datasets: [
        { label: 'CV R²',   data: cvR2,   backgroundColor: 'rgba(14,165,233,.6)',  borderColor: '#0ea5e9', borderWidth: 1, borderRadius: 4 },
        { label: 'Test R²', data: testR2, backgroundColor: 'rgba(249,115,22,.75)', borderColor: '#f97316', borderWidth: 1, borderRadius: 4 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#8b949e' } },
        tooltip: {
          backgroundColor: '#1c2333', titleColor: '#e6edf3', bodyColor: '#8b949e',
          borderColor: '#30363d', borderWidth: 1,
        },
      },
      scales: {
        x: { ticks: { color: '#8b949e' }, grid: { color: 'rgba(48,54,61,.4)' } },
        y: {
          min: 0.75, max: 1.0,
          ticks: { color: '#8b949e', callback: v => v.toFixed(2) },
          grid: { color: 'rgba(48,54,61,.4)' },
          title: { display: true, text: 'R² Score', color: '#8b949e' },
        },
      },
    },
  });
}

function _renderErrorChart(meta) {
  const ctx = document.getElementById('chart-model-error')?.getContext('2d');
  if (!ctx) return;

  const names = Object.keys(meta.all_results);
  insightCharts.modelError = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: names,
      datasets: [
        { label: 'MAE (₹)',  data: names.map(n => meta.all_results[n].mae),  backgroundColor: 'rgba(168,85,247,.6)',  borderColor: '#a855f7', borderWidth: 1, borderRadius: 4 },
        { label: 'RMSE (₹)', data: names.map(n => meta.all_results[n].rmse), backgroundColor: 'rgba(196,181,253,.5)', borderColor: '#c4b5fd', borderWidth: 1, borderRadius: 4 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#8b949e' } },
        tooltip: {
          backgroundColor: '#1c2333', titleColor: '#e6edf3', bodyColor: '#8b949e',
          borderColor: '#30363d', borderWidth: 1,
          callbacks: { label: ctx => ` ${ctx.dataset.label}: ₹${Math.round(ctx.parsed.y).toLocaleString('en-IN')}` },
        },
      },
      scales: {
        x: { ticks: { color: '#8b949e' }, grid: { color: 'rgba(48,54,61,.4)' } },
        y: {
          ticks: { color: '#8b949e', callback: v => '₹' + (v/1000).toFixed(0) + 'k' },
          grid: { color: 'rgba(48,54,61,.4)' },
          title: { display: true, text: 'Error (INR)', color: '#8b949e' },
        },
      },
    },
  });
}

// ── Feature importances ───────────────────────────────────────────────────────
async function _loadFeatureImportances() {
  try {
    const fi = await Api.getFeatureImportances();
    const top = fi.slice(0, 15);
    _renderFIChart(top);
    _renderFITable(top);
  } catch(e) { console.error('Feature importance error', e); }
}

function _renderFIChart(top) {
  const ctx = document.getElementById('chart-fi')?.getContext('2d');
  if (!ctx) return;

  // Colour by feature group
  function getColor(feat) {
    const numFeats = ['travelers','trip_days','activities_count','booking_advance_days','distance_km'];
    const ordFeats = ['accommodation_type','travel_season','meal_plan'];
    if (numFeats.includes(feat)) return 'rgba(249,115,22,.75)';
    if (ordFeats.includes(feat)) return 'rgba(14,165,233,.75)';
    return 'rgba(168,85,247,.6)';
  }

  insightCharts.fi = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top.map(d => d.feature),
      datasets: [{
        label: 'Importance',
        data: top.map(d => d.importance),
        backgroundColor: top.map(d => getColor(d.feature)),
        borderRadius: 4,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1c2333', titleColor: '#e6edf3', bodyColor: '#8b949e',
          borderColor: '#30363d', borderWidth: 1,
          callbacks: { label: ctx => ` ${(ctx.parsed.x * 100).toFixed(2)}%` },
        },
      },
      scales: {
        x: {
          ticks: { color: '#8b949e', callback: v => (v * 100).toFixed(0) + '%' },
          grid: { color: 'rgba(48,54,61,.4)' },
          title: { display: true, text: 'Importance Score', color: '#8b949e' },
        },
        y: { ticks: { color: '#e6edf3', font: { size: 11 } }, grid: { display: false } },
      },
    },
  });
}

function _renderFITable(top) {
  const tbody = document.getElementById('fi-tbody');
  if (!tbody) return;

  function group(feat) {
    const num = ['travelers','trip_days','activities_count','booking_advance_days','distance_km'];
    const ord = ['accommodation_type','travel_season','meal_plan'];
    if (num.includes(feat)) return '<span class="badge badge--best">Numerical</span>';
    if (ord.includes(feat)) return '<span class="badge badge--ok">Ordinal</span>';
    return '<span class="badge" style="background:rgba(168,85,247,.12);color:#a855f7;border:1px solid rgba(168,85,247,.3)">Categorical</span>';
  }

  tbody.innerHTML = top.map((d, i) => `
    <tr>
      <td style="color:var(--clr-text-muted);font-family:var(--font-mono)">#${i+1}</td>
      <td style="font-family:var(--font-mono);font-size:.82rem">${d.feature}</td>
      <td>${group(d.feature)}</td>
      <td style="font-family:var(--font-mono);color:var(--clr-accent)">${(d.importance * 100).toFixed(2)}%</td>
      <td>
        <div style="height:5px;background:var(--clr-border);border-radius:3px;min-width:80px">
          <div style="height:100%;width:${(d.importance * 100 / top[0].importance * 100).toFixed(0)}%;background:var(--clr-accent);border-radius:3px;transition:width 1s ease"></div>
        </div>
      </td>
    </tr>`).join('');
}
