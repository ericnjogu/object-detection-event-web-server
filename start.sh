#~/bin/bash
source activate object_detection_web
export SETTINGS=settings.cfg
python app.py $*
