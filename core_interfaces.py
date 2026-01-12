"""
Core interfaces and a lightweight extraction pipeline to reduce coupling.

Adopts a Ports & Adapters style:
- Source: where input comes from (local file, SharePoint, etc.)
- Extractor: how knowledge is produced (paper/talk/repo agents)
- LLMProvider: model client used by extractors (Foundry, OpenAI, etc.)
- Sink: where artifacts are stored (filesystem, SharePoint, API)
- Notifier: how interested parties are notified (Teams, flows)

This module is intentionally minimal and can be adopted incrementally.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:  # pragma: no cover
        """Return a model-generated string for the given prompt and optional context."""


@runtime_checkable
class Source(Protocol):
    def fetch(self, resource_id: str) -> Any:  # pragma: no cover
        """Return raw input for the given resource identifier (path, URL, drive ID, etc.)."""


@runtime_checkable
class Extractor(Protocol):
    def extract(self, raw: Any, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:  # pragma: no cover
        """Transform raw input into a structured artifact dictionary."""


@runtime_checkable
class Sink(Protocol):
    def save(self, artifact: Dict[str, Any]) -> str:  # pragma: no cover
        """Persist the artifact and return a storage location (URI or path)."""


@runtime_checkable
class Notifier(Protocol):
    def notify(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:  # pragma: no cover
        """Send a notification (Teams, flow, log, etc.)."""


@dataclass
class ExtractionPipeline:
    source: Source
    extractor: Extractor
    sink: Sink
    notifier: Optional[Notifier] = None
    provider: Optional[LLMProvider] = None

    def run(self, resource_id: str) -> Dict[str, Any]:
        """Fetch → Extract → Save → Notify; returns artifact with `location` and `status`."""
        raw = self.source.fetch(resource_id)
        artifact = self.extractor.extract(raw, provider=self.provider)
        location = self.sink.save(artifact)
        artifact["location"] = location
        artifact["status"] = "saved"
        if self.notifier:
            title = artifact.get("title") or "Extraction Complete"
            self.notifier.notify(f"{title}", meta={"location": location, "id": artifact.get("id")})
        return artifact


# Minimal local implementations for quick adoption and examples -----------------

class LocalFileSource:
    """Reads a local file and returns its text content; falls back to bytes."""

    def fetch(self, resource_id: str) -> Any:
        p = Path(resource_id)
        if not p.exists():
            raise FileNotFoundError(f"No such file: {resource_id}")
        data = p.read_bytes()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data


class LocalJSONSink:
    """Writes artifacts as JSON files to `knowledge-agent-poc/outputs/pipeline`."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = base_dir or Path(__file__).parent / "outputs" / "pipeline"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, artifact: Dict[str, Any]) -> str:
        import json
        name = artifact.get("id") or artifact.get("title") or "artifact"
        safe = "".join(c for c in str(name) if c.isalnum() or c in ("-", "_"))
        path = self.base_dir / f"{safe}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(artifact, f, ensure_ascii=False, indent=2)
        return str(path)


class NoopNotifier:
    def notify(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:  # pragma: no cover
        # Intentionally minimal: adopt Teams/flows adapters where needed.
        pass


class DummyProvider:
    """A tiny provider useful for tests and local demos."""

    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        suffix = f" | ctx={len(context or {})}" if context else ""
        return f"echo:{prompt}{suffix}"
