import {
  HttpClient,
  HttpErrorResponse,
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { vi } from 'vitest';
import { AuthService } from './auth.service';
import { authInterceptor } from './auth.interceptor';
import { environment } from '../environments/environment';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('sends cookies to the API but not to unrelated origins', () => {
    http.get(`${environment.apiUrl}/customers/`).subscribe();
    http.get('https://external.example/data').subscribe();

    const apiRequest = httpMock.expectOne(`${environment.apiUrl}/customers/`);
    const externalRequest = httpMock.expectOne('https://external.example/data');

    expect(apiRequest.request.withCredentials).toBe(true);
    expect(externalRequest.request.withCredentials).toBe(false);
    apiRequest.flush([]);
    externalRequest.flush({});
  });

  it('refreshes once and retries an unauthorized API request', () => {
    let response: unknown;
    let failure: unknown;

    http.get(`${environment.apiUrl}/customers/`).subscribe({
      next: (value) => (response = value),
      error: (error: unknown) => (failure = error),
    });

    const originalRequest = httpMock.expectOne(`${environment.apiUrl}/customers/`);
    expect(originalRequest.request.withCredentials).toBe(true);
    originalRequest.flush(
      { detail: 'Unauthorized' },
      { status: 401, statusText: 'Unauthorized' }
    );

    const csrfRequest = httpMock.expectOne(`${environment.apiUrl}/auth/csrf/`);
    csrfRequest.flush({ csrfToken: 'csrf-token' });
    const refreshRequest = httpMock.expectOne(
      `${environment.apiUrl}/auth/token/refresh/`
    );
    expect(refreshRequest.request.method).toBe('POST');
    expect(refreshRequest.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    refreshRequest.flush(null, { status: 204, statusText: 'No Content' });

    const retryRequest = httpMock.expectOne(`${environment.apiUrl}/customers/`);
    expect(retryRequest.request.withCredentials).toBe(true);
    retryRequest.flush([{ id: 1 }]);

    expect(response).toEqual([{ id: 1 }]);
    expect(failure).toBeUndefined();
  });

  it('clears the session and redirects if refresh fails', () => {
    const authService = TestBed.inject(AuthService);
    const router = TestBed.inject(Router);
    const navigate = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    let failure: unknown;

    authService.loadCurrentUser().subscribe({
      error: () => undefined,
    });
    httpMock
      .expectOne(`${environment.apiUrl}/auth/me/`)
      .flush({ name: 'Ana', email: 'ana@example.com' });
    expect(authService.isAuthenticated()).toBe(true);

    http.get(`${environment.apiUrl}/customers/`).subscribe({
      error: (error: unknown) => (failure = error),
    });
    httpMock.expectOne(`${environment.apiUrl}/customers/`).flush(
      { detail: 'Unauthorized' },
      { status: 401, statusText: 'Unauthorized' }
    );
    httpMock
      .expectOne(`${environment.apiUrl}/auth/csrf/`)
      .flush({ csrfToken: 'csrf-token' });
    httpMock
      .expectOne(`${environment.apiUrl}/auth/token/refresh/`)
      .flush({ detail: 'Expired' }, { status: 401, statusText: 'Unauthorized' });

    expect(failure).toBeInstanceOf(HttpErrorResponse);
    expect(authService.isAuthenticated()).toBe(false);
    expect(navigate).toHaveBeenCalledWith(['/login']);
  });
});
