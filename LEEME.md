# Pronósticos NFL: actualización automática

Este proyecto descarga los datos de la NFL, corre el modelo y publica la página de pronósticos **solo**, varias veces por semana. No necesitas abrir ningún chat.

## Qué hace y cuándo (hora de Monterrey, aprox.)

| Día | Hora | Para qué |
|---|---|---|
| Martes | 09:00 | Cierra la semana: resultados, histórico y registro. Prepara la siguiente. |
| Miércoles | 09:00 | Primer reporte de lesiones. |
| Jueves | 14:30 | Antes del partido del jueves. |
| Viernes | 16:30 | Estatus oficial de lesiones. |
| Sábado | 16:00 | Lesiones finales y clima del domingo. |
| Domingo | 06:00, 09:30, 13:15, 17:15 | Antes de cada bloque de partidos. |
| Lunes | 16:00 | Antes del partido del lunes. |

GitHub a veces retrasa estas ejecuciones de 10 a 30 minutos. Los picks de cada partido se congelan solos en cuanto empieza.

## Qué hay en cada carpeta

- `state/`: la "memoria" del modelo (picks congelados, registro en vivo, calibraciones). **No borres esta carpeta.**
- `docs/index.html`: la página publicada. Se regenera sola.
- `.github/workflows/actualizar.yml`: los horarios automáticos.
- Archivos `.py`: el modelo.

## Correrlo a mano

Pestaña **Actions** → **Actualizar pronosticos NFL** → **Run workflow**. Tarda entre 10 y 20 minutos.

## Ajustes manuales opcionales

- `state/wind.json`: viento en mph por partido (ej. `{"2026_09_GB_NE": 18}`). El clima se carga solo; esto es para corregirlo.
- `state/roof.json`: techo cerrado (ej. `{"2026_09_DAL_IND": "closed"}`). Los estadios con techo retráctil se asumen cerrados.
