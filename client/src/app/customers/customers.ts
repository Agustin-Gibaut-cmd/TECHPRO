import { DatePipe } from '@angular/common';
import { Component, ElementRef, Injectable, OnInit, WritableSignal, inject, output, signal, viewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable, finalize } from 'rxjs';
import { extractErrorMessage } from '../error.utils';
import { CustomerPayload, CustomerRecord, CustomersService } from './customers.service';

// --- Dominio, restricciones y mapeo ---
export interface CustomerFormControls {
  name: FormControl<string>;
  phone: FormControl<string>;
  email: FormControl<string>;
  address: FormControl<string>;
  notes: FormControl<string>;
}

export interface FieldConstraints {
  nameMaxLength: number;
  phoneMaxLength: number;
  emailMaxLength: number;
  addressMaxLength: number;
  notesMaxLength: number;
  nonWhitespacePattern: RegExp;
}

export interface FeedbackMessages {
  created: string;
  updated: string;
  deleted: string;
}

export const CUSTOMER_CONSTRAINTS: FieldConstraints = {
  nameMaxLength: 120,
  phoneMaxLength: 32,
  emailMaxLength: 254,
  addressMaxLength: 200,
  notesMaxLength: 1000,
  nonWhitespacePattern: /\S/,
};

export const CUSTOMER_MESSAGES: FeedbackMessages = {
  created: 'El cliente se registró correctamente.',
  updated: 'El cliente se actualizó correctamente.',
  deleted: 'El cliente se eliminó correctamente.',
};

export const EMPTY_CUSTOMER: CustomerPayload = { name: '', phone: '', email: '', address: '', notes: '' };
export const FORM_SCROLL_OPTIONS: ScrollIntoViewOptions = { behavior: 'smooth', block: 'start' };

export const normalizeCustomerPayload = (raw: CustomerPayload): CustomerPayload => ({
  name: raw.name.trim(),
  phone: raw.phone.trim(),
  email: raw.email.trim().toLowerCase(),
  address: raw.address.trim(),
  notes: raw.notes.trim(),
});

export const toFormPayload = (customer: CustomerRecord): CustomerPayload => ({
  name: customer.name,
  phone: customer.phone,
  email: customer.email,
  address: customer.address,
  notes: customer.notes,
});

export const upsertCustomerSorted = (items: CustomerRecord[], saved: CustomerRecord): CustomerRecord[] =>
  [...items.filter((item: CustomerRecord) => item.id !== saved.id), saved].sort(
    (a: CustomerRecord, b: CustomerRecord) => a.name.localeCompare(b.name)
  );

// --- Facade de estado y operaciones CRUD ---
@Injectable()
export class CustomersFacade {
  private readonly customersService: CustomersService = inject(CustomersService);

  readonly customers: WritableSignal<CustomerRecord[]> = signal<CustomerRecord[]>([]);
  readonly editingCustomerId: WritableSignal<number | null> = signal<number | null>(null);
  readonly pendingDeleteId: WritableSignal<number | null> = signal<number | null>(null);
  readonly deletingCustomerId: WritableSignal<number | null> = signal<number | null>(null);
  readonly isLoading: WritableSignal<boolean> = signal<boolean>(false);
  readonly isSaving: WritableSignal<boolean> = signal<boolean>(false);
  readonly errorMessage: WritableSignal<string | null> = signal<string | null>(null);
  readonly successMessage: WritableSignal<string | null> = signal<string | null>(null);

  isBusy(): boolean {
    return this.isSaving() || this.deletingCustomerId() !== null;
  }

  resetFeedback(): void {
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  loadAll(): void {
    this.resetFeedback();
    this.isLoading.set(true);
    this.customersService.list().pipe(finalize(() => this.isLoading.set(false))).subscribe({
      next: (items: CustomerRecord[]) => this.customers.set(items),
      error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
    });
  }

  save(payload: CustomerPayload, onCompleted: () => void): void {
    this.resetFeedback();
    this.isSaving.set(true);
    const editingId: number | null = this.editingCustomerId();
    const request$: Observable<CustomerRecord> = editingId === null
      ? this.customersService.create(payload)
      : this.customersService.update(editingId, payload);

    request$.pipe(finalize(() => this.isSaving.set(false))).subscribe({
      next: (saved: CustomerRecord) => {
        this.customers.update((items: CustomerRecord[]) => upsertCustomerSorted(items, saved));
        this.editingCustomerId.set(null);
        onCompleted();
        this.successMessage.set(editingId === null ? CUSTOMER_MESSAGES.created : CUSTOMER_MESSAGES.updated);
      },
      error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
    });
  }

  toggleDeleteConfirmation(customerId: number): void {
    this.pendingDeleteId.update((current: number | null) => (current === customerId ? null : customerId));
    this.errorMessage.set(null);
  }

  remove(customerId: number, onEditedDeleted: () => void): void {
    this.resetFeedback();
    this.deletingCustomerId.set(customerId);
    this.customersService.delete(customerId).pipe(finalize(() => this.deletingCustomerId.set(null))).subscribe({
      next: () => {
        this.customers.update((items: CustomerRecord[]) => items.filter((item: CustomerRecord) => item.id !== customerId));
        if (this.editingCustomerId() === customerId) {
          this.editingCustomerId.set(null);
          onEditedDeleted();
        }
        this.pendingDeleteId.set(null);
        this.successMessage.set(CUSTOMER_MESSAGES.deleted);
      },
      error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
    });
  }
}

/** Componente para el alta, edición, consulta y baja de clientes del taller. */
@Component({
  imports: [DatePipe, ReactiveFormsModule],
  providers: [CustomersFacade],
  selector: 'app-customers',
  templateUrl: './customers.html',
})


export class Customers implements OnInit {
  private readonly fb: FormBuilder = inject(FormBuilder);
  private readonly facade: CustomersFacade = inject(CustomersFacade);

  readonly back = output<void>();
  private readonly customerFormElement = viewChild<ElementRef<HTMLElement>>('customerFormElement');

  readonly customers: WritableSignal<CustomerRecord[]> = this.facade.customers;
  readonly editingCustomerId: WritableSignal<number | null> = this.facade.editingCustomerId;
  readonly pendingDeleteId: WritableSignal<number | null> = this.facade.pendingDeleteId;
  readonly deletingCustomerId: WritableSignal<number | null> = this.facade.deletingCustomerId;
  readonly isLoading: WritableSignal<boolean> = this.facade.isLoading;
  readonly isSaving: WritableSignal<boolean> = this.facade.isSaving;
  readonly errorMessage: WritableSignal<string | null> = this.facade.errorMessage;
  readonly successMessage: WritableSignal<string | null> = this.facade.successMessage;

  readonly customerForm: FormGroup<CustomerFormControls> = this.fb.nonNullable.group({
    name: this.fb.nonNullable.control('', [Validators.required, Validators.pattern(CUSTOMER_CONSTRAINTS.nonWhitespacePattern), Validators.maxLength(CUSTOMER_CONSTRAINTS.nameMaxLength)]),
    phone: this.fb.nonNullable.control('', [Validators.required, Validators.pattern(CUSTOMER_CONSTRAINTS.nonWhitespacePattern), Validators.maxLength(CUSTOMER_CONSTRAINTS.phoneMaxLength)]),
    email: this.fb.nonNullable.control('', [Validators.email, Validators.maxLength(CUSTOMER_CONSTRAINTS.emailMaxLength)]),
    address: this.fb.nonNullable.control('', [Validators.maxLength(CUSTOMER_CONSTRAINTS.addressMaxLength)]),
    notes: this.fb.nonNullable.control('', [Validators.maxLength(CUSTOMER_CONSTRAINTS.notesMaxLength)]),
  });

  ngOnInit(): void {
    this.loadCustomers();
  }

  /** Carga la cartera completa de clientes desde el servidor. */
  loadCustomers(): void {
    this.facade.loadAll();
  }

  /** Carga los datos de un cliente en el formulario para edición. */
  editCustomer(customer: CustomerRecord): void {
    this.facade.resetFeedback();
    this.pendingDeleteId.set(null);
    this.editingCustomerId.set(customer.id);
    this.customerForm.setValue(toFormPayload(customer));
    this.customerFormElement()?.nativeElement.scrollIntoView?.(FORM_SCROLL_OPTIONS);
  }

  /** Cancela la edición y reinicia el formulario. */
  cancelEdit(): void {
    this.editingCustomerId.set(null);
    this.customerForm.reset({ ...EMPTY_CUSTOMER });
    this.facade.resetFeedback();
  }

  /** Guarda los cambios de un cliente existente o registra uno nuevo. */
  saveCustomer(): void {
    if (this.facade.isBusy()) return;

    const emailControl: FormControl<string> = this.customerForm.controls.email;
    emailControl.setValue(emailControl.value.trim(), { emitEvent: false });

    if (this.customerForm.invalid) {
      this.customerForm.markAllAsTouched();
      return;
    }

    this.facade.save(normalizeCustomerPayload(this.customerForm.getRawValue()), () => {
      this.customerForm.reset({ ...EMPTY_CUSTOMER });
    });
  }

  /** Muestra u oculta la confirmación de eliminación para un cliente. */
  askToDelete(customerId: number): void {
    this.facade.toggleDeleteConfirmation(customerId);
  }

  /** Da de baja el cliente seleccionado en el servidor. */
  deleteCustomer(customer: CustomerRecord): void {
    if (this.facade.isBusy()) return;
    this.facade.remove(customer.id, () => this.customerForm.reset({ ...EMPTY_CUSTOMER }));
  }
}