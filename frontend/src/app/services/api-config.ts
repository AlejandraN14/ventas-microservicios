const DEFAULT_API_BASE_URL = 'http://ventas-alb-333663717.us-east-1.elb.amazonaws.com:8001';

export function getApiBaseUrl(): string {
  const configuredUrl = window.localStorage.getItem('API_BASE_URL')?.trim();
  return configuredUrl || DEFAULT_API_BASE_URL;
}







