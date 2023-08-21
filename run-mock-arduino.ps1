# This script runs the main arduino mock server.
Set-Location budo-fingerprint
Set-Location $(git rev-parse --show-toplevel)
Set-Location backend/tests/utils
py -m flask --app mock_arduino_server.py run -h 0.0.0.0 -p 8000