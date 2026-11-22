import { CurrencyPipe, DatePipe } from '@angular/common';
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
import { SalePayload, SaleRecord, SalesService } from './sales.service';

interface SaleFormControls {
  customer_name: FormControl<string>;
  product_name: FormControl<string>;
  quantity: FormControl<number | null>;
  unit_price: FormControl<number | null>;
}

interface SaleFormValue {
  customer_name: string;
  product_name: string;
  quantity: number | null;
  unit_price: number | null;
}

@Component({
  imports: [CurrencyPipe, DatePipe, ReactiveFormsModule],
  selector: 'app-sales',
  templateUrl: './sales.html',
})
export class Sales implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly salesService = inject(SalesService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('saleFormElement')
  private readonly saleFormElement?: ElementRef<HTMLElement>;

  readonly sales = signal<SaleRecord[]>([]);
  readonly editingSaleId = signal<number | null>(null);
  readonly pendingDeleteId = signal<number | null>(null);
  readonly deletingSaleId = signal<number | null>(null);
  readonly isLoading = signal(false);
  readonly isSaving = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly saleForm: FormGroup<SaleFormControls> = this.fb.group({
    customer_name: this.fb.nonNullable.control('', Validators.maxLength(120)),
    product_name: this.fb.nonNullable.control('', [
      Validators.required,
      Validators.pattern(/\S/),
      Validators.maxLength(120),
    ]),
    quantity: this.fb.control<number | null>(null, [
      Validators.required,
      Validators.min(1),
      Validators.max(2147483647),
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

  loadSales(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.salesService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (sales) => this.sales.set(sales),
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

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

  cancelEdit(): void {
    this.editingSaleId.set(null);
    this.saleForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  previewTotal(): number | null {
    const { quantity, unit_price } = this.saleForm.getRawValue();
    return quantity !== null && unit_price !== null && quantity > 0 && unit_price >= 0
      ? quantity * unit_price
      : null;
  }

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
        next: (sale) => {
          this.sales.update((sales) =>
            editingId === null
              ? [sale, ...sales]
              : sales.map((item) => (item.id === sale.id ? sale : item))
          );
          this.editingSaleId.set(null);
          this.saleForm.reset(this.emptyFormValue());
          this.successMessage.set(
            editingId === null
              ? 'La venta se registró correctamente.'
              : 'La venta se actualizó correctamente.'
          );
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  askToDelete(saleId: number): void {
    this.pendingDeleteId.update((pendingId) =>
      pendingId === saleId ? null : saleId
    );
    this.errorMessage.set(null);
  }

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
          this.sales.update((sales) => sales.filter((item) => item.id !== sale.id));
          if (this.editingSaleId() === sale.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('La venta se eliminó correctamente.');
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
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
    return 'No se pudo guardar la venta. Revisá los datos e intentá nuevamente.';
  }
}
