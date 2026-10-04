/**
 * predict.js — All logic for the Predict page:
 *   form handling, API calls, gauge rendering, breakdown bars, comparable trips.
 */

let gaugeChart = null;
let predictInitDone = false;

// ── Destinations list ─────────────────────────────────────────────────────────
const DESTINATIONS = [
  'Agra','Ahmedabad','Allahabad','Amritsar','Aurangabad',
  'Bhubaneswar','Chennai','Coorg','Darjeeling','Delhi',
  'Dharamshala','Goa','Hampi','Hyderabad','Jaipur',
  'Jaisalmer','Jodhpur','Kochi','Kodaikanal','Kolkata',
  'Leh','Lonavala','Lucknow','Madurai','Manali',
  'Mount Abu','Mumbai','Munnar','Mysore','Nainital',
  'Ooty','Pondicherry','Port Blair','Pune','Puri',
  'Ranthambore','Rishikesh','Shimla','Srinagar','Udaipur',
  'Varanasi','Varkala','Vizag',
];

// ── Destination → type mapping (best-effort) ──────────────────────────────────
const DEST_TYPE_MAP = {
  Goa:'Beach', Puri:'Beach', Varkala:'Beach', 'Port Blair':'Beach',
  Manali:'Mountain', Shimla:'Mountain', Dharamshala:'Mountain',
  Nainital:'Mountain', Mussoorie:'Mountain', Leh:'Mountain',
  Srinagar:'Mountain', Darjeeling:'Mountain', Munnar:'Mountain',
  Coorg:'Mountain', Kodaikanal:'Mountain', Ooty:'Mountain',
  Delhi:'City', Mumbai:'City', Kolkata:'City', Chennai:'City',
  Hyderabad:'City', Pune:'City', Bengaluru:'City', Ahmedabad:'City',
  Lucknow:'City',
  Jaipur:'Heritage', Agra:'Heritage', Udaipur:'Heritage',
  Jodhpur:'Heritage', Jaisalmer:'Heritage', Mysore:'Heritage',
  Hampi:'Heritage', Aurangabad:'Heritage', Lonavala:'Heritage',
  Varanasi:'Religious', Amritsar:'Religious', Madurai:'Religious',
  Allahabad:'Religious', Bhubaneswar:'Religious', Puri:'Religious',
  Rishikesh:'Adventure',
  Ranthambore:'Wildlife',
  Pondicherry:'Nature', Kochi:'Nature', Vizag:'Nature',
  'Mount Abu':'Nature',
};

function getDestType(dest) {
  return DEST_TYPE_MAP[dest] || 'Heritage';
}

// ── Initialise predict page ───────────────────────────────────────────────────
function initPredict() {
  if (predictInitDone) return;
  predictInitDone = true;

  _populateDestinations();
  _wireSliders();
  _wireDestination();
  _wireFormSubmit();
}

function _populateDestinations() {
  const sel = document.getElementById('p-destination');
  if (!sel) return;
  DESTINATIONS.forEach(d => {
    const o = document.createElement('option');
    o.value = o.textContent = d;
    if (d === 'Goa') o.selected = true;
    sel.appendChild(o);
  });
  // Set destination_type after destinations are populated
  _syncDestType();
}

function _wireDestination() {
  const sel = document.getElementById('p-destination');
  if (sel) sel.addEventListener('change', _syncDestType);
}

function _syncDestType() {
  const dest = document.getElementById('p-destination')?.value;
  const typeEl = document.getElementById('p-destination-type');
  if (typeEl && dest) typeEl.value = getDestType(dest);
}

function _wireSliders() {
  const sliders = [
    { id: 'p-travelers',             display: 'p-travelers-val',   suffix: '' },
    { id: 'p-trip-days',             display: 'p-trip-days-val',   suffix: ' days' },
    { id: 'p-activities',            display: 'p-activities-val',  suffix: '' },
    { id: 'p-advance-days',          display: 'p-advance-days-val',suffix: ' days' },
    { id: 'p-distance',              display: 'p-distance-val',    suffix: ' km' },
  ];
  sliders.forEach(({ id, display, suffix }) => {
    const input = document.getElementById(id);
    const val   = document.getElementById(display);
    if (!input || !val) return;
    val.textContent = input.value + suffix;
    input.addEventListener('input', () => { val.textContent = input.value + suffix; });
  });
}

// ── Collect form values ───────────────────────────────────────────────────────
function _collectFormData() {
  const g = id => document.getElementById(id);
  const chip = name => document.querySelector(`input[name="${name}"]:checked`)?.value;

  return {
    destination:          g('p-destination')?.value,
    destination_type:     g('p-destination-type')?.value,
    travelers:            parseInt(g('p-travelers')?.value),
    trip_days:            parseInt(g('p-trip-days')?.value),
    transport_mode:       chip('p-transport') || 'Train',
    accommodation_type:   g('p-accommodation')?.value,
    meal_plan:            g('p-meal-plan')?.value,
    activities_count:     parseInt(g('p-activities')?.value),
    travel_season:        chip('p-season') || 'Shoulder',
    booking_advance_days: parseInt(g('p-advance-days')?.value),
    distance_km:          parseInt(g('p-distance')?.value),
  };
}

// ── Form submit ───────────────────────────────────────────────────────────────
function _wireFormSubmit() {
  const form = document.getElementById('predict-form');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    await _runPrediction();
  });
}

async function _runPrediction() {
  const btn = document.getElementById('predict-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Predicting…';
  }

  try {
    const payload = _collectFormData();
    const [result, trips] = await Promise.all([
      Api.predict(payload),
      Api.comparableTrips(payload).catch(() => []),
    ]);

    _renderResult(result, payload);
    _renderComparableTrips(trips);

    Toast.show('success', 'Prediction ready', fmt(result.predicted_expense));
  } catch (err) {
    Toast.show('error', 'Prediction failed', err.message);
    _showResultEmpty();
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>🔮</span> Predict Expense';
    }
  }
}

// ── Render result panel ───────────────────────────────────────────────────────
function _renderResult(result, payload) {
  const panel = document.getElementById('result-body');
  if (!panel) return;

  const pred  = result.predicted_expense;
  const low   = result.lower_bound;
  const high  = result.upper_bound;
  const mape  = result.mape_pct;

  // Cost breakdown (estimated proportions based on feature importances)
  const accMult = { Budget: 0.08, '2-Star': 0.12, '3-Star': 0.20, '4-Star': 0.30, '5-Star': 0.42 };
  const trMult  = { Bus: 0.06, Train: 0.12, Car: 0.18, Flight: 0.32 };
  const mealMult= { 'Room Only': 0.03, Breakfast: 0.07, 'Half Board': 0.12, 'Full Board': 0.18 };

  const accommodationCost = pred * (accMult[payload.accommodation_type] || 0.20);
  const transportCost     = pred * (trMult[payload.transport_mode] || 0.15);
  const mealCost          = pred * (mealMult[payload.meal_plan] || 0.08);
  const activitiesCost    = pred * 0.05 * payload.activities_count;
  const miscCost          = Math.max(0, pred - accommodationCost - transportCost - mealCost - activitiesCost);

  panel.innerHTML = `
    <div class="prediction-amount">
      <div class="prediction-amount__label">Predicted Total Expense</div>
      <div class="prediction-amount__value" id="pred-counter">₹0</div>
      <div class="prediction-amount__range">
        Range: <span>${fmt(low)}</span> – <span>${fmt(high)}</span>
        <br><span style="font-size:.72rem;color:var(--clr-text-dim)">Based on model MAPE of ${mape.toFixed(1)}%</span>
      </div>
    </div>

    <div class="gauge-wrap">
      <canvas id="gaugeChart" height="160"></canvas>
    </div>

    <div style="margin:20px 0 12px;font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--clr-text-muted);">
      Estimated Cost Breakdown
    </div>
    <div class="breakdown">
      ${_breakdownItem('Accommodation', accommodationCost, pred, '#f97316')}
      ${_breakdownItem('Transport',     transportCost,     pred, '#0ea5e9')}
      ${_breakdownItem('Meals',         mealCost,          pred, '#22c55e')}
      ${_breakdownItem('Activities',    activitiesCost,    pred, '#a855f7')}
      ${_breakdownItem('Misc / Other',  miscCost,          pred, '#6e7681')}
    </div>

    <div id="comparable-section"></div>
  `;

  // Start counter animation
  const counter = document.getElementById('pred-counter');
  if (counter) animateCounter(counter, pred, 1200, '₹');

  // Draw gauge
  _drawGauge(pred, low, high);

  // Trigger bar animations
  requestAnimationFrame(() => {
    document.querySelectorAll('.breakdown__fill').forEach(bar => {
      bar.style.width = bar.dataset.pct + '%';
    });
  });
}

function _breakdownItem(label, value, total, color) {
  const pct = Math.min(100, Math.round((value / total) * 100));
  return `
    <div class="breakdown__item">
      <div class="breakdown__head">
        <span class="breakdown__label">${label}</span>
        <span class="breakdown__val">${fmt(value)}</span>
      </div>
      <div class="breakdown__bar">
        <div class="breakdown__fill" data-pct="${pct}"
             style="width:0%;background:${color}"></div>
      </div>
    </div>`;
}

// ── Gauge chart (Chart.js doughnut) ──────────────────────────────────────────
function _drawGauge(pred, low, high) {
  const canvas = document.getElementById('gaugeChart');
  if (!canvas) return;
  if (gaugeChart) { gaugeChart.destroy(); gaugeChart = null; }

  const max    = 300000;
  const filled = Math.min(pred, max);
  const empty  = max - filled;

  // Color based on range
  let color = '#22c55e';
  if (pred > 100000) color = '#f97316';
  if (pred > 200000) color = '#f85149';

  gaugeChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [filled, empty],
        backgroundColor: [color, '#21262d'],
        borderWidth: 0,
        borderRadius: 4,
        circumference: 180,
        rotation: 270,
      }],
    },
    options: {
      responsive: true,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false },
      },
      animation: { animateRotate: true, duration: 1000 },
    },
    plugins: [{
      id: 'gaugeCenter',
      afterDraw(chart) {
        const { ctx, chartArea: { left, right, top, bottom } } = chart;
        const cx = (left + right) / 2;
        const cy = bottom - 10;
        ctx.save();
        ctx.fillStyle = '#8b949e';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('₹0', left + 16, cy + 2);
        ctx.fillText('₹3L', right - 16, cy + 2);
        ctx.restore();
      },
    }],
  });
}

// ── Comparable trips ──────────────────────────────────────────────────────────
function _renderComparableTrips(trips) {
  const el = document.getElementById('comparable-section');
  if (!el || !trips.length) return;

  const rows = trips.slice(0, 5).map(t => `
    <tr>
      <td>${t.destination}</td>
      <td>${t.travelers}</td>
      <td>${t.trip_days}d</td>
      <td style="color:var(--clr-accent);font-family:var(--font-mono)">${fmt(t.actual_trip_expense)}</td>
    </tr>`).join('');

  el.innerHTML = `
    <div style="margin:20px 0 10px;font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--clr-text-muted);">
      Similar Trips from Dataset
    </div>
    <table class="mini-table">
      <thead><tr><th>Destination</th><th>Travelers</th><th>Duration</th><th>Actual</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function _showResultEmpty() {
  const panel = document.getElementById('result-body');
  if (panel) panel.innerHTML = `
    <div class="result-empty">
      <div class="result-empty__icon">⚠️</div>
      <div>Prediction failed. Check the backend is running.</div>
    </div>`;
}
