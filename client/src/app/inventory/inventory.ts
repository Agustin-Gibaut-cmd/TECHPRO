import { CurrencyPipe } from '@angular/common';
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
  InventoryPayload,
  InventoryRecord,
  InventoryService,
} from './inventory.service';

interface InventoryFormControls {
  readonly name: FormControl<string>;
  readonly sku: FormControl<string>;
  readonly category: FormControl<string>;
  readonly description: FormControl<string>;
  readonly quantity: FormControl<number>;
  readonly min_stock: FormControl<number>;
  readonly unit_price: FormControl<number>;
}

/**
 * Componente para el control de inventario, existencias y precios del taller.
 */
@Component({
  imports: [CurrencyPipe, ReactiveFormsModule],
  selector: 'app-inventory',
  templateUrl: './inventory.html',
})
export class Inventory implements OnInit {
  private readonly fb: FormBuilder = inject(FormBuilder);
  private readonly inventoryService: InventoryService = inject(InventoryService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('inventoryFormElement')
  private readonly inventoryFormElement?: ElementRef<HTMLElement>;

  readonly items: WritableSignal<InventoryRecord[]> = signal<InventoryRecord[]>([]);
  readonly editingItemId: WritableSignal<number | null> = signal<number | null>(null);
  readonly pendingDeleteId: WritableSignal<number | null> = signal<number | null>(null);
  readonly deletingItemId: WritableSignal<number | null> = signal<number | null>(null);
  readonly isLoading: WritableSignal<boolean> = signal<boolean>(false);
  readonly isSaving: WritableSignal<boolean> = signal<boolean>(false);
  readonly errorMessage: WritableSignal<string | null> = signal<string | null>(null);
  readonly successMessage: WritableSignal<string | null> = signal<string | null>(null);

  readonly inventoryForm: FormGroup<InventoryFormControls> = this.fb.nonNullable.group<InventoryFormControls>({
    name: this.fb.nonNullable.control('', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(120)]),
    sku: this.fb.nonNullable.control('', [Validators.required, Validators.pattern(/\S/), Validators.maxLength(40)]),
    category: this.fb.nonNullable.control('', [Validators.maxLength(80)]),
    description: this.fb.nonNullable.control('', [Validators.maxLength(1000)]),
    quantity: this.fb.nonNullable.control(0, [Validators.required, Validators.min(0), Validators.pattern(/^\d+$/)]),
    min_stock: this.fb.nonNullable.control(0, [Validators.required, Validators.min(0), Validators.pattern(/^\d+$/)]),
    unit_price: this.fb.nonNullable.control(0, [Validators.required, Validators.min(0), Validators.pattern(/^\d+(\.\d{1,2})?$/)]),
  });

  ngOnInit(): void {
    this.loadItems();
  }

  /** Carga la lista completa de artículos en stock. */
  loadItems(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.inventoryService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (items: InventoryRecord[]) => this.items.set(items),
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Carga los datos de un artículo para su edición. */
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

  /** Cancela la edición y reinicia los valores del formulario. */
  cancelEdit(): void {
    this.editingItemId.set(null);
    this.inventoryForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  /** Registra un nuevo producto o actualiza el existente en inventario. */
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
        next: (item: InventoryRecord) => {
          this.items.update((current: InventoryRecord[]) =>
            [...current.filter((it: InventoryRecord) => it.id !== item.id), item].sort(
              (a: InventoryRecord, b: InventoryRecord) => a.name.localeCompare(b.name)
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
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Muestra u oculta la confirmación de borrado. */
  askToDelete(itemId: number): void {
    this.pendingDeleteId.update((id: number | null) => (id === itemId ? null : itemId));
    this.errorMessage.set(null);
  }

  /** Elimina el artículo del inventario. */
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
          this.items.update((current: InventoryRecord[]) => current.filter((it: InventoryRecord) => it.id !== item.id));
          if (this.editingItemId() === item.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('El producto se eliminó correctamente.');
        },
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
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
}
