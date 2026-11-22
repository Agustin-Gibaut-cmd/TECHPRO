declare const __PUBLIC_API_URL__: string | undefined;

export const environment = Object.freeze({
  production: false,
  apiUrl:
    typeof __PUBLIC_API_URL__ === 'undefined'
      ? 'http://localhost:8000/api'
      : __PUBLIC_API_URL__.replace(/\/+$/, ''),
});
