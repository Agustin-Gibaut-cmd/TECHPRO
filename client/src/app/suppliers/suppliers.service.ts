import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, switchMap } from 'rxjs';
import { AuthService } from '../auth.service';
import { environment } from '../../environments/environment';

export interface SupplierRecord {
  readonly id: number;
  readonly name: string;
  readonly phone: string;
  readonly email: string;
  readonly address: string;
  readonly notes: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export type SupplierPayload = Pick<
  SupplierRecord,
  'name' | 'phone' | 'email' | 'address' | 'notes'
>;

const SUPPLIERS_URL = `${environment.apiUrl}/suppliers/`;

@Injectable({ providedIn: 'root' })
export class SuppliersService {
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);

  list(): Observable<SupplierRecord[]> {
    return this.http.get<SupplierRecord[]>(SUPPLIERS_URL, { withCredentials: true });
  }

  create(payload: SupplierPayload): Observable<SupplierRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.post<SupplierRecord>(SUPPLIERS_URL, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  update(id: number, payload: SupplierPayload): Observable<SupplierRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.patch<SupplierRecord>(`${SUPPLIERS_URL}${id}/`, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  delete(id: number): Observable<void> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.delete<void>(`${SUPPLIERS_URL}${id}/`, {
          headers,
          withCredentials: true,
        })
      )
    );
  }
}
