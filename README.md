# Respiración Pro

Respiración Pro es una app de respiración guiada preparada como PWA y como app Android para Google Play mediante Capacitor.

## Estado Play Store V1

- Nombre público: `Respiración Pro`
- Android app ID: `com.respiracionpro.app`
- Modelo de venta: pago único
- Precio inicial previsto: `1,99 EUR`
- Idiomas: español e inglés
- Datos: locales en el dispositivo, sin analítica, anuncios, cuentas ni rastreadores
- Build Android: GitHub Actions

## Desarrollo web

La app web principal sigue estando en la raíz del repo:

- `index.html`
- `manifest.json`
- `sw.js`
- `privacy.html`
- `icons/`

Para preparar los assets que usa Capacitor:

```bash
npm install
npm run build
```

El comando copia los archivos necesarios a `www/`, que es generado y no se versiona.

## Android

Sincronizar Android:

```bash
npm run cap:sync
```

Abrir en Android Studio:

```bash
npm run android:open
```

Generar App Bundle release localmente, si tienes Java/Android SDK y firma configurada:

```bash
npm run android:bundle
```

El workflow `.github/workflows/android-release.yml` genera el `.aab` firmado en GitHub Actions cuando se configuran los secretos de firma.

## Publicación

La guía operativa está en:

- `docs/PLAY_STORE_CHECKLIST.md`
- `store-listing/es-ES.md`
- `store-listing/en-US.md`
- `store-listing/data-safety.md`
- `store-listing/closed-test-instructions-es.md`

Assets de tienda:

- `store-assets/feature-graphic.png`
- `icons/icon-512.png`
- `icons/screenshot-narrow.png`
- `icons/screenshot-wide.png`

## Privacidad

La app no recopila datos personales. Las estadísticas, preferencias y patrones personalizados se guardan localmente en el dispositivo del usuario.

Contacto de soporte previsto: `respiracionpro.app@gmail.com`.

