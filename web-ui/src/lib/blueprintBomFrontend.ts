const DEV_WEB_UI_PORTS = new Set(['5173', '5174']);
const DEV_BOM_FRONTEND_PORT = '5021';
const DOCKER_BOM_FRONTEND_PORT = '3000';
const BOM_BASE_PATH = '/bom';

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '');
}

function configuredBomUrl(): string | null {
  const raw = import.meta.env.VITE_BLUEPRINT_AI_BOM_FRONTEND_URL?.trim();
  if (!raw) {
    return null;
  }
  return stripTrailingSlash(raw);
}

export function resolveBlueprintBomFrontendUrl(location: Location): string {
  const configured = configuredBomUrl();
  if (configured) {
    return configured;
  }

  const target = new URL(location.origin);
  target.port = DEV_WEB_UI_PORTS.has(target.port)
    ? DEV_BOM_FRONTEND_PORT
    : DOCKER_BOM_FRONTEND_PORT;
  target.pathname = BOM_BASE_PATH;
  target.search = '';
  target.hash = '';

  return stripTrailingSlash(target.toString());
}

function normalizeBomPath(pathname: string): string {
  const suffix = pathname.startsWith(BOM_BASE_PATH)
    ? pathname.slice(BOM_BASE_PATH.length)
    : pathname;

  if (!suffix) {
    return '';
  }
  return suffix.startsWith('/') ? suffix : `/${suffix}`;
}

export function buildBlueprintBomTargetUrl(location: Location): string {
  const baseUrl = resolveBlueprintBomFrontendUrl(location);
  return `${baseUrl}${normalizeBomPath(location.pathname)}${location.search}`;
}
