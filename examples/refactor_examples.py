from __future__ import annotations

"""Small example wiring the new pipeline with local components.

Run:
    python -m knowledge-agent-poc.refactor_examples path/to/input.txt
"""

import sys
from typing import Any, Dict

from .core_interfaces import (
    ExtractionPipeline,
    LocalFileSource,
    LocalJSONSink,
    DummyProvider,
)


class MinimalExtractor:
    """A tiny extractor that wraps raw content into an artifact.

    Replace with Paper/Talk/Repo agents in real usage.
    """

    def extract(self, raw: Any, provider: DummyProvider | None = None) -> Dict[str, Any]:
        text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        title = text.splitlines()[0][:80] if text else "Untitled"
        model_echo = provider.generate(title) if provider else None
        return {
            "id": title.lower().replace(" ", "-")[:40] or "artifact",
            "title": title,
            "summary": model_echo or "",
            "content_preview": text[:240],
            "kind": "demo",
        }


def main(path: str) -> None:
    pipeline = ExtractionPipeline(
        source=LocalFileSource(),
        extractor=MinimalExtractor(),
        sink=LocalJSONSink(),
        provider=DummyProvider(),
    )
    artifact = pipeline.run(path)
    print(f"Saved → {artifact['location']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m knowledge-agent-poc.refactor_examples <path>")
        sys.exit(2)
    main(sys.argv[1])
