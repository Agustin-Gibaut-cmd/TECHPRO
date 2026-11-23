import { Component, WritableSignal, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthCredentials, AuthForm } from '../auth-form/auth-form';
import { AuthService } from '../auth.service';

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

  toggleMode(): void {
    this.isRegisterMode.update((value: boolean): boolean => !value);
    this.errorMessage.set(null);
  }

  onSubmit(credentials: AuthCredentials): void {
    if (this.isLoading()) {
      return;
    }

    this.errorMessage.set(null);
    this.isLoading.set(true);

    const request = this.isRegisterMode()
      ? this.authService.register(credentials.name, credentials.email, credentials.password)
      : this.authService.login(credentials.email, credentials.password);

    request
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: () => void this.router.navigate(['/dashboard']),
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  private getErrorMessage(error: unknown): string {
    if (!(error instanceof HttpErrorResponse)) {
      return 'No se pudo completar la solicitud.';
    }

    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. Verificá que Django esté iniciado.';
    }

    if (typeof error.error === 'object' && error.error !== null) {
      for (const value of Object.values(error.error)) {
        if (typeof value === 'string') {
          return value;
        }

        if (Array.isArray(value)) {
          const message = value.find((item: unknown): item is string => typeof item === 'string');
          if (message) {
            return message;
          }
        }
      }
    }

    return 'No se pudo completar la operación. Revisá los datos e intentá nuevamente.';
  }
}