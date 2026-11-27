import { Component, Signal, WritableSignal, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';
import { Customers } from '../customers/customers';
import { Inventory } from '../inventory/inventory';
import { Reports } from '../reports/reports';
import { Repairs } from '../repairs/repairs';
import { Sales } from '../sales/sales';
import { Suppliers } from '../suppliers/suppliers';

export type DashboardModuleId = 'repairs' | 'inventory' | 'customers' | 'suppliers' | 'sales' | 'reports';

export type DashboardSelectedModule = DashboardModuleId | null;

export interface DashboardUser {
  name?: string;
}

export interface DashboardModule {
  id: DashboardModuleId;
  title: string;
  description: string;
  icon: DashboardModuleId;
}

const LOGIN_ROUTE: readonly string[] = ['/login'];

const DASHBOARD_MODULES: readonly DashboardModule[] = [
  {
    id: 'repairs',
    title: 'Reparaciones',
    description: 'Alta y seguimiento de equipos, diagnósticos y órdenes de servicio.',
    icon: 'repairs',
  },
  {
    id: 'inventory',
    title: 'Inventario',
    description: 'Control de equipos, componentes, repuestos y stock mínimo.',
    icon: 'inventory',
  },
  {
    id: 'customers',
    title: 'Clientes',
    description: 'Alta y mantenimiento de los contactos de tus clientes.',
    icon: 'customers',
  },
  {
    id: 'suppliers',
    title: 'Proveedores',
    description: 'Alta y mantenimiento de los contactos de tus proveedores.',
    icon: 'suppliers',
  },
  {
    id: 'sales',
    title: 'Ventas',
    description: 'Registro de productos vendidos, clientes e importes.',
    icon: 'sales',
  },
  {
    id: 'reports',
    title: 'Reportes',
    description: 'Resumen de ingresos, reparaciones, ventas y rendimiento del taller.',
    icon: 'reports',
  },
];

/** Panel principal de TECHPRO para navegar entre módulos operativos del taller. */
@Component({
  imports: [Customers, Inventory, Reports, Repairs, Sales, Suppliers],
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
})
export class Dashboard {
  private readonly router: Router = inject(Router);
  private readonly authService: AuthService = inject(AuthService);

  readonly currentUser: Signal<DashboardUser | null | undefined> =
    this.authService.currentUser as Signal<DashboardUser | null | undefined>;
  readonly selectedModule: WritableSignal<DashboardSelectedModule> = signal<DashboardSelectedModule>(null);
  readonly modules: Signal<readonly DashboardModule[]> = signal<readonly DashboardModule[]>(DASHBOARD_MODULES);

  /** Selecciona el módulo activo del panel. */
  selectModule(dashboardModule: DashboardModule): void {
    this.selectedModule.set(dashboardModule.id);
    // WCAG 2.4.3 Focus Order: no perder el foco al reemplazar el contenido.
    this.focusElement('module-content');
  }

  /** Vuelve al listado de módulos y restaura el foco en la tarjeta de origen. */
  onModuleBack(): void {
    const previousModule: DashboardSelectedModule = this.selectedModule();
    this.selectedModule.set(null);
    if (previousModule !== null) {
      // WCAG 2.4.3 Focus Order: devolver el foco al control que abrió el módulo.
      this.focusElement(`module-card-${previousModule}`);
    }
  }

  private focusElement(elementId: string): void {
    setTimeout((): void => {
      document.getElementById(elementId)?.focus();
    }, 0);
  }

  /** Cierra la sesión actual y redirige al login. */
  logout(): void {
    this.authService.logout();
    void this.router.navigate([...LOGIN_ROUTE]);
  }
}