import {
  HttpContextToken,
  HttpErrorResponse,
  HttpEvent,
  HttpHandlerFn,
  HttpInterceptorFn,
  HttpRequest,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, Observable, switchMap, throwError } from 'rxjs';
import { environment } from '../environments/environment';
import { AuthService } from './auth.service';

const AUTH_RETRIED = new HttpContextToken<boolean>(() => false);

/**
 * Interceptor HTTP que adjunta credenciales y renueva tokens expirados ante errores 401.
 */
export const authInterceptor: HttpInterceptorFn = (
  request: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const isApi = isApiRequestUrl(request.url);
  const isAuth = isAuthenticationEndpoint(request.url);

  const cookieRequest = isApi
    ? request.clone({ withCredentials: true })
    : request;

  return next(cookieRequest).pipe(
    catchError((err: unknown) => {
      if (
        !(err instanceof HttpErrorResponse) ||
        err.status !== 401 ||
        !isApi ||
        isAuth ||
        request.context.get(AUTH_RETRIED)
      ) {
        return throwError(() => err);
      }

      return authService.refreshAccessToken().pipe(
        switchMap(() =>
          next(cookieRequest.clone({ context: request.context.set(AUTH_RETRIED, true) }))
        ),
        catchError((refreshErr: unknown) => {
          authService.clearSession();
          void router.navigate(['/login']);
          return throwError(() => refreshErr);
        })
      );
    })
  );
};

function isApiRequestUrl(url: string): boolean {
  return url === environment.apiUrl || url.startsWith(`${environment.apiUrl}/`);
}

function isAuthenticationEndpoint(url: string): boolean {
  return /\/auth\/(csrf|login|register|logout|token\/refresh)\/?$/.test(url);
}
