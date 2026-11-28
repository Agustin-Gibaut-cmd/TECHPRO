
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AuthCredentials, AuthForm } from './auth-form';

describe('AuthForm', () => {
  let component: AuthForm;
  let fixture: ComponentFixture<AuthForm>;

  const validCredentials: AuthCredentials = {
    name: '',
    email: 'ana@example.com',
    password: 'password',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuthForm],
    }).compileComponents();

    fixture = TestBed.createComponent(AuthForm);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  function setLoginCredentials(): void {
    component.authForm.controls.email.setValue(
      validCredentials.email,
    );

    component.authForm.controls.password.setValue(
      validCredentials.password,
    );
  }

  function subscribeToSubmission() {
    const submitted = vi.fn();
    component.submitted.subscribe(submitted);
    return submitted;
  }

  it('submits valid login credentials without requiring a name', () => {
    const submitted = subscribeToSubmission();

    setLoginCredentials();
    component.onSubmit();

    expect(submitted).toHaveBeenCalledWith(validCredentials);
    expect(submitted).toHaveBeenCalledTimes(1);
  });

  it('validates registration credentials and matching passwords', async () => {
    fixture.componentRef.setInput('registerMode', true);
    fixture.detectChanges();
    await fixture.whenStable();

    component.authForm.setValue({
      name: 'Ana',
      email: validCredentials.email,
      password: 'StrongPass!2026',
      confirmPassword: 'StrongPass!2025',
    });

    expect(
      component.authForm.hasError('passwordMismatch'),
    ).toBe(true);

    component.authForm.controls.confirmPassword.setValue(
      'StrongPass!2026',
    );

    expect(component.authForm.valid).toBe(true);
  });

  it('does not submit invalid credentials or while loading', () => {
    const submitted = subscribeToSubmission();

    component.onSubmit();
    expect(submitted).not.toHaveBeenCalled();

    setLoginCredentials();
    component.isLoading = true;
    component.onSubmit();

    expect(submitted).not.toHaveBeenCalled();
  });
});
