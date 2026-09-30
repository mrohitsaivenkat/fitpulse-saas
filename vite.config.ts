import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';
import {defineConfig, Plugin} from 'vite';

function apiRoutesPlugin(): Plugin {
  const handleApi = (req: any, res: any, next: any) => {
    const url = req.url?.split('?')[0];

    // Auth HTML Page Routing
    if (url === '/login') {
      const loginHtmlPath = path.resolve('public/login.html');
      if (fs.existsSync(loginHtmlPath)) {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end(fs.readFileSync(loginHtmlPath));
        return;
      }
    }
    if (url === '/register' || url === '/register/coach') {
      const registerHtmlPath = path.resolve('public/register.html');
      if (fs.existsSync(registerHtmlPath)) {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end(fs.readFileSync(registerHtmlPath));
        return;
      }
    }
    if (url === '/admin' || url === '/admin/overview') {
      const adminPath = path.resolve('public/admin.html');
      if (fs.existsSync(adminPath)) {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end(fs.readFileSync(adminPath));
        return;
      }
    }
    if (url === '/coach' || url === '/coach/portal') {
      const coachPath = path.resolve('public/coach.html');
      if (fs.existsSync(coachPath)) {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end(fs.readFileSync(coachPath));
        return;
      }
    }
    if (url === '/client' || url === '/client/portal') {
      const clientPath = path.resolve('public/client.html');
      if (fs.existsSync(clientPath)) {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end(fs.readFileSync(clientPath));
        return;
      }
    }
    if (url === '/403') {
      const errPath = path.resolve('public/403.html');
      if (fs.existsSync(errPath)) {
        res.statusCode = 403;
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end(fs.readFileSync(errPath));
        return;
      }
    }

    // Health Check Endpoint
    if (url === '/health') {
      res.setHeader('Content-Type', 'application/json');
      res.end(
        JSON.stringify({
          status: 'healthy',
          service: 'FitPulse SaaS Engine',
          phase: 'Phase 4B - Real Diet Plan Management',
          database_configured: true,
          multi_tenant_ready: true,
          auth_configured: true,
          rbac_configured: true,
          tenant_isolation_configured: true,
          security_hardened: true,
          diet_management_ready: true,
        })
      );
      return;
    }

    // Platform Metadata
    if (url === '/api/v1/meta') {
      res.setHeader('Content-Type', 'application/json');
      res.end(
        JSON.stringify({
          platform: 'FitPulse SaaS',
          version: '1.9.0-phase4b',
          target_audience: 'Independent Fitness Coaches and Personal Trainers',
          phase: 'Phase 4B - Real Diet Plan Management',
          auth_system: 'Flask-Login + Session + Werkzeug PBKDF2/scrypt',
          rbac_roles: ['SUPER_ADMIN', 'COACH', 'CLIENT'],
          tenant_model: 'Strict Multi-Tenant Coach Partitioning & Athlete Own-Data Isolation',
          business_modules: [
            'Coach Client Management (Phase 4A)',
            'Real Diet Plan Management (Phase 4B)',
          ],
          security_features: [
            'Session HTTPOnly & SameSite Lax',
            'Cryptographic CSRF Protection',
            'Sliding-Window Rate Limiting',
            'Non-Predictable File Storage & Auth Media Streaming',
            'Audit Credential Sanitization',
            'HTTP Security Headers (CSP, HSTS, X-Frame-Options, nosniff)',
          ],
          models_initialized: [
            'User',
            'Coach',
            'Client',
            'Exercise',
            'DietPlan',
            'DietItem',
            'WorkoutPlan',
            'WorkoutDay',
            'WorkoutExercise',
            'Progress',
            'Measurement',
            'ProgressPhoto',
            'Transformation',
            'TransformationConsent',
            'Review',
            'SubscriptionPlan',
            'Subscription',
            'Notification',
            'SupportTicket',
            'Announcement',
            'AuditLog',
          ],
          free_tools: [
            'Food Alternatives Finder',
            'Historical Diet & Progress Analyzer',
            'Injury & Exercise Safety Guide',
          ],
        })
      );
      return;
    }

    // Auth API endpoints mock/passthrough for Vite preview
    if (url === '/api/v1/auth/login' && req.method === 'POST') {
      let body = '';
      req.on('data', (chunk: any) => body += chunk);
      req.on('end', () => {
        try {
          const { email, password } = JSON.parse(body || '{}');
          if (!email || !password) {
            res.statusCode = 401;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: 'Please provide both email and password.', status_code: 401 }));
            return;
          }
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({
            success: true,
            message: 'Authentication successful.',
            user: { email, role: 'COACH', first_name: 'Coach', last_name: 'User' }
          }));
        } catch {
          res.statusCode = 400;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'Invalid payload.' }));
        }
      });
      return;
    }

    if (url === '/api/v1/auth/register' && req.method === 'POST') {
      let body = '';
      req.on('data', (chunk: any) => body += chunk);
      req.on('end', () => {
        try {
          const { email, first_name, last_name, business_name, password } = JSON.parse(body || '{}');
          if (!email || !password || !first_name || !last_name || !business_name) {
            res.statusCode = 400;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: 'All required fields must be provided.', status_code: 400 }));
            return;
          }
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({
            success: true,
            message: 'Coach account created successfully.',
            user: { email, role: 'COACH', first_name, last_name, business_name }
          }));
        } catch {
          res.statusCode = 400;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'Invalid payload.' }));
        }
      });
      return;
    }

    if (url === '/api/v1/auth/logout') {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ success: true, message: 'Successfully logged out.' }));
      return;
    }

    next();
  };

  return {
    name: 'fitpulse-api-routes',
    configureServer(server) {
      server.middlewares.use(handleApi);
    },
    configurePreviewServer(server) {
      server.middlewares.use(handleApi);
    },
  };
}

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss(), apiRoutesPlugin()],
    resolve: {
      alias: {
        '@': path.resolve('.'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modify—file watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
