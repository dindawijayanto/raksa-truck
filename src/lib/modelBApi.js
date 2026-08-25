const endpoint = import.meta.env.VITE_MODEL_API_URL || '/api/v1/model-b/predict';

export async function predictModelBScenario(payload) {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).join(', ')
      : body.detail;
    throw new Error(detail || 'Model API tidak dapat memproses skenario ini.');
  }
  return body;
}
