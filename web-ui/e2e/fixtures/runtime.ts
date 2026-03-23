function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '');
}

function joinUrl(base: string, path: string): string {
  return `${trimTrailingSlash(base)}${path.startsWith('/') ? path : `/${path}`}`;
}

export const WEB_UI_BASE_URL = trimTrailingSlash(
  process.env.WEB_UI_BASE_URL || 'http://localhost:5174'
);
export const BOM_UI_ORIGIN = trimTrailingSlash(
  process.env.BOM_UI_ORIGIN || 'http://localhost:5021'
);
export const BOM_UI_BASE_PATH = process.env.BOM_UI_BASE_PATH || '/bom';
export const BOM_UI_BASE_URL = joinUrl(BOM_UI_ORIGIN, BOM_UI_BASE_PATH);
export const BOM_WORKFLOW_URL = joinUrl(BOM_UI_BASE_URL, '/workflow');
export const BOM_API_BASE_URL = trimTrailingSlash(
  process.env.BOM_API_BASE_URL || 'http://localhost:5020'
);
