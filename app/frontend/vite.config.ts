import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [react()],
	build: {
		outDir: '../backend/static',
		emptyOutDir: true,
		sourcemap: true,
		rollupOptions: {
			output: {
				manualChunks: id => {
					if (id.includes('@fluentui/react-icons')) {
						return 'fluentui-icons';
					} else if (id.includes('@fluentui/react')) {
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
			'/auth_setup': 'http://localhost:50505',
			'/chat_stream': 'http://localhost:50505',
			'/ask': 'http://localhost:50505',
			'/chat': 'http://localhost:50505',
			'/logs': 'http://localhost:50505',
			'/logs/*': 'http://localhost:50505',
		},
	},
});
