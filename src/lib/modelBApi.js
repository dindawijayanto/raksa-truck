const endpoint = import.meta.env.VITE_MODEL_API_URL || '/api/v1/model-b/predict';

export class ModelBApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ModelBApiError';
    this.status = status;
  }
}

export async function predictModelBScenario(payload) {
  let response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ModelBApiError('Tidak dapat terhubung ke API Model B.', 0);
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).join(', ')
      : body.detail;
    throw new ModelBApiError(detail || 'Model API tidak dapat memproses skenario ini.', response.status);
  }
  return body;
}
