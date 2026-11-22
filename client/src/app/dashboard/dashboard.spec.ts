import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { Dashboard } from './dashboard';

describe('Dashboard', () => {
  let component: Dashboard;
  let fixture: ComponentFixture<Dashboard>;
  let httpMock: HttpTestingController;

  function openModule(
    title: string,
    endpoint: string,
    selector: string,
    response: object
  ): void {
    fixture.detectChanges();
    const moduleButton = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>(
        'section button'
      )
    ).find((button) => button.textContent?.includes(title));
    if (!(moduleButton instanceof HTMLButtonElement)) {
      throw new Error(`No se encontró el módulo ${title}.`);
    }

    moduleButton.click();
    fixture.detectChanges();

    const request = httpMock.expectOne(endpoint);
    expect(request.request.method).toBe('GET');
    request.flush(response);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector(selector)).toBeTruthy();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Dashboard],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Dashboard);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('opens the inventory section without navigating away', () => {
    fixture.detectChanges();
    const moduleButton = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>(
        'section button'
      )
    ).find((button) => button.textContent?.includes('Inventario'));
    if (!(moduleButton instanceof HTMLButtonElement)) {
      throw new Error('No se encontró el módulo de inventario.');
    }

    const router: Router = TestBed.inject(Router);
    const currentUrl: string = router.url;

    moduleButton.click();
    fixture.detectChanges();

    const inventoryRequest = httpMock.expectOne(`${environment.apiUrl}/inventory/`);
    expect(inventoryRequest.request.method).toBe('GET');
    inventoryRequest.flush([]);

    expect(fixture.nativeElement.querySelector('app-inventory')).toBeTruthy();
    expect(router.url).toBe(currentUrl);
  });

  it('opens the customers section', () => {
    fixture.detectChanges();
    const moduleButton = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>(
        'section button'
      )
    ).find((button) => button.textContent?.includes('Clientes'));
    if (!(moduleButton instanceof HTMLButtonElement)) {
      throw new Error('No se encontró el módulo de clientes.');
    }

    moduleButton.click();
    fixture.detectChanges();

    const customersRequest = httpMock.expectOne(`${environment.apiUrl}/customers/`);
    expect(customersRequest.request.method).toBe('GET');
    customersRequest.flush([]);

    expect(fixture.nativeElement.querySelector('app-customers')).toBeTruthy();
  });

  it('opens supplier and sales sections', () => {
    openModule(
      'Proveedores',
      `${environment.apiUrl}/suppliers/`,
      'app-suppliers',
      []
    );
    const backButton = (
      fixture.nativeElement as HTMLElement
    ).querySelector<HTMLButtonElement>('app-suppliers button');
    if (!backButton) {
      throw new Error('No se encontró el botón para volver desde proveedores.');
    }
    backButton.click();
    fixture.detectChanges();

    openModule('Ventas', `${environment.apiUrl}/sales/`, 'app-sales', []);
  });

  it('opens the reports section', () => {
    openModule(
      'Reportes',
      `${environment.apiUrl}/reports/summary/`,
      'app-reports',
      {
        sales_count: 0,
        total_revenue: '0.00',
        average_sale: '0.00',
        monthly_sales: [],
        top_products: [],
        customer_count: 0,
        supplier_count: 0,
        inventory_count: 0,
        inventory_units: 0,
        low_stock_count: 0,
        inventory_value: '0.00',
        repair_count: 0,
        open_repair_count: 0,
      }
    );
  });
});
