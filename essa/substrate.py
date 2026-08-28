from __future__ import annotations

import os
import platform

from essa.self_model import SubstrateSnapshot


class RuntimeSubstrateInspector:
    """Inspect the current Python runtime without external dependencies."""

    def inspect(self) -> SubstrateSnapshot:
        machine = platform.machine() or "unknown-machine"
        system = platform.system() or "unknown-system"
        python = platform.python_version()
        cpu_count = os.cpu_count() or 1
        return SubstrateSnapshot(
            id=f"{system}-{machine}-python-{python}",
            kind="python_runtime",
            capabilities=(
                "inspect_substrate",
                "persist_self_model",
                "record_history",
                "symbolic_transition",
            ),
            constraints=("no_llm_core",),
            attributes={
                "system": system,
                "machine": machine,
                "python_version": python,
                "cpu_count": cpu_count,
            },
        )
