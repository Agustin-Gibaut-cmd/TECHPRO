import {
  Component,
  ElementRef,
  ViewChild,
  WritableSignal,
  inject,
  signal,
} from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { AuthResult, AuthService } from '../auth.service';

interface AuthFormControls {
  name: FormControl<string>;
  email: FormControl<string>;
  password: FormControl<string>;
  confirmPassword: FormControl<string>;
}

const passwordsMatchValidator: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const password: string = control.get('password')?.value ?? '';
  const confirmPassword: string = control.get('confirmPassword')?.value ?? '';

  if (confirmPassword.length === 0) {
    return null;
  }

  return password === confirmPassword ? null : { passwordMismatch: true };
};

@Component({
  imports: [ReactiveFormsModule],
  selector: 'app-login',
  templateUrl: './login.html',
})
export class Login {
  private readonly fb: FormBuilder = inject(FormBuilder);
  private readonly router: Router = inject(Router);
  private readonly authService: AuthService = inject(AuthService);

  @ViewChild('firstInput') private readonly firstInput?: ElementRef<HTMLInputElement>;

  readonly isRegisterMode: WritableSignal<boolean> = signal<boolean>(false);
  readonly showPassword: WritableSignal<boolean> = signal<boolean>(false);
  readonly showConfirmPassword: WritableSignal<boolean> = signal<boolean>(false);
  readonly errorMessage: WritableSignal<string | null> = signal<string | null>(null);

  readonly authForm: FormGroup<AuthFormControls> = this.fb.nonNullable.group<AuthFormControls>(
    {
      name: this.fb.nonNullable.control<string>(''),
      email: this.fb.nonNullable.control<string>('', [Validators.required]),
      password: this.fb.nonNullable.control<string>('', [
        Validators.required,
        Validators.minLength(6),
      ]),
      confirmPassword: this.fb.nonNullable.control<string>(''),
    },
    { validators: passwordsMatchValidator }
  );

  toggleMode(): void {
    this.isRegisterMode.update((value: boolean): boolean => !value);
    this.errorMessage.set(null);
    this.showPassword.set(false);
    this.showConfirmPassword.set(false);

    const nameControl: FormControl<string> = this.authForm.controls.name;
    const emailControl: FormControl<string> = this.authForm.controls.email;
    const confirmControl: FormControl<string> = this.authForm.controls.confirmPassword;

    if (this.isRegisterMode()) {
      nameControl.setValidators([Validators.required, Validators.minLength(2)]);
      emailControl.setValidators([Validators.required, Validators.email]);
      confirmControl.setValidators([Validators.required]);
    } else {
      nameControl.clearValidators();
      nameControl.reset();
      emailControl.setValidators([Validators.required]);
      confirmControl.clearValidators();
      confirmControl.reset();
    }

    nameControl.updateValueAndValidity();
    emailControl.updateValueAndValidity();
    confirmControl.updateValueAndValidity();

    setTimeout((): void => {
      this.firstInput?.nativeElement.focus();
    }, 50);
  }

  onSubmit(): void {
    if (this.authForm.invalid) {
      this.authForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);

    const { name, email, password } = this.authForm.getRawValue();
    const result: AuthResult = this.isRegisterMode()
      ? this.authService.register(name, email, password)
      : this.authService.login(email, password);

    if (!result.success) {
      this.errorMessage.set(this.getErrorMessage(result.reason));
      return;
    }

    void this.router.navigate(['/dashboard']);
  }

  private getErrorMessage(reason: Extract<AuthResult, { success: false }>['reason']): string {
    switch (reason) {
      case 'email-already-registered':
        return 'Ese correo ya está registrado.';
      case 'storage-error':
        return 'No se pudo guardar la sesión. Revisá el almacenamiento del navegador.';
      case 'invalid-credentials':
        return 'Usuario o contraseña incorrectos.';
    }
  }
}