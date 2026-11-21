import { TestBed } from '@angular/core/testing';
import { PLATFORM_ID } from '@angular/core';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let authService: AuthService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [{ provide: PLATFORM_ID, useValue: 'browser' }],
    });
    authService = TestBed.inject(AuthService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('authenticates the demo administrator with either supported login', () => {
    expect(authService.login('admin', 'admin123').success).toBe(true);

    authService.logout();
    expect(authService.login(' ADMIN@ADMIN.COM ', 'admin123').success).toBe(true);
  });

  it('registers a user, starts a session, and does not persist the password', () => {
    const result = authService.register('Ana Pérez', 'ANA@example.com', 'secret123');

    expect(result.success).toBe(true);
    expect(authService.currentUser()).toEqual({
      name: 'Ana Pérez',
      email: 'ana@example.com',
    });
    expect(localStorage.getItem('currentUser')).not.toContain('secret123');
  });

  it('restores the saved session when the service is recreated', () => {
    authService.login('admin@admin.com', 'admin123');

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [{ provide: PLATFORM_ID, useValue: 'browser' }],
    });
    authService = TestBed.inject(AuthService);

    expect(authService.currentUser()).toEqual({
      name: 'Administrador',
      email: 'admin@admin.com',
    });
  });

  it('rejects duplicate email addresses regardless of letter casing', () => {
    authService.register('Ana', 'ana@example.com', 'secret123');

    expect(authService.register('Otra Ana', 'ANA@example.com', 'secret456')).toEqual({
      success: false,
      reason: 'email-already-registered',
    });
  });
});
