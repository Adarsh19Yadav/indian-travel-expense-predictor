/**
 * app.js — SPA router, navigation, toast system, and page init dispatcher.
 */

// ── Toast system ──────────────────────────────────────────────────────────────
const Toast = (() => {
  const container = document.getElementById('toast-container');

  function show(type, title, msg, duration = 4500) {
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    el.innerHTML = `
      <span class="toast__icon">${icons[type] || icons.info}</span>
      <div class="toast__body">
        <div class="toast__title">${title}</div>
        ${msg ? `<div class="toast__msg">${msg}</div>` : ''}
      </div>
      <button class="toast__close" onclick="this.closest('.toast').remove()">✕</button>`;
    container.appendChild(el);
    setTimeout(() => el.remove(), duration);
  }

  return { show };
})();

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(n) {
  return '₹' + Math.round(n).toLocaleString('en-IN');
}

function fmtCompact(n) {
  if (n >= 1e5) return '₹' + (n / 1e5).toFixed(2) + 'L';
  if (n >= 1e3) return '₹' + (n / 1e3).toFixed(1) + 'k';
  return '₹' + Math.round(n);
}

// ── SPA Router ────────────────────────────────────────────────────────────────
const Router = (() => {
  const pages = {};
  let current = null;

  function register(id, initFn) { pages[id] = initFn; }

  function navigate(id, updateHistory = true) {
    // Hide all sections
    document.querySelectorAll('.page-section').forEach(s => {
      s.style.display = 'none';
    });
    // Show target
    const section = document.getElementById(`page-${id}`);
    if (!section) return;
    section.style.display = 'block';

    // Animate
    section.classList.remove('animate-fade-up');
    void section.offsetWidth;
    section.classList.add('animate-fade-up');

    // Nav links
    document.querySelectorAll('.navbar__links a').forEach(a => {
      a.classList.toggle('active', a.dataset.page === id);
    });

    if (updateHistory) {
      history.pushState({ page: id }, '', `#${id}`);
    }

    // Init page logic once
    if (current !== id && pages[id]) {
      pages[id]();
    }
    current = id;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function init() {
    // Handle nav link clicks
    document.querySelectorAll('[data-page]').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        navigate(el.dataset.page);
        // Close mobile nav
        document.querySelector('.navbar__links')?.classList.remove('open');
      });
    });

    // Handle browser back/forward
    window.addEventListener('popstate', e => {
      if (e.state?.page) navigate(e.state.page, false);
    });

    // Mobile nav toggle
    document.querySelector('.navbar__mobile-toggle')?.addEventListener('click', () => {
      document.querySelector('.navbar__links')?.classList.toggle('open');
    });

    // Initial route from hash or default to home
    const hash = location.hash.replace('#', '') || 'home';
    navigate(hash, false);
  }

  return { register, navigate, init };
})();

// ── Counter animation ─────────────────────────────────────────────────────────
function animateCounter(el, target, duration = 1200, prefix = '₹', suffix = '') {
  const start = performance.now();
  const startVal = 0;
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3); // ease-out-cubic
    const val = startVal + eased * (target - startVal);
    el.textContent = prefix + Math.round(val).toLocaleString('en-IN') + suffix;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── Home page init ─────────────────────────────────────────────────────────────
function initHome() {
  // Animate KPI counters after a short delay
  Api.getSummary().then(data => {
    const kpis = [
      { id: 'kpi-records',  val: data.total_records,  prefix: '',  suffix: '' },
      { id: 'kpi-avg',      val: data.avg_expense,     prefix: '₹', suffix: '' },
      { id: 'kpi-median',   val: data.median_expense,  prefix: '₹', suffix: '' },
      { id: 'kpi-dest',     val: data.destinations,    prefix: '',  suffix: '' },
    ];
    kpis.forEach(k => {
      const el = document.getElementById(k.id);
      if (el) animateCounter(el, k.val, 1400, k.prefix, k.suffix);
    });
  }).catch(() => {}); // non-critical
}

// ── Backend health check ──────────────────────────────────────────────────────
async function checkBackend() {
  try {
    const h = await Api.healthCheck();
    const dot = document.getElementById('backend-status-dot');
    const lbl = document.getElementById('backend-status-label');
    if (dot) { dot.style.background = '#22c55e'; dot.style.boxShadow = '0 0 6px #22c55e'; }
    if (lbl) lbl.textContent = `API online · ${h.model}`;
  } catch {
    const dot = document.getElementById('backend-status-dot');
    const lbl = document.getElementById('backend-status-label');
    if (dot) { dot.style.background = '#f85149'; dot.style.boxShadow = 'none'; }
    if (lbl) lbl.textContent = 'API offline — start the backend';
    Toast.show('error', 'Backend offline',
      'Run: uvicorn backend.main:app --reload --port 8000', 8000);
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Register pages
  Router.register('home',      initHome);
  Router.register('predict',   initPredict);
  Router.register('analytics', initAnalytics);
  Router.register('insights',  initInsights);

  Router.init();
  checkBackend();
});
