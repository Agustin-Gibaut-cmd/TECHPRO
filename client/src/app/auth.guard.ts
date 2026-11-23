import { isPlatformBrowser } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { inject, PLATFORM_ID } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { AuthService } from './auth.service';

/**
 * Guardia de enrutamiento que protege rutas privadas asegurando que exista una sesión activa.
 */
export const authGuard: CanActivateFn = ():
  | boolean
  | UrlTree
  | Observable<boolean | UrlTree> => {
  const authService = inject(AuthService);
  const platformId = inject(PLATFORM_ID);
  const router = inject(Router);

  if (!isPlatformBrowser(platformId)) {
    return router.createUrlTree(['/login']);
  }

  if (authService.isAuthenticated()) {
    return true;
  }

  return authService.loadCurrentUser().pipe(
    map(() => true),
    catchError((err: unknown) => {
      if (err instanceof HttpErrorResponse && err.status === 401) {
        authService.clearSession();
        return of(router.createUrlTree(['/login']));
      }
      return throwError(() => err);
    })
  );
};
