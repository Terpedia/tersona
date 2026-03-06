import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node';

// https://astro.build/config
export default defineConfig({
  site: 'https://danielmcshan.github.io',
  base: '/tersona',
  integrations: [tailwind()],
  output: 'static',
  build: {
    assets: '_astro'
  }
});
