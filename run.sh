#!/bin/bash
set -e
python datos.py && python features.py && python qbprior.py && python features2.py
python weather.py || echo "Clima no disponible: se usa el valor estandar"
python predict.py && python props_week.py && python props_extra.py && python player_ctx.py
python history.py && python calib.py
python update_factors.py && python log_update.py && python snap.py && python build_page.py
