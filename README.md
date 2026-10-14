# HandheldFanTweaker

Plugin de [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) para editar las curvas del ventilador y hacer underclock de CPU en consolas con [SteamOS ARM Port](https://github.com/hashtagbasit/SteamOS-ARM-Port).

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

**Por comando** (instala o actualiza a la última versión), en Konsole:

```bash
curl -fsSL https://raw.githubusercontent.com/sleoier/HandheldFanTweaker/main/update.sh | sudo sh
```

**Desde Decky:**

1. Descarga `HandheldFanTweaker.zip` del [último release](https://github.com/sleoier/HandheldFanTweaker/releases/latest).
2. En Decky: ⚙️ Ajustes → **General** → activa **Developer mode**.
3. ⚙️ Ajustes → **Developer** → **Install Plugin from URL** y pega el enlace del `.zip` (o **Install Plugin from ZIP File** si lo copiaste a la consola).

## Cómo funciona

SteamOS ARM Port controla el ventilador con un daemon (`odin3d`) que tiene tres perfiles: Silent, Balanced y Turbo. El plugin muestra la curva de cada perfil en un gráfico, permite mover sus puntos y, al aplicar, reescribe solo esa línea en `/etc/odin3.conf` y recarga el daemon. El perfil activo se sigue eligiendo desde Handheld Control o desde Steam.

- Rechaza curvas peligrosas: tienen que llegar al 100 % a 95 °C o antes.
- Guarda una copia del archivo original y permite volver a la curva de fábrica.
- Si una actualización del sistema restaura las curvas, vuelve a aplicar las tuyas.
- Nunca controla el ventilador directamente; eso lo sigue haciendo el daemon.

### Underclock de CPU

Tres niveles (Low, Medium y High) que limitan la frecuencia máxima de cada clúster a un porcentaje de su tope (87 %, 78 % y 64 %), ajustado a la frecuencia disponible más cercana. En la Odin 3:

| Nivel | Núcleos 0–5 | Núcleos 6–7 |
|---|---|---|
| Low | 3072 MHz | 3513.6 MHz |
| Medium | 2745.6 MHz | 3072 MHz |
| High | 2227.2 MHz | 2438.4 MHz |

Low corta justo donde el modelo de energía del kernel muestra que el consumo sube mucho más rápido que la velocidad. Medium y High coinciden casi por completo con los presets que publicó la comunidad en [Odin3-CPU-Underclock](https://github.com/TheOldTaylor/Odin3-CPU-Underclock).

El nivel se guarda y se vuelve a aplicar al iniciar y cada vez que el sistema restablece las frecuencias. Si el TDP de Steam es más estricto, se respeta. No baja el voltaje ni toca la GPU (para eso está el TDP de Steam).

## Desarrollo

```bash
npm install && npm run build                                        # frontend
PYTHONPATH=py_modules python3 -m unittest discover -s tests -t .    # tests del backend
```

## Licencia

[BSD-3-Clause](LICENSE) · Sleoier
