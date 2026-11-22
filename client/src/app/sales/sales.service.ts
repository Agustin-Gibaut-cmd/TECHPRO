import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, switchMap } from 'rxjs';
import { AuthService } from '../auth.service';
import { environment } from '../../environments/environment';

export interface SaleRecord {
  readonly id: number;
  readonly customer_name: string;
  readonly product_name: string;
  readonly quantity: number;
  readonly unit_price: string;
  readonly total: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface SalePayload {
  readonly customer_name: string;
  readonly product_name: string;
  readonly quantity: number;
  readonly unit_price: number;
}

const SALES_URL = `${environment.apiUrl}/sales/`;

@Injectable({ providedIn: 'root' })
export class SalesService {
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);

  list(): Observable<SaleRecord[]> {
    return this.http.get<SaleRecord[]>(SALES_URL, { withCredentials: true });
  }

  create(payload: SalePayload): Observable<SaleRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.post<SaleRecord>(SALES_URL, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  update(id: number, payload: SalePayload): Observable<SaleRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.patch<SaleRecord>(`${SALES_URL}${id}/`, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  delete(id: number): Observable<void> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.delete<void>(`${SALES_URL}${id}/`, {
          headers,
          withCredentials: true,
        })
      )
    );
  }
}
