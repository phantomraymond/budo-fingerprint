# This file runs the main backend flask server
Set-Location budo-fingerprint
Set-Location $(git rev-parse --show-toplevel)
Set-Location backend
py flask --debug run -h 0.0.0.0 -p 5000