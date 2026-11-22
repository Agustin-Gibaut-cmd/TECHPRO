import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { AuthForm } from '../auth-form/auth-form';
import { Login } from './login';

describe('Login', () => {
  let component: Login;
  let fixture: ComponentFixture<Login>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('uses the shared form and switches to registration validation', () => {
    const authForm = fixture.debugElement.query(By.directive(AuthForm))
      .componentInstance as AuthForm;
    authForm.authForm.controls.email.setValue('ana@example.com');
    authForm.authForm.controls.password.setValue('abc');
    fixture.detectChanges();

    expect(authForm.authForm.valid).toBe(true);

    component.toggleMode();
    fixture.detectChanges();

    expect(authForm.authForm.controls.password.hasError('minlength')).toBe(true);
  });
});
