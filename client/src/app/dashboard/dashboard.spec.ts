import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Dashboard } from './dashboard';

describe('Dashboard', () => {
  let component: Dashboard;
  let fixture: ComponentFixture<Dashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Dashboard],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Dashboard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('keeps unavailable modules on the dashboard', () => {
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

    expect(fixture.nativeElement.querySelector('[role="status"]')?.textContent).toContain(
      'Esta sección todavía no está disponible.'
    );
    expect(router.url).toBe(currentUrl);
  });
});
