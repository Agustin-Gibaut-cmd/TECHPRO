import { HttpErrorResponse } from '@angular/common/http';

/**
 * Extrae un mensaje de error legible a partir de una excepción de red o de DRF.
 *
 * @param error Error capturado en el pipeline de RxJS o llamada HTTP.
 * @param defaultMessage Mensaje de fallback si no se puede determinar la causa.
 * @returns Texto descriptivo del error en español.
 */
export function extractErrorMessage(
  error: unknown,
  defaultMessage = 'No se pudo completar la operación.'
): string {
  if (!(error instanceof HttpErrorResponse)) {
    return defaultMessage;
  }

  if (error.status === 0) {
    return 'No se pudo conectar con el servidor. Verificá que el backend esté iniciado.';
  }

  if (error.status === 401) {
    return 'Tu sesión expiró o las credenciales son incorrectas.';
  }

  if (typeof error.error === 'object' && error.error !== null) {
    for (const value of Object.values(error.error as Record<string, unknown>)) {
      if (typeof value === 'string') {
        return value;
      }
      if (Array.isArray(value)) {
        const firstMessage = value.find((item: unknown): item is string => typeof item === 'string');
        if (firstMessage) {
          return firstMessage;
        }
      }
    }
  }

  return defaultMessage;
}
