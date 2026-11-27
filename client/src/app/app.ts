import { Component, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { filter } from 'rxjs';

/** Títulos de página por ruta para WCAG 2.4.2 Page Titled. */
const PAGE_TITLES: Readonly<Record<string, string>> = {
  '/login': 'Iniciar sesión · TECHPRO',
  '/dashboard': 'Panel · TECHPRO',
};

const DEFAULT_TITLE = 'TECHPRO';

@Component({
  imports: [RouterOutlet],
  selector: 'app-root',
  templateUrl: './app.html',
})
export class App {
  protected readonly title = signal('client');

  constructor() {
    const router: Router = inject(Router);
    const titleService: Title = inject(Title);

    router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        const basePath: string = event.urlAfterRedirects.split('?')[0].split('#')[0];
        titleService.setTitle(PAGE_TITLES[basePath] ?? DEFAULT_TITLE);
      });
  }
}
