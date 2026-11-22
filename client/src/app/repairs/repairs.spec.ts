import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { RepairRecord } from './repairs.service';
import { Repairs } from './repairs';

describe('Repairs', () => {
  let fixture: ComponentFixture<Repairs>;
  let component: Repairs;
  let httpMock: HttpTestingController;

  const url = `${environment.apiUrl}/repairs/`;
  const repair: RepairRecord = {
    id: 41,
    customer_name: 'Ana Pérez',
    customer_phone: '+54 11 1234-5678',
    device_type: 'Notebook',
    device_model: 'ThinkPad T14',
    serial_number: 'SN-123456',
    issue_description: 'No enciende.',
    status: 'received',
    created_at: '2026-11-21T12:00:00Z',
    updated_at: '2026-11-21T12:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Repairs],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Repairs);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('loads the repair table from the authenticated API', () => {
    fixture.detectChanges();

    const request = httpMock.expectOne(url);
    expect(request.request.method).toBe('GET');
    expect(request.request.withCredentials).toBe(true);
    request.flush([repair]);

    expect(fixture.componentInstance.repairs()).toEqual([repair]);
  });

  it('submits validated form data and adds the server response to the table', () => {
    component.repairForm.setValue({
      customer_name: repair.customer_name,
      customer_phone: repair.customer_phone,
      device_type: repair.device_type,
      device_model: repair.device_model,
      serial_number: repair.serial_number,
      issue_description: repair.issue_description,
      status: repair.status,
    });

    component.saveRepair();

    const csrfRequest = httpMock.expectOne(`${environment.apiUrl}/auth/csrf/`);
    expect(csrfRequest.request.method).toBe('GET');
    expect(csrfRequest.request.withCredentials).toBe(true);
    csrfRequest.flush({ csrfToken: 'csrf-token' });

    const request = httpMock.expectOne(url);
    expect(request.request.method).toBe('POST');
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    expect(request.request.body).toEqual(component.repairForm.getRawValue());
    request.flush(repair);

    expect(component.repairs()).toEqual([repair]);
    expect(component.successMessage()).toContain('correctamente');
  });

  it('updates a repair in place without leaving the section', () => {
    const updatedRepair: RepairRecord = {
      ...repair,
      issue_description: 'Se reemplazó el conector de carga.',
      status: 'completed',
    };
    component.repairs.set([repair]);
    component.editRepair(repair);
    component.repairForm.controls.issue_description.setValue(
      updatedRepair.issue_description
    );
    component.repairForm.controls.status.setValue(updatedRepair.status);

    component.saveRepair();

    const csrfRequest = httpMock.expectOne(`${environment.apiUrl}/auth/csrf/`);
    csrfRequest.flush({ csrfToken: 'csrf-token' });

    const request = httpMock.expectOne(`${url}${repair.id}/`);
    expect(request.request.method).toBe('PATCH');
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    request.flush(updatedRepair);

    expect(component.editingRepairId()).toBeNull();
    expect(component.repairs()).toEqual([updatedRepair]);
    expect(component.successMessage()).toContain('actualizó');
  });
});
