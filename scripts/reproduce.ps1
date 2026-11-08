param([string]$Archive = "data/source/python-3.11.18-docs-text.zip", [switch]$WithGeneration)
$ErrorActionPreference = "Stop"
function Run-Checked { param([scriptblock]$Command) & $Command; if ($LASTEXITCODE -ne 0) { throw "Command failed: $Command" } }
Run-Checked { python -m scripts.secure_dvc }
Run-Checked { python -m scripts.ingest $Archive }
Run-Checked { python -m scripts.verify }
Run-Checked { python -m src.evaluation.campaign }
Run-Checked { python -m scripts.prepare_replay }
Run-Checked { python -m scripts.gates }
Run-Checked { python -m pytest tests -q }
if ($WithGeneration) { Run-Checked { python -m src.evaluation.campaign --generation-only } }
