import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { viteSingleFile } from 'vite-plugin-singlefile'

// Сборка — один самодостаточный index.html (JS, CSS, шрифты и данные внутри),
// поэтому dist/index.html открывается двойным щелчком, без сервера и без интернета.
// base: './' — относительные пути, работает и на GitHub Pages в подпапке, и на Vercel.
export default defineConfig({
  base: './',
  plugins: [react(), viteSingleFile({ removeViteModuleLoader: true })],
  build: {
    outDir: 'dist',
    assetsInlineLimit: 100_000_000,
    cssCodeSplit: false,
    chunkSizeWarningLimit: 5000,
  },
  server: { fs: { allow: ['..'] } },
})
