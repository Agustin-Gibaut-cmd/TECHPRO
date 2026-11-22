import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, switchMap } from 'rxjs';
import { AuthService } from '../auth.service';
import { environment } from '../../environments/environment';

export interface CustomerRecord {
  readonly id: number;
  readonly name: string;
  readonly phone: string;
  readonly email: string;
  readonly address: string;
  readonly notes: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export type CustomerPayload = Pick<
  CustomerRecord,
  'name' | 'phone' | 'email' | 'address' | 'notes'
>;

const CUSTOMERS_URL = `${environment.apiUrl}/customers/`;

@Injectable({ providedIn: 'root' })
export class CustomersService {
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);

  list(): Observable<CustomerRecord[]> {
    return this.http.get<CustomerRecord[]>(CUSTOMERS_URL, { withCredentials: true });
  }

  create(payload: CustomerPayload): Observable<CustomerRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.post<CustomerRecord>(CUSTOMERS_URL, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  update(id: number, payload: CustomerPayload): Observable<CustomerRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.patch<CustomerRecord>(`${CUSTOMERS_URL}${id}/`, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  delete(id: number): Observable<void> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.delete<void>(`${CUSTOMERS_URL}${id}/`, {
          headers,
          withCredentials: true,
        })
      )
    );
  }
}
