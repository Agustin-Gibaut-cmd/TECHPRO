import { isPlatformBrowser } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { computed, inject, Injectable, PLATFORM_ID, signal, Signal } from '@angular/core';
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

/**
 * Servicio centralizado para la autenticación y gestión de sesiones mediante cookies HttpOnly.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly platformId = inject(PLATFORM_ID);

  private csrfToken: string | null = null;
  private csrfRequest: Observable<string> | null = null;
  private refreshRequest: Observable<void> | null = null;

  private readonly session = signal<AuthUser | null>(null);

  readonly currentUser: Signal<AuthUser | null> = computed(() => this.session());
  readonly isAuthenticated: Signal<boolean> = computed(() => this.session() !== null);

  /** Inicia sesión mediante email y contraseña, guardando el usuario en memoria. */
  login(email: string, password: string): Observable<AuthResponse> {
    return this.postWithCsrf<AuthResponse>(`${environment.apiUrl}/auth/login/`, {
      email: email.trim().toLowerCase(),
      password,
    }).pipe(tap((res: AuthResponse) => this.session.set(res.user)));
  }

  /** Registra un nuevo usuario en la plataforma. */
  register(name: string, email: string, password: string): Observable<AuthResponse> {
    return this.postWithCsrf<AuthResponse>(`${environment.apiUrl}/auth/register/`, {
      name: name.trim(),
      email: email.trim().toLowerCase(),
      password,
    }).pipe(tap((res: AuthResponse) => this.session.set(res.user)));
  }

  /** Carga la información de la cuenta activa a partir de la cookie de sesión. */
  loadCurrentUser(): Observable<AuthUser> {
    return this.http
      .get<AuthUser>(`${environment.apiUrl}/auth/me/`, { withCredentials: true })
      .pipe(tap((user: AuthUser) => this.session.set(user)));
  }

  /** Rota y renueva los tokens JWT en el servidor mediante la cookie de refresco. */
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

  /** Cierra la sesión activa revocando el token en el servidor y limpiando la memoria. */
  logout(): void {
    this.clearSession();
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    this.postWithCsrf<void>(`${environment.apiUrl}/auth/logout/`, {})
      .pipe(
        catchError((err: unknown) => {
          console.error('No se pudo revocar la sesión en el servidor.', err);
          return EMPTY;
        })
      )
      .subscribe();
  }

  /** Restablece el estado de sesión en memoria. */
  clearSession(): void {
    this.session.set(null);
  }

  /** Construye los encabezados requeridos para peticiones protegidas por CSRF. */
  getCsrfHeaders(): Observable<HttpHeaders> {
    return this.getCsrfToken().pipe(
      map((token: string) => new HttpHeaders({ 'X-CSRFToken': token }))
    );
  }

  private postWithCsrf<T>(url: string, body: object): Observable<T> {
    return this.getCsrfHeaders().pipe(
      switchMap((headers: HttpHeaders) =>
        this.http.post<T>(url, body, {
          headers,
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
          map(({ csrfToken }: CsrfTokenResponse) => {
            if (!csrfToken) {
              throw new Error('El backend no devolvió un token CSRF.');
            }
            return csrfToken;
          }),
          tap((token: string) => {
            this.csrfToken = token;
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
