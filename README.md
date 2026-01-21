# Respiración Pro PWA

Una aplicación web progresiva (PWA) para ejercicios de respiración guiados.

## Contenido del paquete

```
respiracion-pwa/
├── index.html          # App principal
├── manifest.json       # Configuración PWA
├── sw.js              # Service Worker (funcionamiento offline)
├── INSTRUCCIONES.md   # Guía para usuarios
├── README.md          # Este archivo
└── icons/             # Iconos de la app
    ├── icon-72.png
    ├── icon-96.png
    ├── icon-128.png
    ├── icon-144.png
    ├── icon-152.png
    ├── icon-192.png
    ├── icon-384.png
    ├── icon-512.png
    ├── icon-maskable-192.png
    ├── icon-maskable-512.png
    ├── favicon-16.png
    ├── favicon-32.png
    ├── apple-touch-icon.png
    ├── screenshot-wide.png
    └── screenshot-narrow.png
```

## Opciones de hosting gratuito

### 1. GitHub Pages (Recomendado)

**Ventajas:** Gratis, HTTPS automático, fácil de actualizar

1. Crea un repositorio en GitHub (ej: `respiracion-pro`)
2. Sube todos los archivos de esta carpeta
3. Ve a Settings → Pages → Source: "main" branch → Save
4. Tu app estará en: `https://tu-usuario.github.io/respiracion-pro/`

**Comandos:**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/respiracion-pro.git
git push -u origin main
```

### 2. Netlify

**Ventajas:** Drag & drop, dominio personalizado gratis

1. Ve a [netlify.com](https://netlify.com)
2. Arrastra la carpeta `respiracion-pwa` al panel
3. ¡Listo! Te da una URL como `random-name.netlify.app`

### 3. Vercel

**Ventajas:** Muy rápido, ideal para apps

1. Ve a [vercel.com](https://vercel.com)
2. Importa desde GitHub o sube directamente
3. URL automática: `proyecto.vercel.app`

### 4. Firebase Hosting

**Ventajas:** CDN global de Google

```bash
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy
```

### 5. Servidor propio (Nginx/Apache)

Simplemente copia la carpeta al directorio de tu servidor web.

**Importante para PWA:** Necesitas HTTPS. Con Let's Encrypt es gratis:
```bash
sudo certbot --nginx -d tudominio.com
```

## Configuración del servidor

Si usas tu propio servidor, asegúrate de que sirve los archivos con los MIME types correctos:

```nginx
# Nginx
location / {
    types {
        application/manifest+json webmanifest json;
    }
}
```

```apache
# Apache (.htaccess)
AddType application/manifest+json .json
```

## Compartir con amigos

1. Sube la app a cualquiera de las opciones anteriores
2. Comparte la URL con tus amigos
3. Envíales el archivo `INSTRUCCIONES.md` para que sepan cómo instalarla

## Actualizaciones

Cuando actualices la app:

1. Modifica la versión en `sw.js` (línea `CACHE_NAME`)
2. Los usuarios recibirán automáticamente un mensaje de actualización

## Requisitos técnicos

- **Navegador compatible:** Chrome 67+, Firefox 67+, Safari 11.1+, Edge 79+
- **HTTPS obligatorio** para instalar como PWA (excepto localhost)
- **Service Worker** requiere JavaScript habilitado

## Características de la PWA

- ✅ Instalable en Android/iOS/Desktop
- ✅ Funciona offline
- ✅ Iconos adaptativos (Android)
- ✅ Splash screen automático
- ✅ Shortcuts desde la pantalla de inicio
- ✅ Tema claro/oscuro automático
- ✅ Compartible por URL

## Licencia

Uso personal y entre amigos. Creado por Andreas Falk.
