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
  RepairPayload,
  RepairRecord,
  RepairStatus,
  RepairsService,
} from './repairs.service';

interface RepairFormControls {
  readonly customer_name: FormControl<string>;
  readonly customer_phone: FormControl<string>;
  readonly device_type: FormControl<string>;
  readonly device_model: FormControl<string>;
  readonly serial_number: FormControl<string>;
  readonly issue_description: FormControl<string>;
  readonly status: FormControl<RepairStatus>;
}

/**
 * Componente para administración del ciclo de vida de órdenes de servicio técnico.
 */
@Component({
  imports: [DatePipe, ReactiveFormsModule],
  selector: 'app-repairs',
  templateUrl: './repairs.html',
})
export class Repairs implements OnInit {
  private readonly fb: FormBuilder = inject(FormBuilder);
  private readonly repairsService: RepairsService = inject(RepairsService);

  @Output() readonly back = new EventEmitter<void>();
  @ViewChild('repairFormSection') private readonly repairFormSection?: ElementRef<HTMLElement>;

  readonly repairs: WritableSignal<RepairRecord[]> = signal<RepairRecord[]>([]);
  readonly editingRepairId: WritableSignal<number | null> = signal<number | null>(null);
  readonly pendingDeleteId: WritableSignal<number | null> = signal<number | null>(null);
  readonly deletingRepairId: WritableSignal<number | null> = signal<number | null>(null);
  readonly isLoading: WritableSignal<boolean> = signal<boolean>(false);
  readonly isSaving: WritableSignal<boolean> = signal<boolean>(false);
  readonly errorMessage: WritableSignal<string | null> = signal<string | null>(null);
  readonly successMessage: WritableSignal<string | null> = signal<string | null>(null);

  readonly statuses: ReadonlyArray<{ readonly value: RepairStatus; readonly label: string }> = [
    { value: 'received', label: 'Recibido' },
    { value: 'diagnosing', label: 'En diagnóstico' },
    { value: 'in_progress', label: 'En reparación' },
    { value: 'waiting_parts', label: 'Esperando repuesto' },
    { value: 'completed', label: 'Listo' },
    { value: 'delivered', label: 'Entregado' },
  ];

  readonly statusLabels: Readonly<Record<RepairStatus, string>> = {
    received: 'Recibido',
    diagnosing: 'En diagnóstico',
    in_progress: 'En reparación',
    waiting_parts: 'Esperando repuesto',
    completed: 'Listo',
    delivered: 'Entregado',
  };

  readonly repairForm: FormGroup<RepairFormControls> = this.fb.nonNullable.group<RepairFormControls>({
    customer_name: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(120)]),
    customer_phone: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(32)]),
    device_type: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(80)]),
    device_model: this.fb.nonNullable.control('', [Validators.maxLength(100)]),
    serial_number: this.fb.nonNullable.control('', [Validators.maxLength(100)]),
    issue_description: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(2000)]),
    status: this.fb.nonNullable.control<RepairStatus>('received', Validators.required),
  });

  ngOnInit(): void {
    this.loadRepairs();
  }

  /** Carga todas las órdenes de reparación registradas. */
  loadRepairs(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.repairsService
      .list()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (items: RepairRecord[]) => this.repairs.set(items),
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Rellena el formulario con los datos de la orden a editar. */
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

  /** Cancela la edición y reinicia los controles. */
  cancelEdit(): void {
    this.editingRepairId.set(null);
    this.repairForm.reset(this.emptyFormValue());
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }

  /** Guarda los cambios o da de alta una nueva reparación técnica. */
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
        next: (repair: RepairRecord) => {
          if (editingId === null) {
            this.repairs.update((items: RepairRecord[]) => [repair, ...items]);
          } else {
            this.repairs.update((items: RepairRecord[]) =>
              items.map((item: RepairRecord) => (item.id === repair.id ? repair : item))
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
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
      });
  }

  /** Solicita confirmación para borrar una reparación. */
  askToDelete(repairId: number): void {
    this.pendingDeleteId.update((id: number | null) => (id === repairId ? null : repairId));
    this.errorMessage.set(null);
  }

  /** Elimina definitivamente la reparación del sistema. */
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
          this.repairs.update((items: RepairRecord[]) => items.filter((it: RepairRecord) => it.id !== repair.id));
          if (this.editingRepairId() === repair.id) {
            this.cancelEdit();
          }
          this.pendingDeleteId.set(null);
          this.successMessage.set('La reparación se eliminó correctamente.');
        },
        error: (err: unknown) => this.errorMessage.set(extractErrorMessage(err)),
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
}
