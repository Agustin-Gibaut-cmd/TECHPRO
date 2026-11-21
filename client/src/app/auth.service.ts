import { isPlatformBrowser } from '@angular/common';
import { computed, inject, Injectable, PLATFORM_ID, signal } from '@angular/core';

export interface AuthUser {
  readonly name: string;
  readonly email: string;
}

interface DemoAccount extends AuthUser {
  readonly password: string;
}

export type AuthResult =
  | { readonly success: true; readonly user: AuthUser }
  | {
      readonly success: false;
      readonly reason: 'invalid-credentials' | 'email-already-registered' | 'storage-error';
    };

const SESSION_STORAGE_KEY = 'currentUser';
const DEMO_ACCOUNTS: readonly DemoAccount[] = [
  { name: 'Administrador', email: 'admin@admin.com', password: 'admin123' },
];

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly platformId = inject(PLATFORM_ID);
  private readonly accounts: DemoAccount[] = [...DEMO_ACCOUNTS];

  readonly currentUser = signal<AuthUser | null>(this.restoreSession());
  readonly isAuthenticated = computed(() => this.currentUser() !== null);

  login(email: string, password: string): AuthResult {
    const normalizedEmail = email.trim().toLowerCase();
    const account = this.accounts.find(
      (candidate) =>
        (candidate.email === normalizedEmail ||
          (normalizedEmail === 'admin' && candidate.email === 'admin@admin.com')) &&
        candidate.password === password
    );

    if (!account) {
      return { success: false, reason: 'invalid-credentials' };
    }

    return this.startSession(account);
  }

  register(name: string, email: string, password: string): AuthResult {
    const normalizedEmail = email.trim().toLowerCase();
    const accountExists = this.accounts.some((account) => account.email === normalizedEmail);

    if (accountExists) {
      return { success: false, reason: 'email-already-registered' };
    }

    const account: DemoAccount = {
      name: name.trim(),
      email: normalizedEmail,
      password,
    };
    const result = this.startSession(account);

    if (result.success) {
      this.accounts.push(account);
    }

    return result;
  }

  logout(): void {
    this.currentUser.set(null);

    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    try {
      localStorage.removeItem(SESSION_STORAGE_KEY);
    } catch (error) {
      console.error('No se pudo eliminar la sesión guardada.', error);
    }
  }

  private startSession(account: AuthUser): AuthResult {
    const user: AuthUser = { name: account.name, email: account.email };

    if (isPlatformBrowser(this.platformId)) {
      try {
        localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(user));
      } catch (error) {
        console.error('No se pudo guardar la sesión.', error);
        return { success: false, reason: 'storage-error' };
      }
    }

    this.currentUser.set(user);
    return { success: true, user };
  }

  private restoreSession(): AuthUser | null {
    if (!isPlatformBrowser(this.platformId)) {
      return null;
    }

    try {
      const session = localStorage.getItem(SESSION_STORAGE_KEY);
      if (!session) {
        return null;
      }

      const user: unknown = JSON.parse(session);
      if (
        typeof user === 'object' &&
        user !== null &&
        'name' in user &&
        'email' in user &&
        typeof user.name === 'string' &&
        typeof user.email === 'string'
      ) {
        return { name: user.name, email: user.email };
      }

      return null;
    } catch (error) {
      console.error('No se pudo restaurar la sesión guardada.', error);
      return null;
    }
  }
}
