"""
Microsoft 365-specific schemas for Knowledge Agent

Extends base knowledge schemas with Microsoft 365 metadata and provenance.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class M365SourceType(Enum):
    """Microsoft 365 source types"""
    SHAREPOINT = "sharepoint"
    ONEDRIVE = "onedrive"
    TEAMS_MEETING = "teams_meeting"
    TEAMS_FILE = "teams_file"
    UNKNOWN = "unknown"


@dataclass
class M365SourceMetadata:
    """Microsoft 365 source provenance information

    Tracks where the content came from in Microsoft 365 ecosystem
    for auditing, linking, and compliance purposes.
    """

    # Source identification
    source_type: M365SourceType
    source_url: str  # Full web URL to the source

    # SharePoint-specific
    site_id: Optional[str] = None
    site_url: Optional[str] = None
    drive_id: Optional[str] = None
    drive_name: Optional[str] = None

    # Item details
    item_id: str = ""
    item_name: str = ""
    item_path: str = ""

    # Metadata
    last_modified: Optional[datetime] = None
    last_modified_by: Optional[str] = None
    created: Optional[datetime] = None
    created_by: Optional[str] = None
    file_size: Optional[int] = None  # bytes

    # Permissions and compliance
    sensitivity_label: Optional[str] = None
    has_retention_policy: bool = False

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "source_type": self.source_type.value,
            "source_url": self.source_url,
            "site_id": self.site_id,
            "site_url": self.site_url,
            "drive_id": self.drive_id,
            "drive_name": self.drive_name,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "item_path": self.item_path,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "last_modified_by": self.last_modified_by,
            "created": self.created.isoformat() if self.created else None,
            "created_by": self.created_by,
            "file_size": self.file_size,
            "sensitivity_label": self.sensitivity_label,
            "has_retention_policy": self.has_retention_policy,
            "metadata": self.metadata
        }

    @classmethod
    def from_sharepoint_item(
        cls,
        item: Dict[str, Any],
        site_id: str,
        site_url: str
    ) -> 'M365SourceMetadata':
        """Create from SharePoint item metadata

        Args:
            item: SharePoint item from Graph API
            site_id: SharePoint site ID
            site_url: SharePoint site URL

        Returns:
            M365SourceMetadata instance
        """
        # Parse dates
        last_modified = None
        if 'lastModifiedDateTime' in item:
            try:
                last_modified = datetime.fromisoformat(
                    item['lastModifiedDateTime'].replace('Z', '+00:00')
                )
            except:
                pass

        created = None
        if 'createdDateTime' in item:
            try:
                created = datetime.fromisoformat(
                    item['createdDateTime'].replace('Z', '+00:00')
                )
            except:
                pass

        return cls(
            source_type=M365SourceType.SHAREPOINT,
            source_url=item.get('webUrl', ''),
            site_id=site_id,
            site_url=site_url,
            drive_id=item.get('parentReference', {}).get('driveId', ''),
            item_id=item.get('id', ''),
            item_name=item.get('name', ''),
            item_path=item.get('parentReference', {}).get('path', ''),
            last_modified=last_modified,
            last_modified_by=item.get('lastModifiedBy', {}).get('user', {}).get('displayName', ''),
            created=created,
            created_by=item.get('createdBy', {}).get('user', {}).get('displayName', ''),
            file_size=item.get('size', 0)
        )

    @classmethod
    def from_onedrive_item(cls, item: Dict[str, Any]) -> 'M365SourceMetadata':
        """Create from OneDrive item metadata

        Args:
            item: OneDrive item from Graph API

        Returns:
            M365SourceMetadata instance
        """
        # Parse dates
        last_modified = None
        if 'lastModifiedDateTime' in item:
            try:
                last_modified = datetime.fromisoformat(
                    item['lastModifiedDateTime'].replace('Z', '+00:00')
                )
            except:
                pass

        created = None
        if 'createdDateTime' in item:
            try:
                created = datetime.fromisoformat(
                    item['createdDateTime'].replace('Z', '+00:00')
                )
            except:
                pass

        return cls(
            source_type=M365SourceType.ONEDRIVE,
            source_url=item.get('webUrl', ''),
            item_id=item.get('id', ''),
            item_name=item.get('name', ''),
            item_path=item.get('parentReference', {}).get('path', ''),
            last_modified=last_modified,
            last_modified_by=item.get('lastModifiedBy', {}).get('user', {}).get('displayName', ''),
            created=created,
            created_by=item.get('createdBy', {}).get('user', {}).get('displayName', ''),
            file_size=item.get('size', 0)
        )


@dataclass
class M365ArtifactExtension:
    """Extension to BaseKnowledgeArtifact for Microsoft 365 integration

    Tracks Microsoft 365-specific information about extraction and storage.
    """

    # Source provenance
    m365_source: Optional[M365SourceMetadata] = None

    # Storage locations (where artifact was saved in M365)
    sharepoint_artifact_url: Optional[str] = None
    sharepoint_summary_url: Optional[str] = None
    teams_notification_sent: bool = False
    teams_channel_id: Optional[str] = None

    # Processing metadata
    extracted_from_m365: bool = False
    extraction_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "m365_source": self.m365_source.to_dict() if self.m365_source else None,
            "sharepoint_artifact_url": self.sharepoint_artifact_url,
            "sharepoint_summary_url": self.sharepoint_summary_url,
            "teams_notification_sent": self.teams_notification_sent,
            "teams_channel_id": self.teams_channel_id,
            "extracted_from_m365": self.extracted_from_m365,
            "extraction_timestamp": self.extraction_timestamp.isoformat() if self.extraction_timestamp else None
        }


@dataclass
class M365ExtractionConfig:
    """Configuration for Microsoft 365 extractions"""

    # SharePoint settings
    default_artifact_library: str = "Knowledge Artifacts"
    create_library_if_missing: bool = True
    organize_by_date: bool = True  # Create year/month folders

    # Teams notification settings
    send_teams_notifications: bool = False
    default_team_id: Optional[str] = None
    default_channel_id: Optional[str] = None

    # Processing settings
    include_m365_metadata: bool = True
    preserve_original_filename: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "default_artifact_library": self.default_artifact_library,
            "create_library_if_missing": self.create_library_if_missing,
            "organize_by_date": self.organize_by_date,
            "send_teams_notifications": self.send_teams_notifications,
            "default_team_id": self.default_team_id,
            "default_channel_id": self.default_channel_id,
            "include_m365_metadata": self.include_m365_metadata,
            "preserve_original_filename": self.preserve_original_filename
        }
