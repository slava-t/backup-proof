#!/usr/bin/env bash
set -eu -o pipefail
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. "$script_dir"/vars
docker build --no-cache -t "$BACKUP_PROOF_PG12_IMG_NAME" .
docker tag "$BACKUP_PROOF_PG12_IMG_NAME" "$BACKUP_PROOF_PG12_IMG_LATEST"
docker tag "$BACKUP_PROOF_PG12_IMG_NAME" "$BACKUP_PROOF_PG12_IMG_VERSIONED"

