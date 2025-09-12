docker compose --profile end-to-end run test-dependencies sleep 0.1
poetry run pytest $(dirname "$(realpath $0)")
test_exit_code=$?
docker compose --profile end-to-end down --volumes --remove-orphans
exit $test_exit_code