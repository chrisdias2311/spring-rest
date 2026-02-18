import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# --- Enterprise Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DOC_PROJECTION] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIDocumentProjector:
    """
    SCRUM-102 Implementation: AI Document Projection Layer
    
    This layer monitors the incoming stream of engineering signals and 
    collapses them into a single-row "Projection". This projection 
    is the source of truth for AI-generated release notes and GTM intelligence.
    
    Acceptance Criteria:
    - Aggregate engineering + business signals
    - Generate structured JSON projection
    - Store content_text for embedding pipeline
    - Compute confidence score
    """

    def __init__(self, release_external_id: str):
        self.release_external_id = release_external_id
        self.signals_buffer: List[Dict[str, Any]] = []
        logger.info(f"Projector initialized for Release Context: {self.release_external_id}")

    def add_signal(self, signal: Dict[str, Any]):
        """Adds a normalized signal to the aggregation buffer."""
        logger.info(f"Signal received from {signal['source_provider']}. Ingesting to projection buffer.")
        self.signals_buffer.append(signal)

    def calculate_confidence_score(self) -> float:
        """
        Computes a confidence score based on signal diversity and density.
        Higher diversity (GitHub + Jira) results in higher confidence.
        """
        if not self.signals_buffer:
            return 0.0
            
        sources = {s['source_provider'] for s in self.signals_buffer}
        base_score = min(len(self.signals_buffer) * 0.1, 0.5) # Density component
        diversity_bonus = 0.5 if len(sources) > 1 else 0.2    # Diversity component
        
        score = base_score + diversity_bonus
        return min(round(score, 2), 1.0)

    def generate_summaries(self) -> Dict[str, str]:
        """
        Simulates AI-driven summarization of the aggregated signal stream.
        In production, this would call an LLM (e.g., GPT-4 or Gemini) with
        the signal buffer as context.
        """
        tech_events = [s for s in self.signals_buffer if s['source_provider'] == 'github']
        biz_events = [s for s in self.signals_buffer if s['source_provider'] == 'jira']

        technical_summary = (
            f"Release includes {len(tech_events)} significant engineering events. "
            "Key focus on infrastructure stability and PR merges into release-intelligence repo."
        ) if tech_events else "No significant technical signals detected."

        business_summary = (
            f"Business status: {len(biz_events)} items progressed. "
            "GTM alignment is high based on Jira transition flows."
        ) if biz_events else "No significant business signals detected."

        return {
            "technical_summary": technical_summary,
            "business_summary": business_summary
        }

    def project(self) -> Dict[str, Any]:
        """
        Executes the projection logic to produce a single 'AI Document' row.
        """
        logger.info(f"Starting projection cycle for Release: {self.release_external_id}")
        
        if not self.signals_buffer:
            logger.warning("No signals to project. Generating empty intelligence frame.")
            
        summaries = self.generate_summaries()
        confidence = self.calculate_confidence_score()
        
        # Construct the final projection object (AI Document)
        ai_document = {
            "id": f"doc_{self.release_external_id}_{datetime.utcnow().strftime('%Y%m%d')}",
            "release_external_id": self.release_external_id,
            "version": datetime.utcnow().timestamp(),
            "projection_schema": "v2.1-stable",
            "content": {
                "technical": summaries['technical_summary'],
                "business": summaries['business_summary'],
                "raw_signal_count": len(self.signals_buffer)
            },
            "content_text": f"{summaries['technical_summary']} {summaries['business_summary']}",
            "confidence_score": confidence,
            "metadata": {
                "ingestion_window_end": datetime.utcnow().isoformat(),
                "provider_diversity": list({s['source_provider'] for s in self.signals_buffer})
            }
        }
        
        logger.info(f"Projection COMPLETED. Confidence: {confidence}. Finalizing write to ai_documents table.")
        return ai_document

# --- Mock Integration Scenario ---
if __name__ == "__main__":
    print("\n=== AI DOCUMENT PROJECTION SYSTEM (SCRUM-102) ===\n")
    
    projector = AIDocumentProjector(release_external_id="PROJ-2024-BETA")
    
    # Simulate a stream of signals coming from SignalProcessor
    mock_signals = [
        {
            "source_provider": "github",
            "normalized_event": "PULL_REQUEST_MERGED",
            "metadata": {"actor": "alice", "context_summary": "Merge core logic"}
        },
        {
            "source_provider": "jira",
            "normalized_event": "TRANSITION_TO_DONE",
            "metadata": {"actor": "bob", "context_summary": "Issue completion"}
        },
        {
            "source_provider": "github",
            "normalized_event": "DEPLOYMENT_SUCCESSFUL",
            "metadata": {"actor": "ci_bot", "context_summary": "Prod deploy"}
        }
    ]
    
    for sig in mock_signals:
        projector.add_signal(sig)
        
    final_doc = projector.project()
    print(f"\n[STRUCTURED AI DOCUMENT]:\n{json.dumps(final_doc, indent=2)}")
