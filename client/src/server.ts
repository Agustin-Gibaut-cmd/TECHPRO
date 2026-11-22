import {
  AngularNodeAppEngine,
  createNodeRequestHandler,
  isMainModule,
  writeResponseToNodeResponse,
} from '@angular/ssr/node';
import express, { type ErrorRequestHandler } from 'express';
import { join } from 'node:path';

const browserDistFolder = join(import.meta.dirname, '../browser');
const app = express();
const angularApp = new AngularNodeAppEngine();

app.disable('x-powered-by');
app.use((_request, response, next) => {
  response.setHeader('X-Content-Type-Options', 'nosniff');
  response.setHeader('X-Frame-Options', 'DENY');
  response.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  next();
});

app.use(
  express.static(browserDistFolder, {
    maxAge: '1y',
    index: false,
    redirect: false,
  }),
);

app.use((request, response, next) => {
  angularApp
    .handle(request)
    .then((result) =>
      result ? writeResponseToNodeResponse(result, response) : next(),
    )
    .catch(next);
});

const handleServerError: ErrorRequestHandler = (
  error,
  _request,
  response,
  next,
) => {
  if (response.headersSent) {
    next(error);
    return;
  }

  console.error('Angular SSR request failed.', error);
  response.status(500).send('Internal server error.');
};

app.use(handleServerError);

function getPort(value: string | undefined): number {
  if (!value) {
    return 4000;
  }

  const port = Number(value);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('PORT must be an integer between 1 and 65535.');
  }

  return port;
}

function startServer(): void {
  const port = getPort(process.env['PORT']);
  const host = process.env['HOST'] || '127.0.0.1';
  const server = app.listen(port, host, () => {
    console.info(`Angular SSR listening on ${host}:${port}`);
  });

  server.on('error', (error: Error) => {
    console.error('Angular SSR could not start.', error);
    process.exitCode = 1;
  });
}

if (isMainModule(import.meta.url) || process.env['pm_id']) {
  startServer();
}

export const reqHandler = createNodeRequestHandler(app);
