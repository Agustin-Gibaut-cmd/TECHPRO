import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';

export interface DashboardModule {
  id: string;
  title: string;
  description: string;
  icon: 'repairs' | 'inventory' | 'customers' | 'suppliers' | 'sales' | 'reports';
}

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
})
export class Dashboard {
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);
  readonly currentUser = this.authService.currentUser;
  readonly selectedModule = signal<string | null>(null);

  readonly modules = signal<DashboardModule[]>([
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
      description: 'Contactos, historial de equipos y reparaciones realizadas.',
      icon: 'customers',
    },
    {
      id: 'suppliers',
      title: 'Proveedores',
      description: 'Gestión de proveedores y pedidos de componentes y repuestos.',
      icon: 'suppliers',
    },
    {
      id: 'sales',
      title: 'Ventas',
      description: 'Registro de ventas de equipos, accesorios y servicios técnicos.',
      icon: 'sales',
    },
    {
      id: 'reports',
      title: 'Reportes',
      description: 'Resumen de ingresos, reparaciones, ventas y rendimiento del taller.',
      icon: 'reports',
    },
  ]);

  selectModule(module: DashboardModule): void {
    this.selectedModule.set(module.title);
  }

  logout(): void {
    this.authService.logout();
    void this.router.navigate(['/login']);
  }
}
