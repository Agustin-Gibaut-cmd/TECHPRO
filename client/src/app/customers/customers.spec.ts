import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { CustomerRecord } from './customers.service';
import { Customers } from './customers';

describe('Customers', () => {
  let fixture: ComponentFixture<Customers>;
  let component: Customers;
  let httpMock: HttpTestingController;

  const customersUrl = `${environment.apiUrl}/customers/`;
  const customer: CustomerRecord = {
    id: 8,
    name: 'Ana Pérez',
    phone: '+54 11 1234-5678',
    email: 'ana@example.com',
    address: 'Av. Siempre Viva 123',
    notes: '',
    created_at: '2026-11-21T12:00:00Z',
    updated_at: '2026-11-21T12:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Customers],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Customers);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('creates a customer with CSRF protection and adds the server response', () => {
    component.customerForm.setValue({
      name: '  Ana Pérez  ',
      phone: ' +54 11 1234-5678 ',
      email: ' ANA@EXAMPLE.COM ',
      address: '',
      notes: '',
    });

    component.saveCustomer();

    const csrfRequest = httpMock.expectOne(`${environment.apiUrl}/auth/csrf/`);
    csrfRequest.flush({ csrfToken: 'csrf-token' });

    const request = httpMock.expectOne(customersUrl);
    expect(request.request.method).toBe('POST');
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    expect(request.request.body).toEqual({
      name: customer.name,
      phone: customer.phone,
      email: customer.email,
      address: '',
      notes: '',
    });
    request.flush(customer);

    expect(component.customers()).toEqual([customer]);
    expect(component.successMessage()).toContain('correctamente');
  });
});
