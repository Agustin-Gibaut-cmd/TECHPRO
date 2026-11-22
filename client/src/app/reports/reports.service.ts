import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface MonthlySales {
  readonly month: string;
  readonly sales_count: number;
  readonly revenue: string;
}

export interface ProductSales {
  readonly product_name: string;
  readonly units_sold: number;
  readonly revenue: string;
}

export interface DashboardReport {
  readonly sales_count: number;
  readonly total_revenue: string;
  readonly average_sale: string;
  readonly monthly_sales: MonthlySales[];
  readonly top_products: ProductSales[];
  readonly customer_count: number;
  readonly supplier_count: number;
  readonly inventory_count: number;
  readonly inventory_units: number;
  readonly low_stock_count: number;
  readonly inventory_value: string;
  readonly repair_count: number;
  readonly open_repair_count: number;
}

const REPORTS_URL = `${environment.apiUrl}/reports/summary/`;

@Injectable({ providedIn: 'root' })
export class ReportsService {
  private readonly http = inject(HttpClient);

  getSummary(): Observable<DashboardReport> {
    return this.http.get<DashboardReport>(REPORTS_URL, { withCredentials: true });
  }
}
