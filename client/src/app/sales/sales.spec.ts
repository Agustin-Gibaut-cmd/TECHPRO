import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { SaleRecord } from './sales.service';
import { Sales } from './sales';

describe('Sales', () => {
  let fixture: ComponentFixture<Sales>;
  let component: Sales;
  let httpMock: HttpTestingController;

  const salesUrl = `${environment.apiUrl}/sales/`;
  const sale: SaleRecord = {
    id: 21,
    customer_name: 'Ana Pérez',
    product_name: 'Cargador USB-C',
    quantity: 2,
    unit_price: '12500.00',
    total: '25000.00',
    created_at: '2026-11-21T12:00:00Z',
    updated_at: '2026-11-21T12:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Sales],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Sales);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('creates a sale using CSRF and shows the server-calculated total', () => {
    component.saleForm.setValue({
      customer_name: sale.customer_name,
      product_name: sale.product_name,
      quantity: sale.quantity,
      unit_price: 12500,
    });

    expect(component.previewTotal()).toBe(25000);
    component.saveSale();

    const csrfRequest = httpMock.expectOne(`${environment.apiUrl}/auth/csrf/`);
    csrfRequest.flush({ csrfToken: 'csrf-token' });

    const request = httpMock.expectOne(salesUrl);
    expect(request.request.method).toBe('POST');
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    expect(request.request.body).toEqual({
      customer_name: sale.customer_name,
      product_name: sale.product_name,
      quantity: sale.quantity,
      unit_price: 12500,
    });
    request.flush(sale);

    expect(component.sales()).toEqual([sale]);
    expect(component.successMessage()).toContain('correctamente');
  });
});
