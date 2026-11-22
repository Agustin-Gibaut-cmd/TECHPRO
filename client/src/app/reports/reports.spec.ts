import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { DashboardReport } from './reports.service';
import { Reports } from './reports';

describe('Reports', () => {
  let fixture: ComponentFixture<Reports>;
  let component: Reports;
  let httpMock: HttpTestingController;

  const reportsUrl = `${environment.apiUrl}/reports/summary/`;
  const report: DashboardReport = {
    sales_count: 2,
    total_revenue: '25000.00',
    average_sale: '12500.00',
    monthly_sales: [{ month: '2026-11', sales_count: 2, revenue: '25000.00' }],
    top_products: [
      { product_name: 'Cargador USB-C', units_sold: 2, revenue: '25000.00' },
    ],
    customer_count: 1,
    supplier_count: 1,
    inventory_count: 1,
    inventory_units: 8,
    low_stock_count: 0,
    inventory_value: '100000.00',
    repair_count: 2,
    open_repair_count: 1,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Reports],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Reports);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('loads the authenticated summary and renders both charts', () => {
    fixture.detectChanges();

    const request = httpMock.expectOne(reportsUrl);
    expect(request.request.method).toBe('GET');
    expect(request.request.withCredentials).toBe(true);
    request.flush(report);
    fixture.detectChanges();

    expect(component.report()).toEqual(report);
    expect(component.maxMonthlyRevenue).toBe(25000);
    expect(component.maxProductUnits).toBe(2);
    expect(
      fixture.nativeElement.querySelectorAll('svg[role="img"]').length
    ).toBe(2);
    expect(fixture.nativeElement.querySelectorAll('svg rect').length).toBe(2);
    expect(component.barHeight(1, 2)).toBe(80);
  });

  it('renders empty chart axes without inventing report data', () => {
    fixture.detectChanges();

    httpMock.expectOne(reportsUrl).flush({
      ...report,
      sales_count: 0,
      total_revenue: '0.00',
      average_sale: '0.00',
      monthly_sales: [],
      top_products: [],
    });
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelectorAll('svg[role="img"]').length
    ).toBe(2);
    expect(fixture.nativeElement.querySelectorAll('svg rect').length).toBe(0);
    expect(fixture.nativeElement.textContent).toContain(
      'Sin ventas para mostrar'
    );
    expect(fixture.nativeElement.textContent).toContain(
      'Sin productos para mostrar'
    );
  });
});
