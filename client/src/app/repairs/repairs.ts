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
  RepairPayload,
  RepairRecord,
  RepairStatus,
  RepairsService,
} from './repairs.service';

interface RepairFormControls {
  customer_name: FormControl<string>;
  customer_phone: FormControl<string>;
  device_type: FormControl<string>;
  device_model: FormControl<string>;
  serial_number: FormControl<string>;
  issue_description: FormControl<string>;
  status: FormControl<RepairStatus>;
}

@Component({
  imports: [DatePipe, ReactiveFormsModule],
  selector: 'app-repairs',
  templateUrl: './repairs.html',
})
export class Repairs implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly repairsService = inject(RepairsService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('repairFormSection') private readonly repairFormSection?: ElementRef<HTMLElement>;

  readonly repairs = signal<RepairRecord[]>([]);
  readonly editingRepairId = signal<number | null>(null);
  readonly pendingDeleteId = signal<number | null>(null);
  readonly deletingRepairId = signal<number | null>(null);
  readonly isLoading = signal(false);
  readonly isSaving = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly statuses: ReadonlyArray<{ value: RepairStatus; label: string }> = [
    { value: 'received', label: 'Recibido' },
    { value: 'diagnosing', label: 'En diagnóstico' },
    { value: 'in_progress', label: 'En reparación' },
    { value: 'waiting_parts', label: 'Esperando repuesto' },
    { value: 'completed', label: 'Listo' },
    { value: 'delivered', label: 'Entregado' },
  ];
  readonly statusLabels: Record<RepairStatus, string> = {
    received: 'Recibido',
    diagnosing: 'En diagnóstico',
    in_progress: 'En reparación',
    waiting_parts: 'Esperando repuesto',
    completed: 'Listo',
    delivered: 'Entregado',
  };

  readonly repairForm: FormGroup<RepairFormControls> = this.fb.nonNullable.group({
    customer_name: ['', [Validators.required, Validators.maxLength(120)]],
    customer_phone: ['', [Validators.required, Validators.maxLength(32)]],
    device_type: ['', [Validators.required, Validators.maxLength(80)]],
    device_model: ['', [Validators.maxLength(100)]],
    serial_number: ['', [Validators.maxLength(100)]],
    issue_description: ['', [Validators.required, Validators.maxLength(2000)]],
    status: this.fb.nonNullable.control<RepairStatus>('received', Validators.required),
  });

  ngOnInit(): void {
    this.loadRepairs();
  }

  loadRepairs(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.repairsService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (repairs) => this.repairs.set(repairs),
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  editRepair(repair: RepairRecord): void {
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.pendingDeleteId.set(null);
    this.editingRepairId.set(repair.id);
    this.repairForm.setValue({
      customer_name: repair.customer_name,
      customer_phone: repair.customer_phone,
      device_type: repair.device_type,
      device_model: repair.device_model,
      serial_number: repair.serial_number,
      issue_description: repair.issue_description,
      status: repair.status,
    });
    this.repairFormSection?.nativeElement.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
  }

  cancelEdit(): void {
    this.editingRepairId.set(null);
    this.repairForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  saveRepair(): void {
    if (this.isSaving() || this.deletingRepairId() !== null) {
      return;
    }

    if (this.repairForm.invalid) {
      this.repairForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.isSaving.set(true);

    const payload: RepairPayload = this.repairForm.getRawValue();
    const editingId = this.editingRepairId();
    const request =
      editingId === null
        ? this.repairsService.create(payload)
        : this.repairsService.update(editingId, payload);

    request
      .pipe(finalize(() => this.isSaving.set(false)))
      .subscribe({
        next: (repair) => {
          if (editingId === null) {
            this.repairs.update((repairs) => [repair, ...repairs]);
          } else {
            this.repairs.update((repairs) =>
              repairs.map((item) => (item.id === repair.id ? repair : item))
            );
          }

          this.editingRepairId.set(null);
          this.repairForm.reset(this.emptyFormValue());
          this.successMessage.set(
            editingId === null
              ? 'La reparación se registró correctamente.'
              : 'La reparación se actualizó correctamente.'
          );
        },
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  askToDelete(repairId: number): void {
    this.pendingDeleteId.update((pendingId) =>
      pendingId === repairId ? null : repairId
    );
    this.errorMessage.set(null);
  }

  deleteRepair(repair: RepairRecord): void {
    if (this.isSaving() || this.deletingRepairId() !== null) {
      return;
    }

    this.errorMessage.set(null);
    this.deletingRepairId.set(repair.id);

    this.repairsService
      .delete(repair.id)
      .pipe(finalize(() => this.deletingRepairId.set(null)))
      .subscribe({
        next: () => {
          this.repairs.update((repairs) =>
            repairs.filter((item) => item.id !== repair.id)
          );
          if (this.editingRepairId() === repair.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('La reparación se eliminó correctamente.');
        },
        error: (error: unknown) =>
          this.errorMessage.set(
            this.getErrorMessage(
              error,
              'No se pudo eliminar la reparación. Intentá nuevamente.'
            )
          ),
      });
  }

  private emptyFormValue(): RepairPayload {
    return {
      customer_name: '',
      customer_phone: '',
      device_type: '',
      device_model: '',
      serial_number: '',
      issue_description: '',
      status: 'received',
    };
  }

  private getErrorMessage(
    error: unknown,
    fallback = 'No se pudo guardar la reparación. Revisá los datos e intentá nuevamente.'
  ): string {
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

    return fallback;
  }
}
