import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { PLATFORM_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { AuthResponse, AuthService, AuthUser } from './auth.service';
import { environment } from '../environments/environment';

describe('AuthService', () => {
  let authService: AuthService;
  let httpMock: HttpTestingController;

  const credentials = { email: 'ana@example.com', password: 'StrongPass!2026' };
  const user: AuthUser = { name: 'Ana Pérez', email: credentials.email };
  const authResponse: AuthResponse = { user };

  function configureAuthService(): void {
    TestBed.configureTestingModule({
      providers: [
        { provide: PLATFORM_ID, useValue: 'browser' },
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    authService = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  }

  function flushCsrfToken(): void {
    const request = httpMock.expectOne(`${environment.apiUrl}/auth/csrf/`);
    expect(request.request.method).toBe('GET');
    expect(request.request.withCredentials).toBe(true);
    request.flush({ csrfToken: 'csrf-token' });
  }

  beforeEach(() => {
    configureAuthService();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('sends login with CSRF and credentials, keeping JWT out of the response body', () => {
    let response: AuthResponse | undefined;

    authService.login(credentials.email, credentials.password).subscribe((value) => {
      response = value;
    });

    flushCsrfToken();
    const request = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(credentials);
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    request.flush(authResponse);

    expect(response).toEqual(authResponse);
    expect(authService.currentUser()).toEqual(user);
    expect(authService.isAuthenticated()).toBe(true);
  });

  it('registers with CSRF and credentials', () => {
    let response: AuthResponse | undefined;

    authService.register('Ana Pérez', credentials.email, credentials.password).subscribe((value) => {
      response = value;
    });

    flushCsrfToken();
    const request = httpMock.expectOne(`${environment.apiUrl}/auth/register/`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ name: 'Ana Pérez', ...credentials });
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    request.flush(authResponse);

    expect(response?.user.email).toBe(credentials.email);
    expect(authService.isAuthenticated()).toBe(true);
  });

  it('refreshes the HttpOnly cookie session without exposing JWT values', () => {
    let completed = false;

    authService.refreshAccessToken().subscribe(() => {
      completed = true;
    });

    flushCsrfToken();
    const request = httpMock.expectOne(`${environment.apiUrl}/auth/token/refresh/`);
    expect(request.request.body).toEqual({});
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    request.flush(null, { status: 204, statusText: 'No Content' });

    expect(completed).toBe(true);
  });

  it('restores the user from the authenticated server endpoint', () => {
    authService.loadCurrentUser().subscribe();

    const request = httpMock.expectOne(`${environment.apiUrl}/auth/me/`);
    expect(request.request.withCredentials).toBe(true);
    request.flush(user);

    expect(authService.currentUser()).toEqual(user);
    expect(authService.isAuthenticated()).toBe(true);
  });

  it('revokes the server session and clears in-memory user state on logout', () => {
    authService.loadCurrentUser().subscribe();
    httpMock.expectOne(`${environment.apiUrl}/auth/me/`).flush(user);

    authService.logout();
    expect(authService.isAuthenticated()).toBe(false);
    flushCsrfToken();

    const request = httpMock.expectOne(`${environment.apiUrl}/auth/logout/`);
    expect(request.request.body).toEqual({});
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    request.flush(null, { status: 204, statusText: 'No Content' });
  });
});
