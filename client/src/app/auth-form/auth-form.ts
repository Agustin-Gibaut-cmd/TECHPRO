import { Component, ElementRef, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild, inject, signal,} from '@angular/core';
import { AbstractControl, FormBuilder, FormControl, FormGroup, ReactiveFormsModule, ValidationErrors, ValidatorFn, Validators,} from '@angular/forms';

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

class AuthFormValidator {
  static passwordsMatch: ValidatorFn = (
    control: AbstractControl
  ): ValidationErrors | null => {
    const { password, confirmPassword } = control.value;

    return !confirmPassword || password === confirmPassword
      ? null
      : { passwordMismatch: true };
  };
}

@Component({
  selector: 'app-auth-form',
  imports: [ReactiveFormsModule],
  templateUrl: './auth-form.html',
})
export class AuthForm implements OnChanges {
  private readonly fb = inject(FormBuilder);

  @Input() registerMode = false;
  @Input() isLoading = false;
  @Input() errorMessage: string | null = null;

  @Output() readonly submitted = new EventEmitter<AuthCredentials>();
  @Output() readonly modeToggle = new EventEmitter<void>();

  @ViewChild('firstInput') private firstInput?: ElementRef<HTMLInputElement>;

  readonly showPassword = signal(false);
  readonly showConfirmPassword = signal(false);

  readonly authForm: FormGroup<AuthFormControls> =
    this.fb.nonNullable.group({
      name: this.fb.nonNullable.control(''),
      email: this.fb.nonNullable.control('', [
        Validators.required, Validators.email,
      ]),
      password: this.fb.nonNullable.control('', [Validators.required]),
      confirmPassword: this.fb.nonNullable.control(''),
    }, { validators: AuthFormValidator.passwordsMatch });

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['registerMode']) {
      this.configureForm();
      this.resetVisibility();
      this.focusFirstInput();
    }
  }

  private configureForm(): void {
    const { name, email, password, confirmPassword } =
      this.authForm.controls;

    name.setValidators(this.registerMode
      ? [Validators.required, Validators.minLength(2)]
      : null);

    email.setValidators([Validators.required, Validators.email]);

    password.setValidators(this.registerMode
      ? [Validators.required, Validators.minLength(12)]
      : [Validators.required]);

    confirmPassword.setValidators(
      this.registerMode ? [Validators.required] : null
    );

    if (!this.registerMode) {
      name.reset();
      confirmPassword.reset();
    }

    Object.values(this.authForm.controls).forEach(control =>
      control.updateValueAndValidity({ onlySelf: true })
    );

    this.authForm.updateValueAndValidity();
  }

  private resetVisibility(): void {
    this.showPassword.set(false);
    this.showConfirmPassword.set(false);
  }

  private focusFirstInput(): void {
    setTimeout(() => this.firstInput?.nativeElement.focus(), 50);
  }

  onSubmit(): void {
    if (this.isLoading) return;

    if (this.authForm.invalid) {
      this.authForm.markAllAsTouched();
      return;
    }

    const { name, email, password } = this.authForm.getRawValue();

    this.submitted.emit({
      name: name.trim(),
      email: email.trim().toLowerCase(),
      password,
    });
  }
}
