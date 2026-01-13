"""
Adapters for Microsoft 365 to fit the core `ExtractionPipeline` Protocols.

These adapters are thin wrappers around `M365KnowledgeConnector` methods.
They allow SharePoint/OneDrive to act as Sources and SharePoint as a Sink,
and Teams as a Notifier, enabling clean orchestration and easy testing.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import sys
import os

# Ensure knowledge-agent-poc is on sys.path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from m365_connector import M365KnowledgeConnector
from core_interfaces import Source, Sink, Notifier


class SharePointSource(Source):
    """Fetches file bytes from SharePoint via `download_file`.

    Construct with site id/path and optional drive name.
    `fetch(resource_id)` expects a file path like "/Shared Documents/file.pdf".
    """

    def __init__(self, connector: M365KnowledgeConnector, site_id: str, drive_name: Optional[str] = None) -> None:
        self.connector = connector
        self.site_id = site_id
        self.drive_name = drive_name

    def fetch(self, resource_id: str) -> Any:
        return self.connector.download_file(self.site_id, resource_id, drive_name=self.drive_name)


class OneDrivePathSource(Source):
    """Fetches file bytes from OneDrive by path using `get_onedrive_file_by_path`.

    `fetch(resource_id)` expects a path like "/Documents/paper.pdf".
    """

    def __init__(self, connector: M365KnowledgeConnector) -> None:
        self.connector = connector

    def fetch(self, resource_id: str) -> Any:
        return self.connector.get_onedrive_file_by_path(resource_id)


class OneDriveSink(Sink):
    """Saves artifacts to OneDrive as JSON in the specified folder."""

    def __init__(self, connector: M365KnowledgeConnector, folder_path: str = "/Documents/Knowledge Artifacts") -> None:
        self.connector = connector
        self.folder_path = folder_path

    def save(self, artifact: Dict[str, Any]) -> str:
        import json

        name = artifact.get("id") or artifact.get("title") or "artifact"
        safe = "".join(c for c in str(name) if c.isalnum() or c in ("-", "_"))
        filename = f"{safe}.json"
        content = json.dumps(artifact, ensure_ascii=False, indent=2).encode("utf-8")
        meta = self.connector.upload_to_onedrive(self.folder_path, filename, content)
        return meta.get("webUrl", filename)


class SharePointSink(Sink):
    """Saves artifacts to a SharePoint folder as JSON.

    Provide `site_id`, `folder_path`, and optional `drive_name`.
    The location returned is the SharePoint `webUrl` of the uploaded file.
    """

    def __init__(self, connector: M365KnowledgeConnector, site_id: str, folder_path: str, drive_name: Optional[str] = None) -> None:
        self.connector = connector
        self.site_id = site_id
        self.folder_path = folder_path
        self.drive_name = drive_name

    def save(self, artifact: Dict[str, Any]) -> str:
        import json

        name = artifact.get("id") or artifact.get("title") or "artifact"
        safe = "".join(c for c in str(name) if c.isalnum() or c in ("-", "_"))
        filename = f"{safe}.json"

        content = json.dumps(artifact, ensure_ascii=False, indent=2).encode("utf-8")
        meta = self.connector.upload_file(
            site_id=self.site_id,
            folder_path=self.folder_path,
            filename=filename,
            content=content,
            drive_name=self.drive_name,
        )
        return meta.get("webUrl", filename)


class TeamsNotifier(Notifier):
    """Posts messages to a Teams channel or chat.

    Provide either `team_id`+`channel_id` for channels, or `chat_id` for chats.
    If both are provided, channel takes precedence.
    """

    def __init__(
        self,
        connector: M365KnowledgeConnector,
        team_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> None:
        self.connector = connector
        self.team_id = team_id
        self.channel_id = channel_id
        self.chat_id = chat_id

    def notify(self, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
        suffix = ""
        if meta and meta.get("location"):
            suffix = f"\n\nArtifact: {meta['location']}"
        html = f"<p>{message}</p>{suffix and f'<p>{suffix}</p>'}"

        if self.team_id and self.channel_id:
            self.connector.post_to_channel(self.team_id, self.channel_id, html)
        elif self.chat_id:
            self.connector.post_to_chat(self.chat_id, html)
        else:
            # No target configured; silently ignore.
            return
