import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Vite config tuned for a self-contained chat web app. Adjust server port as needed.
export default defineConfig({
    plugins: [react()],
    envPrefix: "VITE_",
    server: {
        port: 5173
    },
    build: {
        outDir: "dist",
        sourcemap: true
    }
});
