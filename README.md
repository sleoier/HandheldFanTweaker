# HandheldFanTweaker

Plugin de [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) para editar las curvas del ventilador en consolas con [SteamOS ARM Port](https://github.com/hashtagbasit/SteamOS-ARM-Port).

> [!WARNING]
> Proyecto hecho 100 % con vibecoding: el código lo escribió una IA (Claude) mientras **Sleoier** monitoreaba el desarrollo y lo probaba en una AYN Odin 3. Úsalo bajo tu propio riesgo.

## Compatibilidad

| | Consolas |
|---|---|
| ✅ Probado | AYN Odin 3 |
| 🟡 Debería funcionar | KONKR Pocket FIT Elite |
| 🔒 Solo lectura | Consolas con `konkrd` (Odin 2, Thor, Pocket FIT, Pocket S2, Retroid Pocket 5/6, AYANEO Pocket, REDMAGIC 6…) |
| ❌ No funciona | Steam Deck, consolas x86, Android |

## Instalación

1. Descarga `HandheldFanTweaker.zip` del [último release](https://github.com/sleoier/HandheldFanTweaker/releases/latest).
2. En Decky: ⚙️ Ajustes → **General** → activa **Developer mode**.
3. ⚙️ Ajustes → **Developer** → **Install Plugin from URL** y pega el enlace del `.zip` (o **Install Plugin from ZIP File** si lo copiaste a la consola).

## Cómo funciona

SteamOS ARM Port controla el ventilador con un daemon (`odin3d`) que tiene tres perfiles: Silent, Balanced y Turbo. El plugin muestra la curva de cada perfil en un gráfico, permite mover sus puntos y, al aplicar, reescribe solo esa línea en `/etc/odin3.conf` y recarga el daemon. El perfil activo se sigue eligiendo desde Handheld Control o desde Steam.

- Rechaza curvas peligrosas: tienen que llegar al 100 % a 95 °C o antes.
- Guarda una copia del archivo original y permite volver a la curva de fábrica.
- Si una actualización del sistema restaura las curvas, vuelve a aplicar las tuyas.
- Nunca controla el ventilador directamente; eso lo sigue haciendo el daemon.

## Desarrollo

```bash
npm install && npm run build                                        # frontend
PYTHONPATH=py_modules python3 -m unittest discover -s tests -t .    # tests del backend
```

## Licencia

[BSD-3-Clause](LICENSE) · Sleoier
