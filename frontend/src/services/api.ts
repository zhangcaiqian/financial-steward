const API_BASE = "/api";
const ERROR_EVENT = "app:api-error";

function emitApiError(message: string) {
  if (typeof window === "undefined") return;
  if (!message) return;
  window.dispatchEvent(new CustomEvent(ERROR_EVENT, { detail: { message } }));
}

function extractMessage(text: string, status: number) {
  const trimmed = text.trim();
  if (!trimmed) return `请求失败(${status})`;
  try {
    const data = JSON.parse(trimmed);
    if (typeof data === "string") return data;
    if (data && typeof data === "object") {
      if ("detail" in data && data.detail) return String(data.detail);
      if ("message" in data && data.message) return String(data.message);
    }
  } catch {
    // ignore parse error
  }
  return trimmed.length > 160 ? `${trimmed.slice(0, 160)}...` : trimmed;
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  let emitted = false;
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!response.ok) {
      const text = await response.text();
      const message = extractMessage(text, response.status);
      emitApiError(message);
      emitted = true;
      throw new Error(`API error ${response.status}: ${text}`);
    }

    return response.json();
  } catch (error) {
    if (!emitted) {
      const raw = error instanceof Error ? error.message : "请求失败";
      const message = raw.includes("Failed to fetch") ? "网络异常，请稍后重试" : raw;
      emitApiError(message);
    }
    throw error;
  }
}
