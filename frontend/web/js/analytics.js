/**
 * analytics.js — All Chart.js charts for the Analytics page.
 * Uses tabs: Destinations | Season | Transport | Accommodation | Distributions
 */

let analyticsInitDone = false;
const analyticsCharts = {};

// Shared Chart.js defaults
const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: '#8b949e', font: { size: 12 } },
    },
    tooltip: {
      backgroundColor: '#1c2333',
      titleColor: '#e6edf3',
      bodyColor: '#8b949e',
      borderColor: '#30363d',
      borderWidth: 1,
      callbacks: {
        label: ctx => ' ₹' + Math.round(ctx.parsed.y ?? ctx.parsed).toLocaleString('en-IN'),
      },
    },
  },
  scales: {
    x: {
      ticks: { color: '#8b949e', font: { size: 11 } },
      grid:  { color: 'rgba(48,54,61,.5)' },
    },
    y: {
      ticks: {
        color: '#8b949e', font: { size: 11 },
        callback: v => '₹' + (v >= 1000 ? (v/1000).toFixed(0)+'k' : v),
      },
      grid: { color: 'rgba(48,54,61,.5)' },
    },
  },
};

function makeBarDefaults() {
  return JSON.parse(JSON.stringify(CHART_DEFAULTS));
}

function initAnalytics() {
  if (analyticsInitDone) return;
  analyticsInitDone = true;

  _wireAnalyticsTabs();
  _loadDestinations();
  _loadSeason();
  _loadTransport();
  _loadAccommodation();
  _loadDistributions();
}

// ── Tab wiring ────────────────────────────────────────────────────────────────
function _wireAnalyticsTabs() {
  document.querySelectorAll('#page-analytics .tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#page-analytics .tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('#page-analytics .tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab)?.classList.add('active');
      // Trigger chart resize so they fill container correctly
      Object.values(analyticsCharts).forEach(c => c?.resize?.());
    });
  });
}

// ── Destinations ──────────────────────────────────────────────────────────────
async function _loadDestinations() {
  try {
    const data = await Api.getByDestination();
    const top20 = data.slice(0, 20);

    // Horizontal bar — top 20 by avg expense
    const ctx = document.getElementById('chart-dest-bar')?.getContext('2d');
    if (ctx) {
      const typeColors = {
        Heritage:'#f97316', Beach:'#0ea5e9', Mountain:'#22c55e',
        City:'#a855f7', Religious:'#fb923c', Nature:'#34d399',
        Wildlife:'#f59e0b', Adventure:'#ef4444',
      };
      analyticsCharts.destBar = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: top20.map(d => d.destination),
          datasets: [{
            label: 'Avg Expense',
            data: top20.map(d => d.avg_expense),
            backgroundColor: top20.map(d => typeColors[d.destination_type] || '#8b949e'),
            borderRadius: 4,
          }],
        },
        options: {
          ...makeBarDefaults(),
          indexAxis: 'y',
          plugins: {
            ...CHART_DEFAULTS.plugins,
            legend: { display: false },
            tooltip: {
              ...CHART_DEFAULTS.plugins.tooltip,
              callbacks: {
                label: ctx => ` ₹${Math.round(ctx.parsed.x).toLocaleString('en-IN')} · ${data[ctx.dataIndex]?.destination_type}`,
              },
            },
          },
          scales: {
            x: { ...CHART_DEFAULTS.scales.x },
            y: { ticks: { color: '#8b949e', font: { size: 11 } }, grid: { color: 'rgba(48,54,61,.3)' } },
          },
        },
      });
    }

    // Donut — by destination type
    const typeMap = {};
    data.forEach(d => {
      typeMap[d.destination_type] = (typeMap[d.destination_type] || 0) + d.avg_expense;
    });
    const typeCtx = document.getElementById('chart-dest-type')?.getContext('2d');
    if (typeCtx) {
      const labels = Object.keys(typeMap);
      analyticsCharts.destType = new Chart(typeCtx, {
        type: 'doughnut',
        data: {
          labels,
          datasets: [{
            data: labels.map(l => Math.round(typeMap[l])),
            backgroundColor: ['#f97316','#0ea5e9','#22c55e','#a855f7','#fb923c','#34d399','#f59e0b','#ef4444'],
            borderColor: '#161b22',
            borderWidth: 2,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#8b949e', font: { size: 11 } }, position: 'right' },
            tooltip: {
              backgroundColor: '#1c2333', titleColor: '#e6edf3', bodyColor: '#8b949e',
              borderColor: '#30363d', borderWidth: 1,
              callbacks: { label: ctx => ` ₹${Math.round(ctx.parsed).toLocaleString('en-IN')}` },
            },
          },
        },
      });
    }
  } catch(e) { console.error('Destinations chart error', e); }
}

// ── Season ────────────────────────────────────────────────────────────────────
async function _loadSeason() {
  try {
    const data = await Api.getBySeason();
    const seasonColors = { 'Off-Peak': '#93c5fd', Shoulder: '#fcd34d', Peak: '#f87171' };

    const ctx1 = document.getElementById('chart-season-bar')?.getContext('2d');
    if (ctx1) {
      analyticsCharts.seasonBar = new Chart(ctx1, {
        type: 'bar',
        data: {
          labels: data.map(d => d.season),
          datasets: [{
            label: 'Avg Expense',
            data: data.map(d => d.avg_expense),
            backgroundColor: data.map(d => seasonColors[d.season] || '#8b949e'),
            borderRadius: 6,
          }],
        },
        options: { ...makeBarDefaults(), plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } } },
      });
    }

    const ctx2 = document.getElementById('chart-season-pie')?.getContext('2d');
    if (ctx2) {
      analyticsCharts.seasonPie = new Chart(ctx2, {
        type: 'pie',
        data: {
          labels: data.map(d => d.season),
          datasets: [{
            data: data.map(d => d.trip_count),
            backgroundColor: data.map(d => seasonColors[d.season] || '#8b949e'),
            borderColor: '#161b22', borderWidth: 2,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#8b949e' }, position: 'bottom' },
            tooltip: {
              backgroundColor: '#1c2333', titleColor: '#e6edf3', bodyColor: '#8b949e',
              borderColor: '#30363d', borderWidth: 1,
              callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} trips` },
            },
          },
        },
      });
    }
  } catch(e) { console.error('Season chart error', e); }
}

// ── Transport ─────────────────────────────────────────────────────────────────
async function _loadTransport() {
  try {
    const data = await Api.getByTransport();
    const trColors = { Flight: '#f97316', Car: '#0ea5e9', Train: '#22c55e', Bus: '#a855f7' };

    const ctx1 = document.getElementById('chart-transport-bar')?.getContext('2d');
    if (ctx1) {
      analyticsCharts.transportBar = new Chart(ctx1, {
        type: 'bar',
        data: {
          labels: data.map(d => d.transport_mode),
          datasets: [{
            label: 'Avg Expense',
            data: data.map(d => d.avg_expense),
            backgroundColor: data.map(d => trColors[d.transport_mode] || '#8b949e'),
            borderRadius: 6,
          }],
        },
        options: { ...makeBarDefaults(), plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } } },
      });
    }

    const ctx2 = document.getElementById('chart-transport-pie')?.getContext('2d');
    if (ctx2) {
      analyticsCharts.transportPie = new Chart(ctx2, {
        type: 'doughnut',
        data: {
          labels: data.map(d => d.transport_mode),
          datasets: [{
            data: data.map(d => d.trip_count),
            backgroundColor: data.map(d => trColors[d.transport_mode] || '#8b949e'),
            borderColor: '#161b22', borderWidth: 2,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#8b949e' }, position: 'bottom' },
            tooltip: {
              backgroundColor: '#1c2333', titleColor: '#e6edf3', bodyColor: '#8b949e',
              borderColor: '#30363d', borderWidth: 1,
              callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} trips` },
            },
          },
        },
      });
    }
  } catch(e) { console.error('Transport chart error', e); }
}

// ── Accommodation ─────────────────────────────────────────────────────────────
async function _loadAccommodation() {
  try {
    const data = await Api.getByAccommodation();
    const gradient = ['#93c5fd','#60a5fa','#3b82f6','#2563eb','#1d4ed8'];

    const ctx1 = document.getElementById('chart-acc-bar')?.getContext('2d');
    if (ctx1) {
      analyticsCharts.accBar = new Chart(ctx1, {
        type: 'bar',
        data: {
          labels: data.map(d => d.accommodation_type),
          datasets: [{
            label: 'Avg Expense',
            data: data.map(d => d.avg_expense),
            backgroundColor: gradient,
            borderRadius: 6,
          }],
        },
        options: { ...makeBarDefaults(), plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } } },
      });
    }

    const ctx2 = document.getElementById('chart-acc-line')?.getContext('2d');
    if (ctx2) {
      analyticsCharts.accLine = new Chart(ctx2, {
        type: 'line',
        data: {
          labels: data.map(d => d.accommodation_type),
          datasets: [{
            label: 'Avg Expense',
            data: data.map(d => d.avg_expense),
            borderColor: '#f97316',
            backgroundColor: 'rgba(249,115,22,.08)',
            pointBackgroundColor: '#f97316',
            pointRadius: 6,
            tension: 0.35,
            fill: true,
          }],
        },
        options: { ...makeBarDefaults() },
      });
    }
  } catch(e) { console.error('Accommodation chart error', e); }
}

// ── Distributions ─────────────────────────────────────────────────────────────
async function _loadDistributions() {
  try {
    const [distData, travData, daysData] = await Promise.all([
      Api.getExpenseDistribution(),
      Api.getByTravelers(),
      Api.getByTripDays(),
    ]);

    // Histogram
    const ctx1 = document.getElementById('chart-histogram')?.getContext('2d');
    if (ctx1) {
      analyticsCharts.histogram = new Chart(ctx1, {
        type: 'bar',
        data: {
          labels: distData.labels,
          datasets: [{
            label: 'Trips',
            data: distData.counts,
            backgroundColor: 'rgba(14,165,233,.7)',
            borderColor: '#0ea5e9',
            borderWidth: 1,
            borderRadius: 2,
          }],
        },
        options: {
          ...makeBarDefaults(),
          plugins: {
            ...CHART_DEFAULTS.plugins,
            legend: { display: false },
            tooltip: {
              ...CHART_DEFAULTS.plugins.tooltip,
              callbacks: { label: ctx => ` ${ctx.parsed.y} trips` },
            },
          },
          scales: {
            x: { ticks: { color: '#8b949e', font: { size: 10 }, maxRotation: 45 }, grid: { color: 'rgba(48,54,61,.4)' } },
            y: { ticks: { color: '#8b949e', font: { size: 11 } }, grid: { color: 'rgba(48,54,61,.4)' }, title: { display: true, text: 'Number of Trips', color: '#8b949e' } },
          },
        },
      });
    }

    // Travelers line
    const ctx2 = document.getElementById('chart-travelers')?.getContext('2d');
    if (ctx2) {
      analyticsCharts.travelers = new Chart(ctx2, {
        type: 'line',
        data: {
          labels: travData.map(d => d.travelers),
          datasets: [{
            label: 'Avg Expense',
            data: travData.map(d => d.avg_expense),
            borderColor: '#a855f7',
            backgroundColor: 'rgba(168,85,247,.08)',
            pointBackgroundColor: '#a855f7',
            pointRadius: 5,
            tension: 0.35,
            fill: true,
          }],
        },
        options: {
          ...makeBarDefaults(),
          scales: {
            x: { ...CHART_DEFAULTS.scales.x, title: { display: true, text: 'Travelers', color: '#8b949e' } },
            y: { ...CHART_DEFAULTS.scales.y },
          },
        },
      });
    }

    // Trip days area
    const ctx3 = document.getElementById('chart-trip-days')?.getContext('2d');
    if (ctx3) {
      analyticsCharts.tripDays = new Chart(ctx3, {
        type: 'line',
        data: {
          labels: daysData.map(d => d.trip_days),
          datasets: [{
            label: 'Avg Expense',
            data: daysData.map(d => d.avg_expense),
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34,197,94,.08)',
            pointBackgroundColor: '#22c55e',
            pointRadius: 4,
            tension: 0.35,
            fill: true,
          }],
        },
        options: {
          ...makeBarDefaults(),
          scales: {
            x: { ...CHART_DEFAULTS.scales.x, title: { display: true, text: 'Trip Days', color: '#8b949e' } },
            y: { ...CHART_DEFAULTS.scales.y },
          },
        },
      });
    }
  } catch(e) { console.error('Distribution chart error', e); }
}
