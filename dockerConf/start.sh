#!/bin/sh

set -o errexit

gunicorn --workers 10 --threads 2 -b 0.0.0.0:8050 app:server