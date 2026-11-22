import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  ElementRef,
  EventEmitter,
  OnInit,
  Output,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import {
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { finalize } from 'rxjs';
import {
  CustomerPayload,
  CustomerRecord,
  CustomersService,
} from './customers.service';

interface CustomerFormControls {
  name: FormControl<string>;
  phone: FormControl<string>;
  email: FormControl<string>;
  address: FormControl<string>;
  notes: FormControl<string>;
}

@Component({
  imports: [DatePipe, ReactiveFormsModule],
  selector: 'app-customers',
  templateUrl: './customers.html',
})
export class Customers implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly customersService = inject(CustomersService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('customerFormElement')
  private readonly customerFormElement?: ElementRef<HTMLElement>;

  readonly customers = signal<CustomerRecord[]>([]);
  readonly editingCustomerId = signal<number | null>(null);
  readonly pendingDeleteId = signal<number | null>(null);
  readonly deletingCustomerId = signal<number | null>(null);
  readonly isLoading = signal(false);
  readonly isSaving = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly customerForm: FormGroup<CustomerFormControls> = this.fb.nonNullable.group({
    name: [
      '',
      [Validators.required, Validators.pattern(/\S/), Validators.maxLength(120)],
    ],
    phone: [
      '',
      [Validators.required, Validators.pattern(/\S/), Validators.maxLength(32)],
    ],
    email: ['', [Validators.email, Validators.maxLength(254)]],
    address: ['', [Validators.maxLength(200)]],
    notes: ['', [Validators.maxLength(1000)]],
  });

  ngOnInit(): void {
    this.loadCustomers();
  }

  loadCustomers(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.customersService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (customers) => this.customers.set(customers),
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  editCustomer(customer: CustomerRecord): void {
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.pendingDeleteId.set(null);
    this.editingCustomerId.set(customer.id);
    this.customerForm.setValue({
      name: customer.name,
      phone: customer.phone,
      email: customer.email,
      address: customer.address,
      notes: customer.notes,
    });
    this.customerFormElement?.nativeElement.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  }

  cancelEdit(): void {
    this.editingCustomerId.set(null);
    this.customerForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  saveCustomer(): void {
    if (this.isSaving() || this.deletingCustomerId() !== null) {
      return;
    }

    if (this.customerForm.invalid) {
      this.customerForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.isSaving.set(true);

    const formValue = this.customerForm.getRawValue();
    const payload: CustomerPayload = {
      ...formValue,
      name: formValue.name.trim(),
      phone: formValue.phone.trim(),
      email: formValue.email.trim().toLowerCase(),
      address: formValue.address.trim(),
      notes: formValue.notes.trim(),
    };
    const editingId = this.editingCustomerId();
    const request =
      editingId === null
        ? this.customersService.create(payload)
        : this.customersService.update(editingId, payload);

    request
      .pipe(finalize(() => this.isSaving.set(false)))
      .subscribe({
        next: (customer) => {
          this.customers.update((customers) =>
            [
              ...customers.filter((item) => item.id !== customer.id),
              customer,
            ].sort((left, right) => left.name.localeCompare(right.name))
          );
          this.editingCustomerId.set(null);
          this.customerForm.reset(this.emptyFormValue());
          this.successMessage.set(
            editingId === null
              ? 'El cliente se registró correctamente.'
              : 'El cliente se actualizó correctamente.'
          );
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  askToDelete(customerId: number): void {
    this.pendingDeleteId.update((pendingId) => (pendingId === customerId ? null : customerId));
    this.errorMessage.set(null);
  }

  deleteCustomer(customer: CustomerRecord): void {
    if (this.isSaving() || this.deletingCustomerId() !== null) {
      return;
    }

    this.errorMessage.set(null);
    this.deletingCustomerId.set(customer.id);

    this.customersService
      .delete(customer.id)
      .pipe(finalize(() => this.deletingCustomerId.set(null)))
      .subscribe({
        next: () => {
          this.customers.update((customers) =>
            customers.filter((item) => item.id !== customer.id)
          );
          if (this.editingCustomerId() === customer.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('El cliente se eliminó correctamente.');
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  private emptyFormValue(): CustomerPayload {
    return { name: '', phone: '', email: '', address: '', notes: '' };
  }

  private getErrorMessage(error: unknown): string {
    if (!(error instanceof HttpErrorResponse)) {
      return 'No se pudo completar la solicitud.';
    }
    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. Verificá que Django esté iniciado.';
    }
    if (error.status === 401) {
      return 'Tu sesión venció. Volvé a iniciar sesión para continuar.';
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
    return 'No se pudo guardar el cliente. Revisá los datos e intentá nuevamente.';
  }
}
