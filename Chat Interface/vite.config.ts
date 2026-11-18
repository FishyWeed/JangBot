import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	// Read non-secret HOST/PORT from the single root .env for dev proxy alignment
	const rootEnv = loadEnv(mode, '..', '');
	const apiHost = rootEnv.HOST || '127.0.0.1';
	const apiPort = rootEnv.PORT || '8000';
	const apiTarget = `http://${apiHost}:${apiPort}`;

	return {
		envDir: '..',
		plugins: [
			sveltekit({
				compilerOptions: {
					runes: ({ filename }) =>
						filename.split(/[/\\]/).includes('node_modules') ? undefined : true
				},
				adapter: adapter({
					pages: 'build',
					assets: 'build',
					fallback: 'index.html',
					precompress: false,
					strict: false
				})
			})
		],
		server: {
			proxy: {
				'/api': {
					target: apiTarget,
					changeOrigin: true
				}
			}
		}
	};
});
