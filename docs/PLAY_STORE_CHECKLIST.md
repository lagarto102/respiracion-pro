# Respiración Pro - Play Store checklist

## 1. Cuenta y venta

1. Crear o abrir Google Play Console.
2. Si es cuenta nueva personal, completar verificación de identidad y verificación con dispositivo Android.
3. Pagar la tasa única de registro de Google Play.
4. Crear perfil de pagos para vender la app.
5. Crear un Gmail público de soporte: `respiracionproapp@gmail.com`.

## 2. App en Play Console

- Nombre: `Respiración Pro`
- Tipo: App
- Categoría: Health & Fitness / Salud y bienestar
- Precio inicial: `1,99 EUR`
- Anuncios: No
- Compras dentro de la app: No
- Público objetivo: adultos y público general, no dirigida específicamente a menores de 13 años
- Política de privacidad: publicar `privacy.html` en una URL accesible

## 3. Firma Android en GitHub

El workflow `.github/workflows/android-release.yml` genera el `.aab` firmado si existen estos secretos del repositorio:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

Para crear el keystore, usar Android Studio o `keytool`:

```bash
keytool -genkeypair -v -keystore respiracion-pro-upload.keystore -alias respiracion-pro-upload -keyalg RSA -keysize 2048 -validity 10000
```

Convertir el keystore a Base64 antes de guardarlo como secreto:

```bash
base64 -w 0 respiracion-pro-upload.keystore
```

En Windows PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("respiracion-pro-upload.keystore"))
```

Guardar el resultado en `ANDROID_KEYSTORE_BASE64`. No subir nunca el archivo `.keystore` al repo.

## 4. Build

1. Subir la rama `play-ready-v1` a GitHub.
2. Ir a GitHub > Actions > Android release bundle.
3. Ejecutar workflow manualmente con:
   - `version_name`: `1.0.0`
   - `version_code`: `1`
4. Descargar el artifact `.aab`.
5. Subirlo primero a Internal testing en Play Console.

## 5. Data Safety

Declaración recomendada:

- Recopila datos: No
- Comparte datos: No
- Datos cifrados en tránsito: No aplica, la app no envía datos personales a servidores
- Permite solicitar eliminación: No aplica a servidores; el usuario puede borrar datos locales desde ajustes del navegador/app o exportar/importar su historial
- Ubicación: No
- Salud: No se recopila información de salud
- Analítica: No
- Ads SDK: No
- Cuentas: No

## 6. Prueba cerrada

Si la cuenta personal es nueva:

1. Crear prueba cerrada.
2. Añadir al menos 12 testers con cuentas Google.
3. Mantenerlos opt-in durante 14 días continuos.
4. Pedirles que prueben:
   - iniciar/detener sesión
   - cambiar idioma
   - audio, voz y vibración
   - historial
   - exportar/importar datos
   - modo avión
5. Guardar un resumen de feedback para solicitar acceso a producción.

## 7. Producción

Cuando Play permita producción:

1. Revisar Android Vitals y pre-launch report.
2. Corregir cualquier crash o warning grave.
3. Publicar con rollout gradual si está disponible.
4. Vigilar reseñas y feedback durante la primera semana.
