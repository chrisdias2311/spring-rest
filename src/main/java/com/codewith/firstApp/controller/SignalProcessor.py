import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# --- Enterprise Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SIGNAL_INTEL] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalIntelligencePipeline:
    """
    SCRUM-101 Implementation: Signal Processing Pipeline
    
    This pipeline is responsible for ingesting fragmented engineering signals 
    from GitHub and Jira, normalizing them into a unified "Signal" format, 
    and preparing them for GTM (Go-To-Market) visibility.
    
    Key Responsibilities:
    - Webhook payload normalization
    - Idempotency guarding using SHA-256 versioning
    - Release intelligence linking (release_external_id)
    - Metadata persistence (Supabase/RDS mock)
    """

    def __init__(self, release_external_id: str):
        """
        Initialize the pipeline for a specific release context.
        
        Args:
            release_external_id (str): The global ID of the release this pipeline is monitoring.
        """
        self.release_external_id = release_external_id
        self.processed_signals_vault = set()  # Mocking a distributed Redis cache for idempotency
        logger.info(f"Pipeline initialized for Release: {self.release_external_id}")

    def handle_github_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Standard parser for GitHub Webhook events (PR merged, Commit pushed).
        
        Extracts relevant engineering signals like contributor, diff size, and branch.
        """
        logger.info("Processing incoming GitHub webhook...")
        
        try:
            # Extract GitHub-specific data points
            repo_name = payload.get("repository", {}).get("full_name")
            sender = payload.get("sender", {}).get("login")
            action = payload.get("action", "push") # Default to push if not specified
            
            # Simulated normalization trigger
            signal_data = {
                "source": "github",
                "origin_id": str(payload.get("id")),
                "actor": sender,
                "event_type": action,
                "context": f"Repository: {repo_name}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return self.normalize_to_signal(signal_data)
        except Exception as e:
            logger.error(f"GitHub Parse Error: {str(e)}")
            return None

    def handle_jira_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Standard parser for Jira Webhook events (Issue updated, Sprint changed).
        
        Extracts status transitions and story point updates.
        """
        logger.info("Processing incoming Jira webhook...")
        
        try:
            issue_key = payload.get("issue", {}).get("key")
            status = payload.get("issue", {}).get("fields", {}).get("status", {}).get("name")
            user = payload.get("user", {}).get("displayName")
            
            signal_data = {
                "source": "jira",
                "origin_id": issue_key,
                "actor": user,
                "event_type": f"TRANSITION_TO_{status.upper()}",
                "context": f"Issue: {issue_key} moved to {status}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return self.normalize_to_signal(signal_data)
        except Exception as e:
            logger.error(f"Jira Parse Error: {str(e)}")
            return None

    def normalize_to_signal(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts disparate payload formats into the Shiplog Unified Signal Schema.
        
        Required fields for Release Intelligence:
        - signal_id (UUID)
        - signal_version (SHA Fingerprint)
        - release_external_id (Linkage)
        """
        logger.info(f"Normalizing signal from {raw_data['source']}...")
        
        # 1. Create unique identity
        signal_id = str(uuid.uuid4())
        
        # 2. Generate Idempotency Key (Signal Versioning)
        # We hash the source + origin_id + event_type to ensure we don't process
        # the exact same event twice even if the webhook retries.
        raw_string = f"{raw_data['source']}:{raw_data['origin_id']}:{raw_data['event_type']}"
        signal_version = hashlib.sha256(raw_string.encode()).hexdigest()
        
        # 3. Final Unified Signal Object
        unified_signal = {
            "signal_id": signal_id,
            "signal_version": signal_version,
            "release_external_id": self.release_external_id,
            "source_provider": raw_data['source'],
            "normalized_event": raw_data['event_type'].upper(),
            "metadata": {
                "actor": raw_data['actor'],
                "context_summary": raw_data['context'],
                "raw_timestamp": raw_data['timestamp']
            },
            "ingested_at": datetime.utcnow().isoformat()
        }
        
        return self.apply_idempotency_guard(unified_signal)

    def apply_idempotency_guard(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ensures that duplicate signals are ignored.
        
        Acceptance Criteria: Duplicate signals ignored using versioning.
        """
        version = signal['signal_version']
        
        if version in self.processed_signals_vault:
            logger.warning(f"DUPLICATE DETECTED: Signal version {version[:10]} already exists. Dropping.")
            return None
            
        logger.info(f"NEW SIGNAL: Version {version[:10]} is unique.")
        self.processed_signals_vault.add(version)
        return self.persist_signal_metadata(signal)

    def persist_signal_metadata(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persists signal metadata for traceability.
        Simulates writes to RDS and log streaming to Supabase.
        """
        logger.info(f"Persisting Signal {signal['signal_id']} to RDS (Signals Table)")
        logger.info(f"Streaming Signal Audit to Supabase for GTM visibility")
        
        # Mocking the database "Save" operation
        # In production, this would be: 
        # db.execute("INSERT INTO signals ...", signal)
        
        return signal

# --- Demonstration Scenario ---
if __name__ == "__main__":
    print("\n=== STARTING SIGNAL PROCESSING PIPELINE (SCRUM-101) ===\n")
    
    # Target release for GTM visibility
    PIPELINE = SignalIntelligencePipeline(release_external_id="RLS-2024-ALPHA")
    
    # 1. Mock GitHub Payload (PR Merged)
    github_payload = {
        "id": 123456,
        "action": "pull_request_merged",
        "repository": {"full_name": "shiplog/release-intelligence"},
        "sender": {"login": "engineering_lead"}
    }
    
    print("\n--- TEST: GITHUB PR MERGE ---")
    processed_github = PIPELINE.handle_github_webhook(github_payload)
    if processed_github:
        print(f"Result: {json.dumps(processed_github, indent=2)}")

    # 2. Mock Jira Payload (Status Change)
    jira_payload = {
        "issue": {
            "key": "CORE-101",
            "fields": {"status": {"name": "In Review"}}
        },
        "user": {"displayName": "Product Manager"}
    }
    
    print("\n--- TEST: JIRA STATUS CHANGE ---")
    processed_jira = PIPELINE.handle_jira_webhook(jira_payload)
    if processed_jira:
        print(f"Result: {json.dumps(processed_jira, indent=2)}")

    # 3. TEST IDEMPOTENCY: Re-process the same GitHub payload
    print("\n--- TEST: DUPLICATE DETECTION (GITHUB RETRY) ---")
    retry_github = PIPELINE.handle_github_webhook(github_payload)
    if not retry_github:
        print("Success: Pipeline correctly ignored duplicate signal.")

    print("\n=== PIPELINE DEMONSTRATION COMPLETE ===\n")
