#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

export START_MONITORING=true
export START_JENKINS=true
export START_MINIKUBE_FOR_JENKINS=true

exec ./start-dev.sh
