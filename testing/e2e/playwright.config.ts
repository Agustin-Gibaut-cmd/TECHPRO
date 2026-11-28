import { defineConfig, devices } from '@playwright/test';

declare const process: {
  readonly env: Readonly<Record<string, string | undefined>>;
};

const webUrl = process.env.TECHPRO_WEB_URL;
if (!webUrl) {
  throw new Error('Define TECHPRO_WEB_URL para ejecutar las pruebas E2E.');
}

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: webUrl,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
