import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { InventoryRecord } from './inventory.service';
import { Inventory } from './inventory';

describe('Inventory', () => {
  let fixture: ComponentFixture<Inventory>;
  let component: Inventory;
  let httpMock: HttpTestingController;

  const inventoryUrl = `${environment.apiUrl}/inventory/`;
  const item: InventoryRecord = {
    id: 17,
    name: 'Cargador USB-C',
    sku: 'CARGADOR-001',
    category: 'Accesorios',
    description: 'Cargador de 65 W.',
    quantity: 8,
    min_stock: 2,
    unit_price: '12500.00',
    created_at: '2026-11-21T12:00:00Z',
    updated_at: '2026-11-21T12:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Inventory],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Inventory);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('creates inventory items with normalized SKU and CSRF protection', () => {
    component.inventoryForm.setValue({
      name: item.name,
      sku: ' cargador-001 ',
      category: item.category,
      description: item.description,
      quantity: item.quantity,
      min_stock: item.min_stock,
      unit_price: 12500,
    });

    component.saveItem();

    const csrfRequest = httpMock.expectOne(`${environment.apiUrl}/auth/csrf/`);
    csrfRequest.flush({ csrfToken: 'csrf-token' });

    const request = httpMock.expectOne(inventoryUrl);
    expect(request.request.method).toBe('POST');
    expect(request.request.withCredentials).toBe(true);
    expect(request.request.headers.get('X-CSRFToken')).toBe('csrf-token');
    expect(request.request.body).toEqual({
      name: item.name,
      sku: item.sku,
      category: item.category,
      description: item.description,
      quantity: item.quantity,
      min_stock: item.min_stock,
      unit_price: 12500,
    });
    request.flush(item);

    expect(component.items()).toEqual([item]);
    expect(component.successMessage()).toContain('correctamente');
  });
});
