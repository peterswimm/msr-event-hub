"""
Microsoft 365 Integration Examples for Knowledge Agent

Demonstrates how to use the Knowledge Agent with Microsoft 365 services:
- SharePoint document extraction
- OneDrive file extraction
- Batch processing of SharePoint libraries
- Teams notifications
- Enterprise workflows
"""

import sys
import os
import asyncio
from pathlib import Path

# Add to path
sys.path.insert(0, os.path.dirname(__file__))

from knowledge_agent_bot import KnowledgeExtractionAgent
from integrations.m365_connector import M365KnowledgeConnector


# ========== Example 1: Extract from SharePoint Document ==========

def example_1_sharepoint_extraction():
    """Extract knowledge from a SharePoint document"""
    print("=" * 60)
    print("Example 1: SharePoint Document Extraction")
    print("=" * 60)

    # Initialize agent with M365 enabled
    agent = KnowledgeExtractionAgent(enable_m365=True)

    # Extract from SharePoint
    result = agent.extract_from_sharepoint(
        site_id="contoso.sharepoint.com,abc-123,def-456",
        file_path="/Shared Documents/Research/transformer_paper.pdf",
        save_to_sharepoint=True
    )

    if result["success"]:
        print(f"\n✅ Successfully extracted: {result['title']}")
        print(f"Confidence: {result['confidence']:.0%}")
        print(f"Source: {result['m365_source']['web_url']}")

        if 'sharepoint_urls' in result:
            print(f"\nSaved to SharePoint:")
            print(f"  JSON: {result['sharepoint_urls']['json_url']}")
            print(f"  Summary: {result['sharepoint_urls']['markdown_url']}")
    else:
        print(f"❌ Extraction failed: {result['error']}")

    print()


# ========== Example 2: Extract from OneDrive ==========

def example_2_onedrive_extraction():
    """Extract knowledge from OneDrive file"""
    print("=" * 60)
    print("Example 2: OneDrive File Extraction")
    print("=" * 60)

    agent = KnowledgeExtractionAgent(enable_m365=True)

    result = agent.extract_from_onedrive(
        file_path="/Documents/Research/talk_transcript.txt",
        save_to_onedrive=True
    )

    if result["success"]:
        print(f"\n✅ Successfully extracted: {result['title']}")
        print(f"Confidence: {result['confidence']:.0%}")

        if 'onedrive_urls' in result:
            print(f"\nSaved to OneDrive:")
            print(f"  JSON: {result['onedrive_urls']['json_url']}")
            print(f"  Summary: {result['onedrive_urls']['markdown_url']}")
    else:
        print(f"❌ Extraction failed: {result['error']}")

    print()


# ========== Example 3: SharePoint with Teams Notification ==========

def example_3_sharepoint_with_teams():
    """Extract from SharePoint and notify Teams channel"""
    print("=" * 60)
    print("Example 3: SharePoint + Teams Notification")
    print("=" * 60)

    agent = KnowledgeExtractionAgent(enable_m365=True)

    result = agent.extract_from_sharepoint(
        site_id="contoso.sharepoint.com,abc-123,def-456",
        file_path="/Shared Documents/AI Research/paper.pdf",
        save_to_sharepoint=True,
        notify_teams=True,
        team_id="19:team_abc123@thread.tacv2",
        channel_id="19:channel_xyz789@thread.tacv2"
    )

    if result["success"]:
        print(f"\n✅ Successfully extracted: {result['title']}")

        if result.get('teams_notification') == 'sent':
            print("✉️ Teams notification sent successfully")
    else:
        print(f"❌ Extraction failed: {result['error']}")

    print()


# ========== Example 4: Batch Process SharePoint Library ==========

def example_4_batch_processing():
    """Process multiple documents from SharePoint library"""
    print("=" * 60)
    print("Example 4: Batch Processing SharePoint Library")
    print("=" * 60)

    # Initialize connector
    connector = M365KnowledgeConnector()
    agent = KnowledgeExtractionAgent(enable_m365=True)

    site_id = "contoso.sharepoint.com,abc-123,def-456"
    library_path = "/Shared Documents/Research Papers"

    # This is a simplified example - in practice, you'd use Graph API to list files
    pdf_files = [
        "/Shared Documents/Research Papers/paper1.pdf",
        "/Shared Documents/Research Papers/paper2.pdf",
        "/Shared Documents/Research Papers/paper3.pdf"
    ]

    results = []
    for file_path in pdf_files:
        print(f"\nProcessing: {file_path}")
        result = agent.extract_from_sharepoint(
            site_id=site_id,
            file_path=file_path,
            save_to_sharepoint=True
        )

        if result["success"]:
            print(f"  ✅ {result['title']} (confidence: {result['confidence']:.0%})")
            results.append(result)
        else:
            print(f"  ❌ Failed: {result['error']}")

    print(f"\n📊 Batch complete: {len(results)}/{len(pdf_files)} successful")
    print()


# ========== Example 5: Direct M365 Connector Usage ==========

def example_5_direct_connector():
    """Use M365 connector directly for custom workflows"""
    print("=" * 60)
    print("Example 5: Direct M365 Connector Usage")
    print("=" * 60)

    connector = M365KnowledgeConnector()

    # Get site information
    site_path = "contoso.sharepoint.com:/sites/Research"
    site = connector.get_site_by_path(site_path)
    print(f"\nSite: {site.get('displayName', 'Unknown')}")
    print(f"URL: {site.get('webUrl', 'N/A')}")

    # Get drive (document library)
    drive = connector.get_site_drive(site['id'])
    print(f"\nDrive: {drive.get('name', 'Unknown')}")
    print(f"Drive ID: {drive['id']}")

    # Download a file
    try:
        content = connector.download_file(
            site['id'],
            "/Shared Documents/sample.pdf"
        )
        print(f"\nDownloaded file: {len(content)} bytes")
    except Exception as e:
        print(f"\nFailed to download: {e}")

    print()


# ========== Example 6: Custom Artifact Storage ==========

def example_6_custom_storage():
    """Extract and save to custom SharePoint location"""
    print("=" * 60)
    print("Example 6: Custom Artifact Storage")
    print("=" * 60)

    agent = KnowledgeExtractionAgent(enable_m365=True)
    connector = agent.m365

    # Extract from local file first
    result = agent.extract_paper_knowledge("papers/local_paper.pdf")

    if result["success"]:
        # Get artifact
        artifact_data = result["full_artifact"]

        # Upload to custom SharePoint location
        site_id = "contoso.sharepoint.com,abc-123,def-456"

        # Create folder for this extraction
        from datetime import datetime
        folder_name = f"Knowledge Artifacts/{datetime.now().strftime('%Y/%m')}"

        try:
            connector.create_folder(site_id, folder_name)
        except:
            pass  # Folder might already exist

        # Upload JSON
        import json
        json_content = json.dumps(artifact_data, indent=2).encode()

        connector.upload_file(
            site_id,
            folder_name,
            f"{artifact_data['title'].replace(' ', '_')}.json",
            json_content
        )

        print(f"✅ Uploaded to custom location: {folder_name}")

    print()


# ========== Example 7: Error Handling and Retry ==========

def example_7_error_handling():
    """Demonstrate robust error handling"""
    print("=" * 60)
    print("Example 7: Error Handling and Retry")
    print("=" * 60)

    agent = KnowledgeExtractionAgent(enable_m365=True)

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        result = agent.extract_from_sharepoint(
            site_id="contoso.sharepoint.com,abc-123,def-456",
            file_path="/Shared Documents/paper.pdf",
            save_to_sharepoint=True
        )

        if result["success"]:
            print(f"✅ Success on attempt {retry_count + 1}")
            break
        else:
            retry_count += 1
            print(f"❌ Attempt {retry_count} failed: {result['error']}")

            if retry_count < max_retries:
                print(f"Retrying in 5 seconds...")
                import time
                time.sleep(5)
            else:
                print(f"Failed after {max_retries} attempts")

    print()


# ========== Example 8: Enterprise Workflow ==========

def example_8_enterprise_workflow():
    """Complete enterprise workflow: Extract → Store → Notify"""
    print("=" * 60)
    print("Example 8: Enterprise Workflow")
    print("=" * 60)

    agent = KnowledgeExtractionAgent(enable_m365=True)

    # Configuration
    config = {
        "site_id": "contoso.sharepoint.com,abc-123,def-456",
        "source_library": "/Shared Documents/Incoming",
        "artifact_library": "/Knowledge Artifacts",
        "team_id": "19:team_abc@thread.tacv2",
        "channel_id": "19:channel_xyz@thread.tacv2"
    }

    # Files to process
    files_to_process = [
        "/Shared Documents/Incoming/new_paper.pdf"
    ]

    for file_path in files_to_process:
        print(f"\n📄 Processing: {file_path}")

        # Step 1: Extract
        result = agent.extract_from_sharepoint(
            site_id=config["site_id"],
            file_path=file_path,
            save_to_sharepoint=True,
            notify_teams=True,
            team_id=config["team_id"],
            channel_id=config["channel_id"]
        )

        if result["success"]:
            # Step 2: Log success
            print(f"  ✅ Extracted: {result['title']}")
            print(f"  📊 Confidence: {result['confidence']:.0%}")

            # Step 3: Verify artifacts saved
            if 'sharepoint_urls' in result:
                print(f"  💾 Artifacts saved")

            # Step 4: Verify notification sent
            if result.get('teams_notification') == 'sent':
                print(f"  ✉️ Team notified")

            print(f"  ✨ Workflow complete")
        else:
            print(f"  ❌ Failed: {result['error']}")

    print()


# ========== Main Execution ==========

if __name__ == "__main__":
    print("\n")
    print("=" * 60)
    print("Knowledge Agent - Microsoft 365 Integration Examples")
    print("=" * 60)
    print()

    # Check if M365 integration is available
    try:
        from integrations.m365_connector import M365KnowledgeConnector
        m365_available = True
    except ImportError as e:
        print(f"❌ Microsoft 365 integration not available: {e}")
        print("Make sure graph_auth.py and graph_service.py are configured")
        m365_available = False

    if m365_available:
        print("Available examples:")
        print("1. SharePoint Document Extraction")
        print("2. OneDrive File Extraction")
        print("3. SharePoint + Teams Notification")
        print("4. Batch Processing SharePoint Library")
        print("5. Direct M365 Connector Usage")
        print("6. Custom Artifact Storage")
        print("7. Error Handling and Retry")
        print("8. Enterprise Workflow")
        print()

        choice = input("Select example (1-8) or 'all' to run all: ").strip()

        if choice == 'all':
            example_1_sharepoint_extraction()
            example_2_onedrive_extraction()
            example_3_sharepoint_with_teams()
            example_4_batch_processing()
            example_5_direct_connector()
            example_6_custom_storage()
            example_7_error_handling()
            example_8_enterprise_workflow()
        elif choice == '1':
            example_1_sharepoint_extraction()
        elif choice == '2':
            example_2_onedrive_extraction()
        elif choice == '3':
            example_3_sharepoint_with_teams()
        elif choice == '4':
            example_4_batch_processing()
        elif choice == '5':
            example_5_direct_connector()
        elif choice == '6':
            example_6_custom_storage()
        elif choice == '7':
            example_7_error_handling()
        elif choice == '8':
            example_8_enterprise_workflow()
        else:
            print("Invalid choice. Run with --help for usage.")

    print("\nExamples complete!")
    print()
