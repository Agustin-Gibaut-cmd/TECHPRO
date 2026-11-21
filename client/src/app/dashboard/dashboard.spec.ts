import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { Dashboard } from './dashboard';

describe('Dashboard', () => {
  let component: Dashboard;
  let fixture: ComponentFixture<Dashboard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Dashboard],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Dashboard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('keeps module options on the dashboard and reports unavailable sections', () => {
    const moduleButton: HTMLButtonElement =
      fixture.nativeElement.querySelector('section button');
    const router: Router = TestBed.inject(Router);
    const currentUrl: string = router.url;

    moduleButton.click();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[role="status"]')?.textContent).toContain(
      'Reparaciones'
    );
    expect(router.url).toBe(currentUrl);
  });
});
