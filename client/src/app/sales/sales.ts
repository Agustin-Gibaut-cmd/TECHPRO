import { CurrencyPipe, DatePipe } from '@angular/common';
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
import { SalePayload, SaleRecord, SalesService } from './sales.service';

interface SaleFormControls {
  readonly customer_name: FormControl<string>;
  readonly product_name: FormControl<string>;
  readonly quantity: FormControl<number | null>;
  readonly unit_price: FormControl<number | null>;
}

interface SaleFormValue {
  readonly customer_name: string;
  readonly product_name: string;
  readonly quantity: number | null;
  readonly unit_price: number | null;
}

/**
 * Componente para el registro, consulta y anulación de ventas del taller.
 */
@Component({
  imports: [CurrencyPipe, DatePipe, ReactiveFormsModule],
  selector: 'app-sales',
  templateUrl: './sales.html',
})
export class Sales implements OnInit {
  private readonly fb: FormBuilder = inject(FormBuilder);
  private readonly salesService: SalesService = inject(SalesService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('saleFormElement')
  private readonly saleFormElement?: ElementRef<HTMLElement>;

  readonly sales: WritableSignal<SaleRecord[]> = signal<SaleRecord[]>([]);
  readonly editingSaleId: WritableSignal<number | null> = signal<number | null>(null);
  readonly pendingDeleteId: WritableSignal<number | null> = signal<number | null>(null);
  readonly deletingSaleId: WritableSignal<number | null> = signal<number | null>(null);
  readonly isLoading: WritableSignal<boolean> = signal<boolean>(false);
  readonly isSaving: WritableSignal<boolean> = signal<boolean>(false);
  readonly errorMessage: WritableSignal<string | null> = signal<string | null>(null);
  readonly successMessage: WritableSignal<string | null> = signal<string | null>(null);

  readonly saleForm: FormGroup<SaleFormControls> = this.fb.group<SaleFormControls>({
    customer_name: this.fb.nonNullable.control('', Validators.maxLength(120)),
    product_name: this.fb.nonNullable.control('', [
      Validators.required,
      Validators.pattern(/\S/),
      Validators.maxLength(120),
    ]),
    quantity: this.fb.control<number | null>(null, [
      Validators.required,
      Validators.min(1),
      Validators.max(2_147_483_647),
      Validators.pattern(/^[1-9]\d*$/),
    ]),
    unit_price: this.fb.control<number | null>(null, [
      Validators.required,
      Validators.min(0),
      Validators.pattern(/^\d+(\.\d{1,2})?$/),
    ]),
  });

  ngOnInit(): void {
    this.loadSales();
  }

  /** Carga la lista cronológica de ventas desde la API. */
  loadSales(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.salesService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (items: SaleRecord[]) => this.sales.set(items),
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Rellena el formulario con la venta a editar. */
  editSale(sale: SaleRecord): void {
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.pendingDeleteId.set(null);
    this.editingSaleId.set(sale.id);
    this.saleForm.setValue({
      customer_name: sale.customer_name,
      product_name: sale.product_name,
      quantity: sale.quantity,
      unit_price: Number(sale.unit_price),
    });
    this.saleFormElement?.nativeElement.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  }

  /** Cancela la edición activa. */
  cancelEdit(): void {
    this.editingSaleId.set(null);
    this.saleForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  /** Calcula la previsualización del importe total en tiempo real. */
  previewTotal(): number | null {
    const { quantity, unit_price } = this.saleForm.getRawValue();
    return quantity !== null && unit_price !== null && quantity > 0 && unit_price >= 0
      ? quantity * unit_price
      : null;
  }

  /** Guarda la venta en el servidor. */
  saveSale(): void {
    if (this.isSaving() || this.deletingSaleId() !== null) {
      return;
    }

    if (this.saleForm.invalid) {
      this.saleForm.markAllAsTouched();
      return;
    }

    const formValue = this.saleForm.getRawValue();
    if (formValue.quantity === null || formValue.unit_price === null) {
      this.saleForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.isSaving.set(true);

    const payload: SalePayload = {
      customer_name: formValue.customer_name.trim(),
      product_name: formValue.product_name.trim(),
      quantity: formValue.quantity,
      unit_price: formValue.unit_price,
    };
    const editingId = this.editingSaleId();
    const request =
      editingId === null
        ? this.salesService.create(payload)
        : this.salesService.update(editingId, payload);

    request
      .pipe(finalize(() => this.isSaving.set(false)))
      .subscribe({
        next: (sale: SaleRecord) => {
          this.sales.update((items: SaleRecord[]) =>
            editingId === null
              ? [sale, ...items]
              : items.map((item: SaleRecord) => (item.id === sale.id ? sale : item))
          );
          this.editingSaleId.set(null);
          this.saleForm.reset(this.emptyFormValue());
          this.successMessage.set(
            editingId === null
              ? 'La venta se registró correctamente.'
              : 'La venta se actualizó correctamente.'
          );
        },
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Solicita confirmación para eliminar una venta. */
  askToDelete(saleId: number): void {
    this.pendingDeleteId.update((id: number | null) => (id === saleId ? null : saleId));
    this.errorMessage.set(null);
  }

  /** Elimina el registro de venta seleccionado. */
  deleteSale(sale: SaleRecord): void {
    if (this.isSaving() || this.deletingSaleId() !== null) {
      return;
    }

    this.errorMessage.set(null);
    this.deletingSaleId.set(sale.id);

    this.salesService
      .delete(sale.id)
      .pipe(finalize(() => this.deletingSaleId.set(null)))
      .subscribe({
        next: () => {
          this.sales.update((items: SaleRecord[]) => items.filter((item: SaleRecord) => item.id !== sale.id));
          if (this.editingSaleId() === sale.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('La venta se eliminó correctamente.');
        },
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  private emptyFormValue(): SaleFormValue {
    return {
      customer_name: '',
      product_name: '',
      quantity: null,
      unit_price: null,
    };
  }
}
