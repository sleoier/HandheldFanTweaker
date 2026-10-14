# HandheldFanTweaker

Plugin de [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) para **editar las curvas del ventilador** de las consolas que usan [SteamOS ARM Port](https://github.com/hashtagbasit/SteamOS-ARM-Port), desde el menú de acceso rápido del modo juego.

> [!WARNING]
> **Este proyecto es 100 % vibecoding.** El código, los tests y este README los escribió una IA (Claude), mientras **Sleoier** monitoreaba el desarrollo, tomaba las decisiones y lo probaba en su AYN Odin 3. No lo escribió un equipo con experiencia en drivers ni en firmware. Revisa lo que hace antes de instalarlo y reporta lo que falle.

> [!NOTE]
> Proyecto no oficial, sin relación con SteamOS ARM Port, Valve, AYN, KONKR, AYANEO ni Retroid. El código se escribió desde cero; de otros proyectos solo se tomó como referencia su comportamiento público (formato del `.conf`, nombre del servicio, señal de recarga).

## ¿Funciona en mi consola?

Solo funciona con **SteamOS ARM Port** instalado. No sirve en el Steam Deck, en consolas x86 (ROG Ally, Legion Go y similares) ni en Android.

| Estado | Consolas | Por qué |
|---|---|---|
| ✅ **Funciona** (probado) | AYN **Odin 3** | Usa `odin3d`, que lee sus curvas desde `/etc/odin3.conf` |
| 🟡 **Debería funcionar** (sin probar) | KONKR **Pocket FIT Elite** | Mismo chip (SM8750) y mismo daemon `odin3d` |
| 🔒 **Solo lectura** | KONKR Pocket FIT, AYANEO Pocket S2 (SM8650) · AYN Odin 2 / Mini / Portal / Thor, AYANEO Pocket ACE / DMG / DS / EVO / S 1K / S 2K, Retroid Pocket 6 / Nova (SM8550) · Retroid Pocket 5 / Flip 2 / Mini / Mini V2, AYN Thor Lite, MANGMI Air Y Pro / Pocket Max, AYANEO Pocket MICRO 2 (SM8250) · REDMAGIC 6 (SM8350) | Usan `konkrd`, que tiene las curvas dentro del programa. El plugin muestra la temperatura y el ventilador, pero no deja editar |
| ❌ **No funciona** | Cualquier otra | No hay un daemon de ventilador compatible |

En las consolas con `konkrd`, la edición se habilita sola el día que ese daemon lea una sección `[curves]` de su `.conf`, como ya lo hace `odin3d`.

## Qué hace

SteamOS ARM Port ya trae un daemon que mueve el ventilador según la temperatura, con tres perfiles (`silent`, `balanced` y `turbo`). El plugin **Handheld Control** que viene con el sistema permite elegir el perfil, pero no cambiar la curva de cada uno. HandheldFanTweaker hace eso:

- Muestra la curva de cada perfil en un gráfico, con la temperatura actual marcada.
- Permite mover cada punto (temperatura y velocidad), agregar o quitar puntos, aplicar y volver a la curva original.
- Muestra en vivo la temperatura que sigue la curva y la velocidad del ventilador.
- Recuerda tus curvas y las vuelve a aplicar si una actualización del sistema restaura el archivo original.

Convive con Handheld Control: ese plugin sigue eligiendo qué perfil está activo (también por juego) y este solo cambia la forma de cada curva. No escriben los mismos archivos.

## Instalación

Es un proyecto de uso personal: no está en la tienda de Decky ni tiene releases públicos.

1. En la PC, compila el frontend:

   ```bash
   npm install
   npm run build
   ```

2. Copia a la consola `plugin.json`, `package.json`, `main.py`, `py_modules/`, `dist/`, `README.md`, `LICENSE` e `install-on-device.sh` (por SSH, LocalSend o un pendrive).
3. En la consola, desde esa carpeta:

   ```bash
   sudo sh install-on-device.sh
   ```

El script copia el plugin a `~/homebrew/plugins/HandheldFanTweaker` y reinicia Decky. Para actualizar, repite los mismos pasos.

## Cómo funciona

```
 Menú rápido (React)                    Backend (Python, root)
┌────────────────────────┐  callable  ┌────────────────────────────────────────────┐
│ gráfico + deslizadores │──────────▶ │ main.py  (adaptador de Decky)              │
│ Apply / Restore        │ ◀──────────│   └─ FanCurveService (casos de uso)        │
└────────────────────────┘  {ok,...}  │        ├─ IniCurveFile ──▶ /etc/odin3.conf │
                                      │        ├─ SystemdDaemon ─▶ SIGHUP a odin3d │
                                      │        ├─ SysfsTelemetry ◀─ /sys (lectura) │
                                      │        └─ JsonSnapshotStore ─▶ curves.json │
                                      └────────────────────────────────────────────┘
```

1. Al abrir el panel, el frontend pide el estado: daemon detectado, curvas actuales, curvas originales, perfil activo, límites y telemetría.
2. Al presionar **Apply**, el backend valida la curva. Si es válida, reescribe **solo la línea de ese perfil** en `[curves]` y envía `SIGHUP` al daemon, que vuelve a leer su configuración.
3. El daemon sigue siendo el único que mueve el ventilador. El plugin nunca escribe en `pwm1`.

### Qué toca en el sistema

| Acción | Dónde |
|---|---|
| Escribe | Solo las líneas `silent = …`, `balanced = …` y `turbo = …` de `[curves]` en el `.conf` del daemon. Comentarios y otras secciones quedan igual. |
| Copia de seguridad | Antes del primer cambio guarda el `.conf` original como `<archivo>.handheldfantweaker.bak`, una sola vez. |
| Señal | `systemctl kill --signal=HUP <daemon>.service` |
| Lee | `/sys/class/thermal/*`, `/sys/class/hwmon/*` y el `state.json` del daemon (perfil activo) |
| Memoria propia | `curves.json` en la carpeta de ajustes que Decky le da al plugin |
| Nunca toca | Bootloader, particiones, kernel, el ventilador directamente ni archivos de otros plugins |

Necesita `root` (flag de Decky) porque `/etc` es de root.

### Seguridad de las curvas

El backend rechaza una curva, sin escribir nada, si:

- tiene menos de 2 o más de 10 puntos,
- alguna temperatura está fuera de 20–110 °C o algún PWM fuera de 0–255,
- las temperaturas no van de menor a mayor o la velocidad baja cuando sube la temperatura,
- **no llega al 100 % (PWM 255) a 95 °C o antes**.

Además, `odin3d` tiene su propio corte: a 88 °C pone el ventilador al 100 % sin importar la curva.

### Curva original y actualizaciones

La primera vez que el plugin lee el `.conf`, guarda esas curvas como **originales**. Cuando aplicas una curva, la guarda como **tuya**. Al iniciar Decky:

- si el `.conf` volvió a la curva original (por ejemplo después de una actualización), vuelve a escribir la tuya;
- si alguien editó el `.conf` a mano con otros valores, respeta ese cambio y lo toma como tu curva.

## Arquitectura del backend

Capas con dependencias que apuntan hacia adentro:

```
py_modules/handheld_fan_tweaker/
├── domain/            reglas puras, sin E/S
│   ├── curve.py         FanCurve: validación e interpolación
│   ├── models.py        Telemetry, BackendInfo, Snapshot
│   └── errors.py
├── ports.py           interfaces que necesita la aplicación
├── application/
│   └── service.py       FanCurveService: estado, aplicar, restaurar, reconciliar
├── infrastructure/    lo que toca el sistema
│   ├── ini_curve_file.py       [curves] línea por línea, escritura atómica
│   ├── curve_text.py           formato "45:0, 60:65, 90:255"
│   ├── daemons.py              odin3d / konkrd: detección, SIGHUP, perfil activo
│   ├── sysfs_telemetry.py      temperaturas y ventilador desde /sys
│   └── json_snapshot_store.py  memoria del plugin
├── composition.py     conecta las implementaciones
└── cli.py             el mismo backend por consola
main.py                adaptador de Decky
```

- **domain** no importa nada del proyecto.
- **application** solo conoce `domain` y `ports`; los tests la prueban con implementaciones en memoria.
- **infrastructure** recibe una raíz de archivos (`root`), así que se prueba sobre un árbol falso en `/tmp`.
- **main.py** no tiene lógica: pasa cada llamada al servicio y convierte los errores en `{"ok": false, "error": "…"}`.

Para agregar otro daemon, descríbelo con un `DaemonSpec` en `infrastructure/daemons.py` y súmalo a `KNOWN_DAEMONS`. Si guarda las curvas en otro formato, implementa `CurveRepository` y conéctalo en `composition.py`.

El backend usa solo la biblioteca estándar de Python. En la Odin 3, Decky corre bajo Box64 (x86-64 sobre ARM), así que no se pueden usar librerías compiladas.

## Desarrollo

- PC: [Node.js](https://nodejs.org/) 18+ para compilar el frontend.
- Consola: SteamOS ARM Port con Decky Loader.

### Tests

Solo usan la biblioteca estándar. Corren en la consola o en cualquier Linux con Python 3.9+:

```bash
PYTHONPATH=py_modules python3 -m unittest discover -s tests -t . -v
```

`run-tests.sh` corre todo en la consola (tests, lectura del estado real y escritura sobre una copia en `/tmp`) y deja un reporte en `~/Downloads/hft-report.txt`.

### Backend por consola

```bash
export PYTHONPATH=py_modules
python3 -m handheld_fan_tweaker.cli state
python3 -m handheld_fan_tweaker.cli telemetry

# Escritura sobre una copia, sin tocar el sistema:
mkdir -p /tmp/hft/etc /tmp/hft/usr/lib/odin3
cp /etc/odin3.conf /tmp/hft/etc/ && touch /tmp/hft/usr/lib/odin3/odin3d
python3 -m handheld_fan_tweaker.cli --root /tmp/hft --dry-run set silent "50:0,60:40,75:120,90:255"
python3 -m handheld_fan_tweaker.cli --root /tmp/hft --dry-run reset silent
```

## Desinstalar y volver atrás

- Curvas: botón **Restore original curve** en cada perfil.
- A mano: `sudo cp /etc/odin3.conf.handheldfantweaker.bak /etc/odin3.conf && sudo systemctl kill --signal=HUP odin3d`
- Plugin: Decky → ⚙️ Ajustes → Plugins → HandheldFanTweaker → Uninstall.

## Limitaciones

- Solo se probó en una AYN Odin 3.
- En las consolas con `konkrd`, la edición queda deshabilitada hasta que el daemon lea `[curves]` desde su `.conf`.
- La temperatura del panel se calcula como la describe el daemon (promedio de las zonas de CPU/GPU más calientes), pero se mide aparte y puede diferir unos grados.
- Se editan los tres perfiles que ya existen; no se pueden crear perfiles nuevos.

## Autor

**Sleoier**: idea, dirección y pruebas en hardware. El código se generó con vibecoding (Claude) bajo su supervisión.

## Licencia

[BSD-3-Clause](LICENSE)
