import { CurrencyPipe } from '@angular/common';
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
  InventoryPayload,
  InventoryRecord,
  InventoryService,
} from './inventory.service';

interface InventoryFormControls {
  name: FormControl<string>;
  sku: FormControl<string>;
  category: FormControl<string>;
  description: FormControl<string>;
  quantity: FormControl<number>;
  min_stock: FormControl<number>;
  unit_price: FormControl<number>;
}

@Component({
  imports: [CurrencyPipe, ReactiveFormsModule],
  selector: 'app-inventory',
  templateUrl: './inventory.html',
})
export class Inventory implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly inventoryService = inject(InventoryService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('inventoryFormElement')
  private readonly inventoryFormElement?: ElementRef<HTMLElement>;

  readonly items = signal<InventoryRecord[]>([]);
  readonly editingItemId = signal<number | null>(null);
  readonly pendingDeleteId = signal<number | null>(null);
  readonly deletingItemId = signal<number | null>(null);
  readonly isLoading = signal(false);
  readonly isSaving = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly inventoryForm: FormGroup<InventoryFormControls> = this.fb.nonNullable.group({
    name: [
      '',
      [Validators.required, Validators.pattern(/\S/), Validators.maxLength(120)],
    ],
    sku: [
      '',
      [Validators.required, Validators.pattern(/\S/), Validators.maxLength(40)],
    ],
    category: ['', [Validators.maxLength(80)]],
    description: ['', [Validators.maxLength(1000)]],
    quantity: this.fb.nonNullable.control(0, [
      Validators.required,
      Validators.min(0),
      Validators.pattern(/^\d+$/),
    ]),
    min_stock: this.fb.nonNullable.control(0, [
      Validators.required,
      Validators.min(0),
      Validators.pattern(/^\d+$/),
    ]),
    unit_price: this.fb.nonNullable.control(0, [
      Validators.required,
      Validators.min(0),
      Validators.pattern(/^\d+(\.\d{1,2})?$/),
    ]),
  });

  ngOnInit(): void {
    this.loadItems();
  }

  loadItems(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.inventoryService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (items) => this.items.set(items),
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  editItem(item: InventoryRecord): void {
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.pendingDeleteId.set(null);
    this.editingItemId.set(item.id);
    this.inventoryForm.setValue({
      name: item.name,
      sku: item.sku,
      category: item.category,
      description: item.description,
      quantity: item.quantity,
      min_stock: item.min_stock,
      unit_price: Number(item.unit_price),
    });
    this.inventoryFormElement?.nativeElement.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  }

  cancelEdit(): void {
    this.editingItemId.set(null);
    this.inventoryForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  saveItem(): void {
    if (this.isSaving() || this.deletingItemId() !== null) {
      return;
    }

    if (this.inventoryForm.invalid) {
      this.inventoryForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.isSaving.set(true);

    const formValue = this.inventoryForm.getRawValue();
    const payload: InventoryPayload = {
      ...formValue,
      name: formValue.name.trim(),
      sku: formValue.sku.trim().toUpperCase(),
      category: formValue.category.trim(),
      description: formValue.description.trim(),
    };
    const editingId = this.editingItemId();
    const request =
      editingId === null
        ? this.inventoryService.create(payload)
        : this.inventoryService.update(editingId, payload);

    request
      .pipe(finalize(() => this.isSaving.set(false)))
      .subscribe({
        next: (item) => {
          this.items.update((items) =>
            [...items.filter((current) => current.id !== item.id), item].sort(
              (left, right) => left.name.localeCompare(right.name)
            )
          );
          this.editingItemId.set(null);
          this.inventoryForm.reset(this.emptyFormValue());
          this.successMessage.set(
            editingId === null
              ? 'El producto se registró correctamente.'
              : 'El producto se actualizó correctamente.'
          );
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  askToDelete(itemId: number): void {
    this.pendingDeleteId.update((pendingId) => (pendingId === itemId ? null : itemId));
    this.errorMessage.set(null);
  }

  deleteItem(item: InventoryRecord): void {
    if (this.isSaving() || this.deletingItemId() !== null) {
      return;
    }

    this.errorMessage.set(null);
    this.deletingItemId.set(item.id);

    this.inventoryService
      .delete(item.id)
      .pipe(finalize(() => this.deletingItemId.set(null)))
      .subscribe({
        next: () => {
          this.items.update((items) => items.filter((current) => current.id !== item.id));
          if (this.editingItemId() === item.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('El producto se eliminó correctamente.');
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  private emptyFormValue(): InventoryPayload {
    return {
      name: '',
      sku: '',
      category: '',
      description: '',
      quantity: 0,
      min_stock: 0,
      unit_price: 0,
    };
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
    return 'No se pudo guardar el producto. Revisá los datos e intentá nuevamente.';
  }
}
