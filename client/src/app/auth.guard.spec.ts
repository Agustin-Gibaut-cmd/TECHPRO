import { HttpErrorResponse } from '@angular/common/http';
import { PLATFORM_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  CanActivateFn,
  Router,
  RouterStateSnapshot,
  UrlTree,
  provideRouter,
} from '@angular/router';
import { Observable, firstValueFrom, throwError } from 'rxjs';
import { AuthService } from './auth.service';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  function configureGuard(platformId: string, authenticated = false): {
    router: Router;
    isSessionCleared: () => boolean;
    wasCurrentUserLoaded: () => boolean;
  } {
    let clearedSession = false;
    let loadedCurrentUser = false;

    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: PLATFORM_ID, useValue: platformId },
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => authenticated,
            loadCurrentUser: () => {
              loadedCurrentUser = true;
              return throwError(() => new HttpErrorResponse({ status: 401 }));
            },
            clearSession: () => {
              clearedSession = true;
            },
          },
        },
      ],
    });

    return {
      router: TestBed.inject(Router),
      isSessionCleared: () => clearedSession,
      wasCurrentUserLoaded: () => loadedCurrentUser,
    };
  }

  async function evaluateGuard(guard: CanActivateFn): Promise<unknown> {
    const result = TestBed.runInInjectionContext(() =>
      guard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot)
    );
    return result instanceof Observable ? firstValueFrom(result) : result;
  }

  it('redirects unauthenticated users and clears stale session state', async () => {
    const { router, isSessionCleared } = configureGuard('browser');

    const result = await evaluateGuard(authGuard);

    expect(result instanceof UrlTree).toBe(true);
    expect(router.serializeUrl(result as UrlTree)).toBe('/login');
    expect(isSessionCleared()).toBe(true);
  });

  it('blocks protected routes during server rendering without checking browser cookies', async () => {
    const { router, wasCurrentUserLoaded } = configureGuard('server');

    const result = await evaluateGuard(authGuard);

    expect(result instanceof UrlTree).toBe(true);
    expect(router.serializeUrl(result as UrlTree)).toBe('/login');
    expect(wasCurrentUserLoaded()).toBe(false);
  });

  it('allows a session already restored in memory', async () => {
    configureGuard('browser', true);

    expect(await evaluateGuard(authGuard)).toBe(true);
  });
});
