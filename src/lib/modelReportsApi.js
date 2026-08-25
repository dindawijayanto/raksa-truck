const apiBase = import.meta.env.VITE_MODEL_API_BASE || '/api/v1';

async function getJson(path) {
  const response = await fetch(`${apiBase}${path}`);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || 'Data model tidak dapat dimuat.');
  }
  return body;
}

export function getDashboardOverview() {
  return getJson('/dashboard/overview');
}

export function getModelASessions() {
  return getJson('/model-a/sessions');
}

export function getModelASegments(sessionId) {
  return getJson(`/model-a/sessions/${encodeURIComponent(sessionId)}/segments`);
}
