#!/bin/bash
cd /var/www/timbu/staging/travel.api
source env/bin/activate
/var/www/timbu/staging/travel.api/env/bin/gunicorn -c scripts/deploy/config.py main:app