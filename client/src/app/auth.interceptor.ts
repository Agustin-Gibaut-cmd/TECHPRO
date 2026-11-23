import {
  HttpContextToken,
  HttpErrorResponse,
  HttpInterceptorFn,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { environment } from '../environments/environment';
import { AuthService } from './auth.service';

const AUTH_RETRIED = new HttpContextToken<boolean>(() => false);

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const isApiRequest = isApiRequestUrl(request.url);
  const isAuthEndpoint = isAuthenticationEndpoint(request.url);

  const cookieRequest = isApiRequest
    ? request.clone({ withCredentials: true })
    : request;

  return next(cookieRequest).pipe(
    catchError((error: unknown) => {
      if (
        !(error instanceof HttpErrorResponse) ||
        error.status !== 401 ||
        !isApiRequest ||
        isAuthEndpoint ||
        request.context.get(AUTH_RETRIED)
      ) {
        return throwError(() => error);
      }

      return authService.refreshAccessToken().pipe(
        switchMap(() =>
          next(cookieRequest.clone({ context: request.context.set(AUTH_RETRIED, true) }))
        ),
        catchError((refreshError: unknown) => {
          authService.clearSession();
          void router.navigate(['/login']);
          return throwError(() => refreshError);
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
