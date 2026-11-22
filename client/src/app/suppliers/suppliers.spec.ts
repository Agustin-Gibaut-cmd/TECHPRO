import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { SupplierRecord } from './suppliers.service';
import { Suppliers } from './suppliers';

describe('Suppliers', () => {
  let fixture: ComponentFixture<Suppliers>;
  let component: Suppliers;
  let httpMock: HttpTestingController;

  const suppliersUrl = `${environment.apiUrl}/suppliers/`;
  const supplier: SupplierRecord = {
    id: 12,
    name: 'Distribuidora Central',
    phone: '+54 11 2222-3333',
    email: 'ventas@central.example',
    address: 'Calle 123',
    notes: 'Entrega semanal.',
    created_at: '2026-11-21T12:00:00Z',
    updated_at: '2026-11-21T12:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Suppliers],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Suppliers);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('creates a supplier with CSRF protection and stores the server response', () => {
    component.supplierForm.setValue({
      name: supplier.name,
      phone: supplier.phone,
      email: supplier.email,
      address: supplier.address,
      notes: supplier.notes,
    });

    component.saveSupplier();

    const csrfRequest = httpMock.expectOne(`${environment.apiUrl}/auth/csrf/`);
    csrfRequest.flush({ csrfToken: 'csrf-token' });

    const request = httpMock.expectOne(suppliersUrl);
    expect(request.request.method).toBe('POST');
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    expect(request.request.body.name).toBe(supplier.name);
    request.flush(supplier);

    expect(component.suppliers()).toEqual([supplier]);
    expect(component.successMessage()).toContain('correctamente');
  });
});
