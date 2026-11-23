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
  SupplierPayload,
  SupplierRecord,
  SuppliersService,
} from './suppliers.service';

interface SupplierFormControls {
  readonly name: FormControl<string>;
  readonly phone: FormControl<string>;
  readonly email: FormControl<string>;
  readonly address: FormControl<string>;
  readonly notes: FormControl<string>;
}

/**
 * Componente para el mantenimiento del catálogo de proveedores del taller.
 */
@Component({
  imports: [DatePipe, ReactiveFormsModule],
  selector: 'app-suppliers',
  templateUrl: './suppliers.html',
})
export class Suppliers implements OnInit {
  private readonly fb: FormBuilder = inject(FormBuilder);
  private readonly suppliersService: SuppliersService = inject(SuppliersService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('supplierFormElement')
  private readonly supplierFormElement?: ElementRef<HTMLElement>;

  readonly suppliers: WritableSignal<SupplierRecord[]> = signal<SupplierRecord[]>([]);
  readonly editingSupplierId: WritableSignal<number | null> = signal<number | null>(null);
  readonly pendingDeleteId: WritableSignal<number | null> = signal<number | null>(null);
  readonly deletingSupplierId: WritableSignal<number | null> = signal<number | null>(null);
  readonly isLoading: WritableSignal<boolean> = signal<boolean>(false);
  readonly isSaving: WritableSignal<boolean> = signal<boolean>(false);
  readonly errorMessage: WritableSignal<string | null> = signal<string | null>(null);
  readonly successMessage: WritableSignal<string | null> = signal<string | null>(null);

  readonly supplierForm: FormGroup<SupplierFormControls> = this.fb.nonNullable.group<SupplierFormControls>({
    name: this.fb.nonNullable.control('', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(120)]),
    phone: this.fb.nonNullable.control('', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(32)]),
    email: this.fb.nonNullable.control('', [Validators.email, Validators.maxLength(254)]),
    address: this.fb.nonNullable.control('', [Validators.maxLength(200)]),
    notes: this.fb.nonNullable.control('', [Validators.maxLength(1000)]),
  });

  ngOnInit(): void {
    this.loadSuppliers();
  }

  /** Carga la lista completa de proveedores desde el servidor. */
  loadSuppliers(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.suppliersService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (items: SupplierRecord[]) => this.suppliers.set(items),
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Abre el proveedor seleccionado en el formulario para edición. */
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

  /** Cancela la edición y reinicia los campos del formulario. */
  cancelEdit(): void {
    this.editingSupplierId.set(null);
    this.supplierForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  /** Guarda un nuevo proveedor o actualiza los datos del existente. */
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
        next: (supplier: SupplierRecord) => {
          this.suppliers.update((items: SupplierRecord[]) =>
            [...items.filter((item: SupplierRecord) => item.id !== supplier.id), supplier].sort(
              (a: SupplierRecord, b: SupplierRecord) => a.name.localeCompare(b.name)
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
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Muestra u oculta la confirmación de eliminación para un proveedor. */
  askToDelete(supplierId: number): void {
    this.pendingDeleteId.update((id: number | null) => (id === supplierId ? null : supplierId));
    this.errorMessage.set(null);
  }

  /** Da de baja el proveedor en el backend. */
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
          this.suppliers.update((items: SupplierRecord[]) =>
            items.filter((item: SupplierRecord) => item.id !== supplier.id)
          );
          if (this.editingSupplierId() === supplier.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('El proveedor se eliminó correctamente.');
        },
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  private emptyFormValue(): SupplierPayload {
    return { name: '', phone: '', email: '', address: '', notes: '' };
  }
}
