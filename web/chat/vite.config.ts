import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    build: {
        // Build as library when building for component export
        lib: process.env.BUILD_MODE === 'lib' ? {
            entry: path.resolve(__dirname, 'src/lib/index.ts'),
            name: 'MSREventChat',
            formats: ['es', 'umd'],
            fileName: (format) => {
                if (format === 'es') return 'index.mjs';
                return 'index.umd.js';
            }
        } : undefined,
        outDir: process.env.BUILD_MODE === 'lib' ? "dist-lib" : "../static",
        emptyOutDir: true,
        sourcemap: true,
        cssMinify: "lightningcss",
        chunkSizeWarningLimit: 2000,
        rollupOptions: process.env.BUILD_MODE === 'lib' ? {
            external: ['react', 'react-dom'],
            output: {
                globals: {
                    react: 'React',
                    'react-dom': 'ReactDOM'
                }
            }
        } : {
            output: {
                manualChunks(id) {
                    if (id.includes('node_modules')) {
                        if (id.includes('react') && !id.includes('@fluentui')) {
                            return 'react-vendor';
                        }
                        if (id.includes('@fluentui/react-components')) {
                            return 'fluentui-components';
                        }
                        if (id.includes('@fluentui/react-icons')) {
                            return 'fluentui-icons';
                        }
                        if (id.includes('adaptivecards')) {
                            return 'adaptivecards';
                        }
                        if (id.includes('@tanstack')) {
                            return 'tanstack';
                        }
                        return 'vendor';
                    }
                }
            }
        }
    },
    server: {
        proxy: {
            "/ask": "http://127.0.0.1:5000",
            "/chat": "http://127.0.0.1:5000",
            "/conversation": "http://127.0.0.1:5000",
            "/speech": "http://127.0.0.1:5000",
        }
    }
});
