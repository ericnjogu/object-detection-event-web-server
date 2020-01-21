#~/bin/bash
source activate web-server-events
export PYTHONPATH=.:proto/generated
export SETTINGS=settings.cfg
python app.py $*
