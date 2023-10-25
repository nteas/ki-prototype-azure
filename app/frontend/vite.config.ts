import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import eslint from 'vite-plugin-eslint';

// https://vitejs.dev/config/
export default defineConfig({
	clearScreen: false,
	plugins: [react(), eslint()],
	build: {
		outDir: '../backend/static',
		emptyOutDir: true,
		sourcemap: true,
		rollupOptions: {
			output: {
				manualChunks: id => {
					if (id.includes('@fluentui/react')) {
						return 'fluentui-react';
					} else if (id.includes('node_modules')) {
						return 'vendor';
					}
				},
			},
		},
		target: 'esnext',
	},
	server: {
		port: 3000,
		proxy: {
			'/api': {
				target: 'http://localhost:50505',
				changeOrigin: true,
			},
		},
	},
});
