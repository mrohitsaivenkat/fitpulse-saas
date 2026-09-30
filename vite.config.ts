import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig, Plugin} from 'vite';

function apiRoutesPlugin(): Plugin {
  const handleApi = (req: any, res: any, next: any) => {
    const url = req.url?.split('?')[0];
    if (url === '/health') {
      res.setHeader('Content-Type', 'application/json');
      res.end(
        JSON.stringify({
          status: 'healthy',
          service: 'FitPulse SaaS Engine',
          phase: 'Phase 2B - Exercise, Diet & Workout Database Models',
          database_configured: true,
          multi_tenant_ready: true,
        })
      );
      return;
    }
    if (url === '/api/v1/meta') {
      res.setHeader('Content-Type', 'application/json');
      res.end(
        JSON.stringify({
          platform: 'FitPulse SaaS',
          version: '1.2.0-phase2b',
          target_audience: 'Independent Fitness Coaches and Personal Trainers',
          phase: 'Phase 2B - Exercise, Diet & Workout Database Models',
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
