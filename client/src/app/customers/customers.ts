import { DatePipe } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  OnInit,
  Output,
  ViewChild,
  inject,
  signal,
  WritableSignal,
} from '@angular/core';
import {
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { finalize } from 'rxjs';
import { extractErrorMessage } from '../error.utils';
import {
  CustomerPayload,
  CustomerRecord,
  CustomersService,
} from './customers.service';

interface CustomerFormControls {
  readonly name: FormControl<string>;
  readonly phone: FormControl<string>;
  readonly email: FormControl<string>;
  readonly address: FormControl<string>;
  readonly notes: FormControl<string>;
}

/**
 * Componente para el alta, edición, consulta y baja de clientes del taller.
 */
@Component({
  imports: [DatePipe, ReactiveFormsModule],
  selector: 'app-customers',
  templateUrl: './customers.html',
})
export class Customers implements OnInit {
  private readonly fb: FormBuilder = inject(FormBuilder);
  private readonly customersService: CustomersService = inject(CustomersService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('customerFormElement')
  private readonly customerFormElement?: ElementRef<HTMLElement>;

  readonly customers: WritableSignal<CustomerRecord[]> = signal<CustomerRecord[]>([]);
  readonly editingCustomerId: WritableSignal<number | null> = signal<number | null>(null);
  readonly pendingDeleteId: WritableSignal<number | null> = signal<number | null>(null);
  readonly deletingCustomerId: WritableSignal<number | null> = signal<number | null>(null);
  readonly isLoading: WritableSignal<boolean> = signal<boolean>(false);
  readonly isSaving: WritableSignal<boolean> = signal<boolean>(false);
  readonly errorMessage: WritableSignal<string | null> = signal<string | null>(null);
  readonly successMessage: WritableSignal<string | null> = signal<string | null>(null);

  readonly customerForm: FormGroup<CustomerFormControls> = this.fb.nonNullable.group<CustomerFormControls>({
    name: this.fb.nonNullable.control('', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(120)]),
    phone: this.fb.nonNullable.control('', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(32)]),
    email: this.fb.nonNullable.control('', [Validators.email, Validators.maxLength(254)]),
    address: this.fb.nonNullable.control('', [Validators.maxLength(200)]),
    notes: this.fb.nonNullable.control('', [Validators.maxLength(1000)]),
  });

  ngOnInit(): void {
    this.loadCustomers();
  }

  /** Carga la cartera completa de clientes desde el servidor. */
  loadCustomers(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.customersService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (items: CustomerRecord[]) => this.customers.set(items),
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Carga los datos de un cliente en el formulario para edición. */
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

  /** Cancela la edición y reinicia el formulario. */
  cancelEdit(): void {
    this.editingCustomerId.set(null);
    this.customerForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  /** Guarda los cambios de un cliente existente o registra uno nuevo. */
  saveCustomer(): void {
    if (this.isSaving() || this.deletingCustomerId() !== null) {
      return;
    }

    this.customerForm.controls.email.setValue(
      this.customerForm.controls.email.value.trim(),
      { emitEvent: false }
    );
    if (this.customerForm.invalid) {
      this.customerForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.isSaving.set(true);

    const formValue = this.customerForm.getRawValue();
    const payload: CustomerPayload = {
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
        next: (customer: CustomerRecord) => {
          this.customers.update((items: CustomerRecord[]) =>
            [...items.filter((item: CustomerRecord) => item.id !== customer.id), customer].sort(
              (a: CustomerRecord, b: CustomerRecord) => a.name.localeCompare(b.name)
            )
          );
          this.editingCustomerId.set(null);
          this.customerForm.reset(this.emptyFormValue());
          this.successMessage.set(
            editingId === null
              ? 'El cliente se registró correctamente.'
              : 'El cliente se actualizó correctamente.'
          );
        },
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Muestra u oculta la confirmación de eliminación para un cliente. */
  askToDelete(customerId: number): void {
    this.pendingDeleteId.update((id: number | null) => (id === customerId ? null : customerId));
    this.errorMessage.set(null);
  }

  /** Da de baja el cliente seleccionado en el servidor. */
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
          this.customers.update((items: CustomerRecord[]) =>
            items.filter((item: CustomerRecord) => item.id !== customer.id)
          );
          if (this.editingCustomerId() === customer.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('El cliente se eliminó correctamente.');
        },
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  private emptyFormValue(): CustomerPayload {
    return { name: '', phone: '', email: '', address: '', notes: '' };
  }
}
