
export DJANGO_SETTINGS_MODULE="test_settings"

python3 -m coverage run --source="rest_framework_statelessauth" -m django test rest_framework_statelessauth
python3 -m coverage report --fail-under 100
