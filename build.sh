#!/usr/bin/env bash
set -eu -o pipefail
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. "$script_dir"/vars
docker build --no-cache -t "$BACKUP_PROOF_IMG_NAME" --build-arg IMAGE_ID="$BACKUP_PROOF_IMG_VERSIONED" .
docker tag "$BACKUP_PROOF_IMG_NAME" "$BACKUP_PROOF_IMG_LATEST"
docker tag "$BACKUP_PROOF_IMG_NAME" "$BACKUP_PROOF_IMG_VERSIONED"

