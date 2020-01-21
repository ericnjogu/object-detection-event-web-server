#~/bin/bash
source activate web-server-events
export PYTHONPATH=.:proto/generated
$*
