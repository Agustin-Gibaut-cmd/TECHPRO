import {
  CurrencyPipe,
  DecimalPipe,
  registerLocaleData,
} from '@angular/common';
import localeEsAr from '@angular/common/locales/es-AR';
import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  EventEmitter,
  OnInit,
  Output,
  inject,
  signal,
} from '@angular/core';
import { finalize } from 'rxjs';
import { DashboardReport, ReportsService } from './reports.service';

registerLocaleData(localeEsAr);

@Component({
  imports: [CurrencyPipe, DecimalPipe],
  selector: 'app-reports',
  templateUrl: './reports.html',
})
export class Reports implements OnInit {
  private readonly reportsService = inject(ReportsService);

  @Output() readonly back = new EventEmitter<void>();

  readonly report = signal<DashboardReport | null>(null);
  readonly isLoading = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly chartGuides = [0, 0.25, 0.5, 0.75, 1];
  readonly chartLeft = 88;
  readonly chartRight = 620;
  readonly chartTop = 20;
  readonly chartBottom = 180;
  readonly chartHeight = this.chartBottom - this.chartTop;
  readonly chartWidth = this.chartRight - this.chartLeft;

  ngOnInit(): void {
    this.loadReport();
  }

  loadReport(): void {
    this.errorMessage.set(null);
    this.isLoading.set(true);

    this.reportsService
      .getSummary()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (report) => this.report.set(report),
        error: (error: unknown) => this.errorMessage.set(this.getErrorMessage(error)),
      });
  }

  get maxMonthlyRevenue(): number {
    return Math.max(
      0,
      ...(this.report()?.monthly_sales ?? []).map((month) => Number(month.revenue))
    );
  }

  get maxProductUnits(): number {
    return Math.max(
      0,
      ...(this.report()?.top_products ?? []).map((product) => product.units_sold)
    );
  }

  chartGuideY(fraction: number): number {
    return this.chartBottom - fraction * this.chartHeight;
  }

  barWidth(count: number): number {
    if (count < 1) {
      return 0;
    }
    const columnWidth = this.chartWidth / count;
    return Math.min(72, columnWidth * 0.65);
  }

  barX(index: number, count: number): number {
    const columnWidth = this.chartWidth / count;
    return (
      this.chartLeft +
      index * columnWidth +
      (columnWidth - this.barWidth(count)) / 2
    );
  }

  barHeight(value: number, maximum: number): number {
    return maximum > 0
      ? Math.max(2, (value / maximum) * this.chartHeight)
      : 2;
  }

  barY(value: number, maximum: number): number {
    return this.chartBottom - this.barHeight(value, maximum);
  }

  toNumber(value: string): number {
    return Number(value);
  }

  shortProductName(value: string): string {
    return value.length > 12 ? `${value.slice(0, 11)}…` : value;
  }

  formatMonth(value: string): string {
    const [year, month] = value.split('-').map(Number);
    const date = new Date(Date.UTC(year, month - 1));
    return new Intl.DateTimeFormat('es-AR', {
      month: 'short',
      year: '2-digit',
      timeZone: 'UTC',
    }).format(date);
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
    return 'No se pudieron cargar los reportes. Intentá nuevamente.';
  }
}
