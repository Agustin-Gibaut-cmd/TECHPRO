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
  SupplierPayload,
  SupplierRecord,
  SuppliersService,
} from './suppliers.service';

interface SupplierFormControls {
  name: FormControl<string>;
  phone: FormControl<string>;
  email: FormControl<string>;
  address: FormControl<string>;
  notes: FormControl<string>;
}

@Component({
  imports: [DatePipe, ReactiveFormsModule],
  selector: 'app-suppliers',
  templateUrl: './suppliers.html',
})
export class Suppliers implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly suppliersService = inject(SuppliersService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('supplierFormElement')
  private readonly supplierFormElement?: ElementRef<HTMLElement>;

  readonly suppliers = signal<SupplierRecord[]>([]);
  readonly editingSupplierId = signal<number | null>(null);
  readonly pendingDeleteId = signal<number | null>(null);
  readonly deletingSupplierId = signal<number | null>(null);
  readonly isLoading = signal(false);
  readonly isSaving = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly supplierForm: FormGroup<SupplierFormControls> = this.fb.nonNullable.group({
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
    this.loadSuppliers();
  }

  loadSuppliers(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.suppliersService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (suppliers) => this.suppliers.set(suppliers),
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  editSupplier(supplier: SupplierRecord): void {
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.pendingDeleteId.set(null);
    this.editingSupplierId.set(supplier.id);
    this.supplierForm.setValue({
      name: supplier.name,
      phone: supplier.phone,
      email: supplier.email,
      address: supplier.address,
      notes: supplier.notes,
    });
    this.supplierFormElement?.nativeElement.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  }

  cancelEdit(): void {
    this.editingSupplierId.set(null);
    this.supplierForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  saveSupplier(): void {
    if (this.isSaving() || this.deletingSupplierId() !== null) {
      return;
    }

    this.supplierForm.controls.email.setValue(
      this.supplierForm.controls.email.value.trim(),
      { emitEvent: false }
    );
    if (this.supplierForm.invalid) {
      this.supplierForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.isSaving.set(true);

    const formValue = this.supplierForm.getRawValue();
    const payload: SupplierPayload = {
      ...formValue,
      name: formValue.name.trim(),
      phone: formValue.phone.trim(),
      email: formValue.email.trim().toLowerCase(),
      address: formValue.address.trim(),
      notes: formValue.notes.trim(),
    };
    const editingId = this.editingSupplierId();
    const request =
      editingId === null
        ? this.suppliersService.create(payload)
        : this.suppliersService.update(editingId, payload);

    request
      .pipe(finalize(() => this.isSaving.set(false)))
      .subscribe({
        next: (supplier) => {
          this.suppliers.update((suppliers) =>
            [...suppliers.filter((item) => item.id !== supplier.id), supplier].sort(
              (left, right) => left.name.localeCompare(right.name)
            )
          );
          this.editingSupplierId.set(null);
          this.supplierForm.reset(this.emptyFormValue());
          this.successMessage.set(
            editingId === null
              ? 'El proveedor se registró correctamente.'
              : 'El proveedor se actualizó correctamente.'
          );
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  askToDelete(supplierId: number): void {
    this.pendingDeleteId.update((pendingId) =>
      pendingId === supplierId ? null : supplierId
    );
    this.errorMessage.set(null);
  }

  deleteSupplier(supplier: SupplierRecord): void {
    if (this.isSaving() || this.deletingSupplierId() !== null) {
      return;
    }

    this.errorMessage.set(null);
    this.deletingSupplierId.set(supplier.id);

    this.suppliersService
      .delete(supplier.id)
      .pipe(finalize(() => this.deletingSupplierId.set(null)))
      .subscribe({
        next: () => {
          this.suppliers.update((suppliers) =>
            suppliers.filter((item) => item.id !== supplier.id)
          );
          if (this.editingSupplierId() === supplier.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('El proveedor se eliminó correctamente.');
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  private emptyFormValue(): SupplierPayload {
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
    return 'No se pudo guardar el proveedor. Revisá los datos e intentá nuevamente.';
  }
}
