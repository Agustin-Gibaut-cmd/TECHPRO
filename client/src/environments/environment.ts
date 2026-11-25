declare const __PUBLIC_API_URL__: string | undefined;

export interface Environment {
  readonly production: boolean;
  readonly apiUrl: string;
}

const DEFAULT_API_URL: string = 'http://localhost:8000/api';
const TRAILING_SLASHES_REGEX: RegExp = /\/+$/;

function normalizeApiUrl(rawUrl: string): string {
  const trimmedUrl: string = rawUrl.trim();
  const withoutTrailingSlashes: string = trimmedUrl.replace(TRAILING_SLASHES_REGEX, '');
  return withoutTrailingSlashes;
}

function resolveApiUrl(fallbackUrl: string): string {
  const injectedUrl: string | undefined =
    typeof __PUBLIC_API_URL__ === 'undefined' ? undefined : __PUBLIC_API_URL__;

  if (injectedUrl === undefined) {
    return fallbackUrl;
  }

  const normalizedUrl: string = normalizeApiUrl(injectedUrl);
  const hasValue: boolean = normalizedUrl.length > 0;

  return hasValue ? normalizedUrl : fallbackUrl;
}

const initialEnvironment: Environment = {
  production: false,
  apiUrl: resolveApiUrl(DEFAULT_API_URL),
};

export const environment: Readonly<Environment> = Object.freeze(initialEnvironment);