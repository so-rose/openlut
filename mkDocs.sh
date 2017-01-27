SCRIPT_PATH="$(dirname $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}"))/doc"

make -C "$SCRIPT_PATH" doctest
make -C "$SCRIPT_PATH" html
