import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, switchMap } from 'rxjs';
import { AuthService } from '../auth.service';
import { environment } from '../../environments/environment';

export type RepairStatus =
  | 'received'
  | 'diagnosing'
  | 'in_progress'
  | 'waiting_parts'
  | 'completed'
  | 'delivered';

export interface RepairRecord {
  readonly id: number;
  readonly customer_name: string;
  readonly customer_phone: string;
  readonly device_type: string;
  readonly device_model: string;
  readonly serial_number: string;
  readonly issue_description: string;
  readonly status: RepairStatus;
  readonly created_at: string;
  readonly updated_at: string;
}

export type RepairPayload = Pick<
  RepairRecord,
  | 'customer_name'
  | 'customer_phone'
  | 'device_type'
  | 'device_model'
  | 'serial_number'
  | 'issue_description'
  | 'status'
>;

const REPAIRS_URL = `${environment.apiUrl}/repairs/`;

@Injectable({ providedIn: 'root' })
export class RepairsService {
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);

  list(): Observable<RepairRecord[]> {
    return this.http.get<RepairRecord[]>(REPAIRS_URL, { withCredentials: true });
  }

  create(payload: RepairPayload): Observable<RepairRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.post<RepairRecord>(REPAIRS_URL, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }

  update(id: number, payload: RepairPayload): Observable<RepairRecord> {
    return this.authService.getCsrfHeaders().pipe(
      switchMap((headers) =>
        this.http.patch<RepairRecord>(`${REPAIRS_URL}${id}/`, payload, {
          headers,
          withCredentials: true,
        })
      )
    );
  }
}
