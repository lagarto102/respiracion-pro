import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.respiracionpro.app',
  appName: 'Respiración Pro',
  webDir: 'www',
  bundledWebRuntime: false,
  server: {
    androidScheme: 'https'
  },
  android: {
    // WebView transparente mientras carga: se ve el color de arranque (papel o tinta)
    // en vez de un fogonazo blanco.
    backgroundColor: '#00000000',
    buildOptions: {
      releaseType: 'AAB'
    }
  },
  plugins: {
    // El papel llega hasta arriba (detrás de la barra de estado) y los iconos
    // de la barra van oscuros; la app los cambia a claros con el aspecto "tinta".
    StatusBar: {
      overlaysWebView: true,
      style: 'LIGHT'
    }
  }
};

export default config;
