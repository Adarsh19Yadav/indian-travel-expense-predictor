/**
 * api.js — Centralised API client for the FastAPI backend.
 *
 * API_BASE is empty so all requests go to the same origin.
 * - Local dev:   FastAPI runs on http://localhost:8000 — open the app at
 *                http://localhost:8000 (NOT the old separate serve.py port).
 * - Production:  FastAPI serves everything on the Render PORT, same origin.
 */

const API_BASE = '';

const Api = (() => {

  async function _request(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${path}`, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  // ── Prediction ──────────────────────────────────────────────
  function predict(tripInput) {
    return _request('POST', '/predict', tripInput);
  }

  function comparableTrips(tripInput) {
    return _request('POST', '/analytics/comparable-trips', tripInput);
  }

  // ── Analytics ───────────────────────────────────────────────
  function getSummary()           { return _request('GET', '/analytics/summary'); }
  function getByDestination()     { return _request('GET', '/analytics/by-destination'); }
  function getBySeason()          { return _request('GET', '/analytics/by-season'); }
  function getByTransport()       { return _request('GET', '/analytics/by-transport'); }
  function getByAccommodation()   { return _request('GET', '/analytics/by-accommodation'); }
  function getByTravelers()       { return _request('GET', '/analytics/by-travelers'); }
  function getByTripDays()        { return _request('GET', '/analytics/by-trip-days'); }
  function getExpenseDistribution() { return _request('GET', '/analytics/expense-distribution'); }

  // ── Model ────────────────────────────────────────────────────
  function getModelMetrics()       { return _request('GET', '/model/metrics'); }
  function getFeatureImportances() { return _request('GET', '/model/feature-importances'); }
  function healthCheck()           { return _request('GET', '/api/health'); }

  return {
    predict,
    comparableTrips,
    getSummary,
    getByDestination,
    getBySeason,
    getByTransport,
    getByAccommodation,
    getByTravelers,
    getByTripDays,
    getExpenseDistribution,
    getModelMetrics,
    getFeatureImportances,
    healthCheck,
  };
})();
