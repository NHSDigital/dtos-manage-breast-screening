docker compose --profile integration run test-dependencies sleep 0.1
uv run pytest $(dirname "$(realpath $0)")
test_exit_code=$?
docker compose --profile integration down --volumes --remove-orphans
exit $test_exit_code
