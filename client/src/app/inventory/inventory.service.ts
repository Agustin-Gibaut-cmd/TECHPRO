import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, switchMap } from 'rxjs';
import { AuthService } from '../auth.service';
import { environment } from '../../environments/environment';

export interface InventoryRecord {
  readonly id: number;
  readonly name: string;
  readonly sku: string;
  readonly category: string;
  readonly description: string;
  readonly quantity: number;
  readonly min_stock: number;
  readonly unit_price: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface InventoryPayload {
  readonly name: string;
  readonly sku: string;
  readonly category: string;
  readonly description: string;
  readonly quantity: number;
  readonly min_stock: number;
  readonly unit_price: number;
}

const INVENTORY_URL = `${environment.apiUrl}/inventory/`;

@Injectable({ providedIn: 'root' })
export class InventoryService {
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);

  list(): Observable<InventoryRecord[]> {
    return this.http.get<InventoryRecord[]>(INVENTORY_URL, { withCredentials: true });
  }

  create(payload: InventoryPayload): Observable<InventoryRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.post<InventoryRecord>(INVENTORY_URL, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  update(id: number, payload: InventoryPayload): Observable<InventoryRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.patch<InventoryRecord>(`${INVENTORY_URL}${id}/`, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  delete(id: number): Observable<void> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.delete<void>(`${INVENTORY_URL}${id}/`, {
          headers,
          withCredentials: true,
        })
      )
    );
  }
}
