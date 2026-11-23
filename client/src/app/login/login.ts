import { Component, inject, signal, WritableSignal } from '@angular/core';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthCredentials, AuthForm } from '../auth-form/auth-form';
import { AuthService } from '../auth.service';
import { extractErrorMessage } from '../error.utils';

/**
 * Componente principal de acceso al sistema.
 * Permite alternar dinámicamente entre los modos de inicio de sesión y registro de cuenta.
 */
@Component({
  imports: [AuthForm],
  selector: 'app-login',
  templateUrl: './login.html',
})
export class Login {
  private readonly router: Router = inject(Router);
  private readonly authService: AuthService = inject(AuthService);

  readonly isRegisterMode: WritableSignal<boolean> = signal<boolean>(false);
  readonly isLoading: WritableSignal<boolean> = signal<boolean>(false);
  readonly errorMessage: WritableSignal<string | null> = signal<string | null>(null);

  /** Alterna entre el formulario de inicio de sesión y el de alta de cuenta. */
  toggleMode(): void {
    this.isRegisterMode.update((val: boolean) => !val);
    this.errorMessage.set(null);
  }

  /** Procesa el envío del formulario delegando en AuthService según el modo actual. */
  onSubmit(credentials: AuthCredentials): void {
    if (this.isLoading()) {
      return;
    }

    this.errorMessage.set(null);
    this.isLoading.set(true);

    const authCall = this.isRegisterMode()
      ? this.authService.register(credentials.name, credentials.email, credentials.password)
      : this.authService.login(credentials.email, credentials.password);

    authCall
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: () => void this.router.navigate(['/dashboard']),
        error: (err: unknown) => {
          this.errorMessage.set(
            extractErrorMessage(
              err,
              this.isRegisterMode()
                ? 'No se pudo crear la cuenta. Verificá los datos ingresados.'
                : 'Correo o contraseña incorrectos.'
            )
          );
        },
      });
  }
}
