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
      fixture.nativeElement.querySelectorAll('section button')
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
      fixture.nativeElement.querySelectorAll('section button')
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
});
