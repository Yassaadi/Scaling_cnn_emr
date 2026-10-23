#!/bin/bash
# EMR bootstrap action: installs the Python dependencies on every node.
set -euo pipefail
sudo python3 -m pip install --quiet "tensorflow-cpu>=2.15" "pandas>=2.0" "pyarrow>=14" "pillow>=10"
