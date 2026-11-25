import { Component, ElementRef, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild, WritableSignal, inject, signal } from '@angular/core';
import { AbstractControl, FormBuilder, FormControl, FormGroup, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';

/** Datos limpios que emitimos al padre cuando el formulario pasa validaciones. */
export interface AuthCredentials {
  readonly name: string;
  readonly email: string;
  readonly password: string;
}

interface AuthFormControls {
  readonly name: FormControl<string>;
  readonly email: FormControl<string>;
  readonly password: FormControl<string>;
  readonly confirmPassword: FormControl<string>;
}

interface AuthFormRawValue {
  readonly name: string;
  readonly email: string;
  readonly password: string;
  readonly confirmPassword: string;
}

// Reglas mínimas de registro; en login solo exigimos que haya algo escrito en password.
const MIN_NAME_LENGTH: number = 2;
const MIN_REGISTER_PASSWORD_LENGTH: number = 12;

// Pequeña espera para que el DOM actualice los campos al cambiar entre login y registro.
const FOCUS_DELAY_MS: number = 50;

/**
 * Valida que password y confirmPassword coincidan.
 * Si confirmPassword aún está vacío, devolvemos null para no molestar al usuario
 * antes de que termine de escribirlo (el required se encarga de exigir llenarlo).
 */
function passwordsMatchValidator(control: AbstractControl): ValidationErrors | null {
  const password: string = String(control.get('password')?.value ?? '');
  const confirmPassword: string = String(control.get('confirmPassword')?.value ?? '');

  if (confirmPassword.length === 0) {
    return null;
  }

  return password === confirmPassword ? null : { passwordMismatch: true };
}

/**
 * Formulario reutilizable para iniciar sesión o registrarse según `registerMode`.
 * La lógica de petición HTTP vive afuera: este componente solo valida, limpia
 * los datos y emite `submitted`.
 */
@Component({
  selector: 'app-auth-form',
  imports: [ReactiveFormsModule],
  templateUrl: './auth-form.html',
})
export class AuthForm implements OnChanges {
  private readonly formBuilder: FormBuilder = inject(FormBuilder);

  /** Alterna entre modo login (`false`) y registro (`true`). */
  @Input() registerMode: boolean = false;

  /** Bloquea envíos mientras el componente padre procesa la autenticación. */
  @Input() isLoading: boolean = false;

  /** Mensaje de error devuelto por el backend o el padre, si aplica. */
  @Input() errorMessage: string | null = null;

  @Output() readonly submitted: EventEmitter<AuthCredentials> =
    new EventEmitter<AuthCredentials>();
  @Output() readonly modeToggle: EventEmitter<void> =
    new EventEmitter<void>();

  @ViewChild('firstInput') private firstInput?: ElementRef<HTMLInputElement>;

  readonly showPassword: WritableSignal<boolean> = signal<boolean>(false);
  readonly showConfirmPassword: WritableSignal<boolean> = signal<boolean>(false);

  readonly authForm: FormGroup<AuthFormControls> = this.buildForm();

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['registerMode']) {
      return;
    }

    // Reajustamos validadores y limpiamos campos extra cada vez que cambia el modo.
    this.applyModeValidators();
    this.resetOptionalFieldsOnLogin();
    this.recalculateFormValidity();
    this.resetPasswordVisibility();
    this.focusFirstInput();
  }

  onSubmit(): void {
    if (this.isLoading) {
      return;
    }

    if (this.authForm.invalid) {
      this.authForm.markAllAsTouched();
      return;
    }

    this.submitted.emit(this.buildCredentials());
  }

  private buildForm(): FormGroup<AuthFormControls> {
    return this.formBuilder.nonNullable.group({
      name: this.formBuilder.nonNullable.control<string>(''),
      email: this.formBuilder.nonNullable.control<string>('', [
        Validators.required,
        Validators.email,
      ]),
      password: this.formBuilder.nonNullable.control<string>('', [Validators.required]),
      confirmPassword: this.formBuilder.nonNullable.control<string>(''),
    });
  }

  private applyModeValidators(): void {
    const { name, email, password, confirmPassword }: AuthFormControls =
      this.authForm.controls;

    name.setValidators(
      this.registerMode
        ? [Validators.required, Validators.minLength(MIN_NAME_LENGTH)]
        : []
    );

    email.setValidators([Validators.required, Validators.email]);

    password.setValidators(
      this.registerMode
        ? [Validators.required, Validators.minLength(MIN_REGISTER_PASSWORD_LENGTH)]
        : [Validators.required]
    );

    confirmPassword.setValidators(
      this.registerMode ? [Validators.required] : []
    );

    // Solo tiene sentido exigir coincidencia de contraseñas durante el registro.
    this.authForm.setValidators(
      this.registerMode ? [passwordsMatchValidator] : []
    );
  }

  private resetOptionalFieldsOnLogin(): void {
    if (this.registerMode) {
      return;
    }

    // Limpiamos campos exclusivos de registro para que no queden valores colgados al volver a login.
    const { name, confirmPassword }: AuthFormControls = this.authForm.controls;
    name.reset('');
    confirmPassword.reset('');
  }

  private recalculateFormValidity(): void {
    const controls: AbstractControl[] = Object.values(this.authForm.controls);

    // Actualizamos cada control por separado primero para que el estado del grupo refleje el cambio.
    controls.forEach((control: AbstractControl): void => {
      control.updateValueAndValidity({ onlySelf: true });
    });

    this.authForm.updateValueAndValidity();
  }

  private resetPasswordVisibility(): void {
    this.showPassword.set(false);
    this.showConfirmPassword.set(false);
  }

  private focusFirstInput(): void {
    setTimeout((): void => {
      this.firstInput?.nativeElement.focus();
    }, FOCUS_DELAY_MS);
  }

  private buildCredentials(): AuthCredentials {
    const rawValue: AuthFormRawValue = this.authForm.getRawValue();

    // Normalizamos nombre y correo, pero dejamos la contraseña intacta por si tenía espacios intencionales.
    return {
      name: rawValue.name.trim(),
      email: rawValue.email.trim().toLowerCase(),
      password: rawValue.password,
    };
  }
}