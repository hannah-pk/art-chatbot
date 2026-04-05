#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py train_model
python manage.py collectstatic --no-input
python manage.py migrate