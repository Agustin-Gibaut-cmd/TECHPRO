import { isPlatformBrowser } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { computed, inject, Injectable, PLATFORM_ID, signal } from '@angular/core';
import {
  EMPTY,
  Observable,
  catchError,
  finalize,
  map,
  of,
  shareReplay,
  switchMap,
  tap,
} from 'rxjs';
import { environment } from '../environments/environment';

export interface AuthUser {
  readonly name: string;
  readonly email: string;
}

export interface AuthResponse {
  readonly user: AuthUser;
}

interface CsrfTokenResponse {
  readonly csrfToken: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly platformId = inject(PLATFORM_ID);
  private csrfToken: string | null = null;
  private csrfRequest: Observable<string> | null = null;
  private refreshRequest: Observable<void> | null = null;

  private readonly session = signal<AuthUser | null>(null);

  readonly currentUser = computed(() => this.session());
  readonly isAuthenticated = computed(() => this.session() !== null);

  login(email: string, password: string): Observable<AuthResponse> {
    return this.postWithCsrf<AuthResponse>(`${environment.apiUrl}/auth/login/`, {
      email: email.trim().toLowerCase(),
      password,
    }).pipe(tap((response) => this.session.set(response.user)));
  }

  register(name: string, email: string, password: string): Observable<AuthResponse> {
    return this.postWithCsrf<AuthResponse>(`${environment.apiUrl}/auth/register/`, {
      name: name.trim(),
      email: email.trim().toLowerCase(),
      password,
    }).pipe(tap((response) => this.session.set(response.user)));
  }

  loadCurrentUser(): Observable<AuthUser> {
    return this.http
      .get<AuthUser>(`${environment.apiUrl}/auth/me/`, { withCredentials: true })
      .pipe(tap((user) => this.session.set(user)));
  }

  refreshAccessToken(): Observable<void> {
    if (!this.refreshRequest) {
      this.refreshRequest = this.postWithCsrf<void>(
        `${environment.apiUrl}/auth/token/refresh/`,
        {}
      ).pipe(
        finalize(() => {
          this.refreshRequest = null;
        }),
        shareReplay({ bufferSize: 1, refCount: false })
      );
    }

    return this.refreshRequest;
  }

  logout(): void {
    this.clearSession();
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    this.postWithCsrf<void>(`${environment.apiUrl}/auth/logout/`, {})
      .pipe(
        catchError((error: unknown) => {
          console.error('No se pudo revocar la sesión en el servidor.', error);
          return EMPTY;
        })
      )
      .subscribe();
  }

  clearSession(): void {
    this.session.set(null);
  }

  private postWithCsrf<T>(url: string, body: object): Observable<T> {
    return this.getCsrfToken().pipe(
      switchMap((csrfToken) =>
        this.http.post<T>(url, body, {
          headers: new HttpHeaders({ 'X-CSRFToken': csrfToken }),
          withCredentials: true,
        })
      )
    );
  }

  private getCsrfToken(): Observable<string> {
    if (this.csrfToken) {
      return of(this.csrfToken);
    }

    if (!this.csrfRequest) {
      this.csrfRequest = this.http
        .get<CsrfTokenResponse>(`${environment.apiUrl}/auth/csrf/`, {
          withCredentials: true,
        })
        .pipe(
          map(({ csrfToken }) => {
            if (!csrfToken) {
              throw new Error('El backend no devolvió un token CSRF.');
            }
            return csrfToken;
          }),
          tap((csrfToken) => {
            this.csrfToken = csrfToken;
          }),
          finalize(() => {
            this.csrfRequest = null;
          }),
          shareReplay({ bufferSize: 1, refCount: false })
        );
    }

    return this.csrfRequest;
  }
}
