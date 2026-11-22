declare const __PUBLIC_API_URL__: string | undefined;

export const environment = Object.freeze({
  production: true,
  apiUrl:
    typeof __PUBLIC_API_URL__ === 'undefined'
      ? '/api'
      : __PUBLIC_API_URL__.replace(/\/+$/, ''),
});
