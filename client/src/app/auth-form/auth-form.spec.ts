import { ComponentFixture, TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AuthCredentials, AuthForm } from './auth-form';

describe('AuthForm', () => {
  let component: AuthForm;
  let fixture: ComponentFixture<AuthForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuthForm],
    }).compileComponents();

    fixture = TestBed.createComponent(AuthForm);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('submits valid login credentials without requiring a name', () => {
    const credentials: AuthCredentials = {
      name: '',
      email: 'ana@example.com',
      password: 'password',
    };
    const submitted = vi.fn();
    component.submitted.subscribe(submitted);
    component.authForm.controls.email.setValue(credentials.email);
    component.authForm.controls.password.setValue(credentials.password);

    component.onSubmit();

    expect(submitted).toHaveBeenCalledWith(credentials);
    expect(submitted).toHaveBeenCalledTimes(1);
  });

  it('requires a valid name, long matching passwords, and email in registration mode', async () => {
    component.registerMode = true;
    fixture.detectChanges();
    await fixture.whenStable();

    component.authForm.setValue({
      name: 'Ana',
      email: 'ana@example.com',
      password: 'StrongPass!2026',
      confirmPassword: 'StrongPass!2025',
    });

    expect(component.authForm.hasError('passwordMismatch')).toBe(true);

    component.authForm.controls.confirmPassword.setValue('StrongPass!2026');

    expect(component.authForm.valid).toBe(true);
  });

  it('does not emit while invalid or loading', () => {
    const submitted = vi.fn();
    component.submitted.subscribe(submitted);

    component.onSubmit();
    expect(submitted).not.toHaveBeenCalled();

    component.authForm.controls.email.setValue('ana@example.com');
    component.authForm.controls.password.setValue('password');
    component.isLoading = true;
    component.onSubmit();

    expect(submitted).not.toHaveBeenCalled();
  });
});
