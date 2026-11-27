import { expect, test } from '@playwright/test';

const EMAIL = process.env.TECHPRO_TEST_EMAIL ?? 'admin@techpro.local';
const PASSWORD = process.env.TECHPRO_TEST_PASSWORD ?? 'TechproTest!2026';

test('un usuario autenticado accede al dashboard', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill(EMAIL);
  await page.getByLabel('Contraseña').fill(PASSWORD);
  await page.getByRole('button', { name: 'Continuar' }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole('heading', { name: /Hola,/ })).toBeVisible();
});

test('una ruta privada redirige al login sin sesión', async ({ page }) => {
  await page.goto('/dashboard');

  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible();
});
