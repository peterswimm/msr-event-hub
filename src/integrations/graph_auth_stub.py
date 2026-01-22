"""
Stub for graph_auth module - placeholder for future M365 integration.

When full M365 support is needed, replace this with the actual GraphAuthClient.
"""

import logging

logger = logging.getLogger(__name__)


class GraphAuthError(Exception):
    """Raised when Graph authentication fails"""
    pass


class GraphAuthClient:
    """Stub GraphAuthClient for M365 integration.
    
    This is a placeholder implementation. Full M365 integration requires:
    - Microsoft Graph API setup
    - Service principal or user credentials
    - SharePoint/OneDrive/Teams API permissions
    """

    def __init__(self, *args, **kwargs):
        """Initialize Graph auth client."""
        logger.warning("Using stub GraphAuthClient - M365 integration not fully implemented")
        self.authenticated = False

    async def authenticate(self):
        """Authenticate with Microsoft Graph."""
        logger.warning("Stub authenticate called - M365 authentication not implemented")
        self.authenticated = False
        return False

    async def get_access_token(self):
        """Get access token for Graph API."""
        if not self.authenticated:
            raise GraphAuthError("Not authenticated")
        return None

    async def get_sharepoint_files(self, *args, **kwargs):
        """Stub method for SharePoint file retrieval."""
        raise NotImplementedError("SharePoint integration not implemented")

    async def get_onedrive_files(self, *args, **kwargs):
        """Stub method for OneDrive file retrieval."""
        raise NotImplementedError("OneDrive integration not implemented")

    async def get_teams_messages(self, *args, **kwargs):
        """Stub method for Teams message retrieval."""
        raise NotImplementedError("Teams integration not implemented")
