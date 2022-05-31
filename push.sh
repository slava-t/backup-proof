#!/usr/bin/env bash
set -eu -o pipefail
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. "$script_dir"/vars
docker push "$BACKUP_PROOF_IMG_LATEST"
docker push "$BACKUP_PROOF_IMG_VERSIONED"

