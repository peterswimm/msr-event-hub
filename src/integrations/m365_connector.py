"""
Microsoft 365 Connector for Knowledge Agent

This module integrates the Knowledge Agent with Microsoft 365 services:
- SharePoint: Download documents, upload artifacts
- OneDrive: Personal file storage access
- Teams: Meeting transcripts, channel notifications

Leverages the existing EventKit Graph authentication and service infrastructure.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Add parent directory to path for EventKit imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    from graph_auth import GraphAuthClient, GraphAuthError
except ImportError:
    # Use stub for M365 integration until full implementation
    from .graph_auth_stub import GraphAuthClient, GraphAuthError
    logger.warning("Using stub GraphAuthClient - full M365 integration not available")

try:
    from settings import Settings
except ImportError:
    # Create minimal Settings stub if not available
    class Settings:
        pass
    logger.warning("Using stub Settings")


class M365ConnectorError(Exception):
    """Raised when Microsoft 365 operations fail"""
    pass


class M365KnowledgeConnector:
    """Connect Knowledge Agent to Microsoft 365 services

    Provides methods to:
    - Download files from SharePoint/OneDrive
    - Upload knowledge artifacts to SharePoint
    - Get Teams meeting transcripts
    - Post summaries to Teams channels
    """

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(
        self,
        auth_client: Optional[GraphAuthClient] = None,
        settings: Optional[Settings] = None
    ):
        """Initialize M365 connector

        Args:
            auth_client: Authenticated GraphAuthClient (creates default if None)
            settings: Application settings (loads default if None)
        """
        # Initialize settings
        if settings is None:
            settings = Settings()
        self.settings = settings

        # Initialize auth client
        if auth_client is None:
            try:
                auth_client = GraphAuthClient(settings)
            except GraphAuthError as e:
                logger.error(f"Failed to initialize Graph auth: {e}")
                raise M365ConnectorError(f"Authentication setup failed: {e}") from e

        self.auth_client = auth_client
        logger.info("Initialized M365KnowledgeConnector")

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for Graph API

        Returns:
            Dict with Authorization and Content-Type headers

        Raises:
            M365ConnectorError: If token acquisition fails
        """
        try:
            token = self.auth_client.get_access_token()
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        except GraphAuthError as e:
            logger.error(f"Failed to get access token: {e}")
            raise M365ConnectorError(f"Authentication failed: {e}") from e

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """Make authenticated request to Graph API

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for httpx request

        Returns:
            Response JSON or content

        Raises:
            M365ConnectorError: If request fails
        """
        import httpx

        url = f"{self.GRAPH_API_BASE}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        # Merge headers
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                )

                # Handle errors
                if response.status_code == 401:
                    raise M365ConnectorError("Authentication failed: Invalid token")
                elif response.status_code == 403:
                    raise M365ConnectorError("Access denied: Insufficient permissions")
                elif response.status_code == 404:
                    raise M365ConnectorError(f"Resource not found: {endpoint}")
                elif response.status_code >= 400:
                    error_msg = response.text[:200] if response.text else "Unknown error"
                    raise M365ConnectorError(
                        f"API error {response.status_code}: {error_msg}"
                    )

                # Return binary content or JSON
                if 'application/json' in response.headers.get('content-type', ''):
                    return response.json()
                else:
                    return response.content

        except httpx.RequestError as e:
            logger.error(f"Network error calling Graph API: {e}")
            raise M365ConnectorError(f"Network error: {e}") from e

    # ========== SharePoint Operations ==========

    def get_site_by_path(self, site_path: str) -> Dict[str, Any]:
        """Get SharePoint site by path

        Args:
            site_path: Site path like "contoso.sharepoint.com:/sites/Research"

        Returns:
            Site object with id, webUrl, etc.
        """
        logger.info(f"Getting SharePoint site: {site_path}")
        return self._make_request("GET", f"sites/{site_path}")

    def get_site_drive(self, site_id: str, drive_name: str = None) -> Dict[str, Any]:
        """Get drive (document library) for a site

        Args:
            site_id: SharePoint site ID
            drive_name: Optional drive name (gets default if None)

        Returns:
            Drive object with id, webUrl, etc.
        """
        if drive_name:
            # Search for specific drive by name
            drives = self._make_request("GET", f"sites/{site_id}/drives")
            for drive in drives.get('value', []):
                if drive.get('name') == drive_name:
                    return drive
            raise M365ConnectorError(f"Drive not found: {drive_name}")
        else:
            # Get default drive
            return self._make_request("GET", f"sites/{site_id}/drive")

    def get_item_by_path(
        self,
        site_id: str,
        item_path: str,
        drive_name: str = None
    ) -> Dict[str, Any]:
        """Get SharePoint item (file/folder) by path

        Args:
            site_id: SharePoint site ID
            item_path: Path to item like "/Shared Documents/file.pdf"
            drive_name: Optional drive name

        Returns:
            Item object with id, name, size, etc.
        """
        drive = self.get_site_drive(site_id, drive_name)
        drive_id = drive['id']

        # URL encode the path
        from urllib.parse import quote
        encoded_path = quote(item_path.strip('/'))

        return self._make_request("GET", f"drives/{drive_id}/root:/{encoded_path}")

    def download_file(
        self,
        site_id: str,
        file_path: str,
        drive_name: str = None
    ) -> bytes:
        """Download file from SharePoint

        Args:
            site_id: SharePoint site ID
            file_path: Path to file like "/Shared Documents/paper.pdf"
            drive_name: Optional drive name

        Returns:
            File content as bytes
        """
        logger.info(f"Downloading SharePoint file: {file_path}")

        # Get item metadata
        item = self.get_item_by_path(site_id, file_path, drive_name)

        # Check if it's a file
        if 'folder' in item:
            raise M365ConnectorError(f"Path is a folder, not a file: {file_path}")

        # Download content
        drive = self.get_site_drive(site_id, drive_name)
        content = self._make_request(
            "GET",
            f"drives/{drive['id']}/items/{item['id']}/content"
        )

        logger.info(f"Downloaded {len(content)} bytes from {file_path}")
        return content

    def upload_file(
        self,
        site_id: str,
        folder_path: str,
        filename: str,
        content: bytes,
        drive_name: str = None
    ) -> Dict[str, Any]:
        """Upload file to SharePoint

        Args:
            site_id: SharePoint site ID
            folder_path: Folder path like "/Knowledge Artifacts"
            filename: File name
            content: File content as bytes
            drive_name: Optional drive name

        Returns:
            Uploaded file metadata
        """
        logger.info(f"Uploading file to SharePoint: {folder_path}/{filename}")

        drive = self.get_site_drive(site_id, drive_name)

        # URL encode the path
        from urllib.parse import quote
        encoded_path = quote(f"{folder_path.strip('/')}/{filename}")

        # Upload content
        result = self._make_request(
            "PUT",
            f"drives/{drive['id']}/root:/{encoded_path}:/content",
            content=content,
            headers={"Content-Type": "application/octet-stream"}
        )

        logger.info(f"Uploaded file: {result.get('webUrl')}")
        return result

    def create_folder(
        self,
        site_id: str,
        folder_path: str,
        drive_name: str = None
    ) -> Dict[str, Any]:
        """Create folder in SharePoint

        Args:
            site_id: SharePoint site ID
            folder_path: Full path to create like "/Knowledge Artifacts/2025"
            drive_name: Optional drive name

        Returns:
            Created folder metadata
        """
        drive = self.get_site_drive(site_id, drive_name)

        # Split path into parent and name
        parent_path = str(Path(folder_path).parent)
        folder_name = Path(folder_path).name

        # Get parent folder
        if parent_path == '.':
            parent_endpoint = f"drives/{drive['id']}/root"
        else:
            from urllib.parse import quote
            encoded_parent = quote(parent_path.strip('/'))
            parent_endpoint = f"drives/{drive['id']}/root:/{encoded_parent}"

        # Create folder
        result = self._make_request(
            "POST",
            f"{parent_endpoint}/children",
            json={
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
        )

        logger.info(f"Created folder: {result.get('webUrl')}")
        return result

    # ========== OneDrive Operations ==========

    def get_onedrive_file(self, file_id: str) -> bytes:
        """Download file from OneDrive

        Args:
            file_id: OneDrive file ID

        Returns:
            File content as bytes
        """
        logger.info(f"Downloading OneDrive file: {file_id}")
        content = self._make_request("GET", f"me/drive/items/{file_id}/content")
        logger.info(f"Downloaded {len(content)} bytes from OneDrive")
        return content

    def get_onedrive_file_by_path(self, file_path: str) -> bytes:
        """Download file from OneDrive by path

        Args:
            file_path: Path to file like "/Documents/paper.pdf"

        Returns:
            File content as bytes
        """
        logger.info(f"Downloading OneDrive file: {file_path}")
        from urllib.parse import quote
        encoded_path = quote(file_path.strip('/'))
        content = self._make_request("GET", f"me/drive/root:/{encoded_path}:/content")
        logger.info(f"Downloaded {len(content)} bytes from OneDrive")
        return content

    def upload_to_onedrive(
        self,
        folder_path: str,
        filename: str,
        content: bytes
    ) -> Dict[str, Any]:
        """Upload file to OneDrive

        Args:
            folder_path: Folder path like "/Documents/Knowledge"
            filename: File name
            content: File content as bytes

        Returns:
            Uploaded file metadata
        """
        logger.info(f"Uploading file to OneDrive: {folder_path}/{filename}")

        from urllib.parse import quote
        encoded_path = quote(f"{folder_path.strip('/')}/{filename}")

        result = self._make_request(
            "PUT",
            f"me/drive/root:/{encoded_path}:/content",
            content=content,
            headers={"Content-Type": "application/octet-stream"}
        )

        logger.info(f"Uploaded file: {result.get('webUrl')}")
        return result

    # ========== Teams Operations ==========

    def get_meeting_transcript(self, meeting_id: str) -> Optional[str]:
        """Get Teams meeting transcript

        Args:
            meeting_id: Teams meeting ID

        Returns:
            Transcript text or None if not available

        Note:
            Requires OnlineMeetings.Read.All permission
        """
        logger.info(f"Getting Teams meeting transcript: {meeting_id}")

        try:
            # Get meeting transcripts
            result = self._make_request(
                "GET",
                f"me/onlineMeetings/{meeting_id}/transcripts"
            )

            transcripts = result.get('value', [])
            if not transcripts:
                logger.warning("No transcripts found for meeting")
                return None

            # Get first transcript content
            transcript_id = transcripts[0]['id']
            content = self._make_request(
                "GET",
                f"me/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
            )

            if isinstance(content, bytes):
                content = content.decode('utf-8')

            logger.info(f"Retrieved transcript ({len(content)} chars)")
            return content

        except M365ConnectorError as e:
            logger.error(f"Failed to get meeting transcript: {e}")
            return None

    def post_to_channel(
        self,
        team_id: str,
        channel_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Post message to Teams channel

        Args:
            team_id: Teams team ID
            channel_id: Channel ID within team
            message: Message content (supports HTML)

        Returns:
            Posted message metadata
        """
        logger.info(f"Posting to Teams channel: {team_id}/{channel_id}")

        result = self._make_request(
            "POST",
            f"teams/{team_id}/channels/{channel_id}/messages",
            json={
                "body": {
                    "contentType": "html",
                    "content": message
                }
            }
        )

        logger.info("Posted message to Teams")
        return result

    def post_to_chat(
        self,
        chat_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Post message to Teams chat

        Args:
            chat_id: Teams chat ID
            message: Message content (supports HTML)

        Returns:
            Posted message metadata
        """
        logger.info(f"Posting to Teams chat: {chat_id}")

        result = self._make_request(
            "POST",
            f"chats/{chat_id}/messages",
            json={
                "body": {
                    "contentType": "html",
                    "content": message
                }
            }
        )

        logger.info("Posted message to chat")
        return result

    # ========== Helper Methods ==========

    def parse_site_path(self, site_url: str) -> str:
        """Parse SharePoint site URL to Graph API path format

        Args:
            site_url: Full URL like "https://contoso.sharepoint.com/sites/Research"

        Returns:
            Graph API path like "contoso.sharepoint.com:/sites/Research"
        """
        # Remove https://
        path = site_url.replace('https://', '').replace('http://', '')

        # Split domain and path
        parts = path.split('/', 1)
        domain = parts[0]
        site_path = f"/{parts[1]}" if len(parts) > 1 else ""

        return f"{domain}:{site_path}"

    def format_artifact_summary(
        self,
        artifact: Any,
        include_links: bool = False,
        sharepoint_urls: Optional[Dict[str, str]] = None
    ) -> str:
        """Format knowledge artifact as Teams message

        Args:
            artifact: BaseKnowledgeArtifact instance
            include_links: Include SharePoint links
            sharepoint_urls: Optional dict with 'json_url' and 'markdown_url'

        Returns:
            HTML formatted message for Teams
        """
        confidence_emoji = "🟢" if artifact.confidence_score >= 0.8 else "🟡" if artifact.confidence_score >= 0.6 else "🔴"

        html = f"""
<h2>🎯 Knowledge Extraction Complete</h2>

<strong>Title:</strong> {artifact.title}<br/>
<strong>Type:</strong> {artifact.source_type.value.title()}<br/>
<strong>Contributors:</strong> {', '.join(artifact.contributors[:3])}{'...' if len(artifact.contributors) > 3 else ''}<br/>
<strong>Confidence:</strong> {confidence_emoji} {artifact.confidence_score:.0%}<br/>

<h3>Overview</h3>
<p>{artifact.plain_language_overview[:300]}{'...' if len(artifact.plain_language_overview) > 300 else ''}</p>

<h3>Key Methods</h3>
<p>{artifact.key_methods_approach[:200]}{'...' if len(artifact.key_methods_approach) > 200 else ''}</p>

<h3>Potential Impact</h3>
<p>{artifact.potential_impact[:200]}{'...' if len(artifact.potential_impact) > 200 else ''}</p>
"""

        if include_links and sharepoint_urls:
            html += f"""
<h3>📁 Files</h3>
<ul>
<li><a href="{sharepoint_urls.get('json_url', '#')}">JSON Artifact</a></li>
<li><a href="{sharepoint_urls.get('markdown_url', '#')}">Markdown Summary</a></li>
</ul>
"""

        html += f"""
<p><em>Extracted on {artifact.extraction_date.strftime('%Y-%m-%d %H:%M')} using {artifact.extraction_model}</em></p>
"""

        return html


# Convenience function for quick initialization
def create_connector(
    settings: Optional[Settings] = None
) -> M365KnowledgeConnector:
    """Create and initialize M365KnowledgeConnector

    Args:
        settings: Optional Settings instance

    Returns:
        Initialized M365KnowledgeConnector

    Raises:
        M365ConnectorError: If initialization fails
    """
    return M365KnowledgeConnector(settings=settings)
