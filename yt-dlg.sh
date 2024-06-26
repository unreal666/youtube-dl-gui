#!/usr/bin/env sh
exec "${PYTHON:-python3}" -Werror "$(dirname "$(realpath "$0")")/youtube_dl_gui/__main__.py" "$@"
