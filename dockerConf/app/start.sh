#!/bin/sh

set -o errexit

gunicorn -w 4 -b 0.0.0.0:8050 app:server