const DEFAULT_API_BASE_URL = 'http://localhost:8001';

export function getApiBaseUrl(): string {
  const configuredUrl = window.localStorage.getItem('API_BASE_URL')?.trim();
  return configuredUrl || DEFAULT_API_BASE_URL;
}
