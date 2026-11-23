import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
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

export interface AuthCredentials {
  readonly name: string;
  readonly email: string;
  readonly password: string;
}

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
  selector: 'app-auth-form',
  templateUrl: './auth-form.html',
})
export class AuthForm implements OnChanges {
  private readonly fb: FormBuilder = inject(FormBuilder);

  @Input() registerMode = false;
  @Input() isLoading = false;
  @Input() errorMessage: string | null = null;
  @Output() submitted = new EventEmitter<AuthCredentials>();
  @Output() modeToggle = new EventEmitter<void>();
  @ViewChild('firstInput') private readonly firstInput?: ElementRef<HTMLInputElement>;

  readonly showPassword = signal(false);
  readonly showConfirmPassword = signal(false);
  readonly authForm: FormGroup<AuthFormControls> = this.fb.nonNullable.group<AuthFormControls>(
    {
      name: this.fb.nonNullable.control(''),
      email: this.fb.nonNullable.control('', [Validators.required, Validators.email]),
      password: this.fb.nonNullable.control('', [Validators.required]),
      confirmPassword: this.fb.nonNullable.control(''),
    },
    { validators: passwordsMatchValidator }
  );

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['registerMode']) {
      return;
    }

    const { name, email, password, confirmPassword } = this.authForm.controls;

    if (this.registerMode) {
      name.setValidators([Validators.required, Validators.minLength(2)]);
      email.setValidators([Validators.required, Validators.email]);
      password.setValidators([Validators.required, Validators.minLength(12)]);
      confirmPassword.setValidators([Validators.required]);
    } else {
      name.clearValidators();
      name.reset();
      email.setValidators([Validators.required, Validators.email]);
      password.setValidators([Validators.required]);
      confirmPassword.clearValidators();
      confirmPassword.reset();
    }

    Object.values(this.authForm.controls).forEach((control) => {
      control.updateValueAndValidity();
    });
    this.showPassword.set(false);
    this.showConfirmPassword.set(false);

    setTimeout(() => this.firstInput?.nativeElement.focus(), 50);
  }

  onSubmit(): void {
    if (this.isLoading) {
      return;
    }

    if (this.authForm.invalid) {
      this.authForm.markAllAsTouched();
      return;
    }

    const { name, email, password } = this.authForm.getRawValue();
    this.submitted.emit({ name, email, password });
  }
}
