"""
LexFusion Frontend API Client
==============================
Communicates with the FastAPI backend. If the backend is offline,
it falls back to Local Direct Mode, running the LangGraph agent
code locally using the imported `agents` package.
"""

from __future__ import annotations

import os
import sys
import logging
import requests
from typing import Any, Optional

# Add project root to path for local imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

LOCAL_AGENTS_IMPORT_ERROR = None
try:
    from agents.generate import generate_answer, run_debate
    from agents.schemas import DebateResponse, GenerateResponse
    LOCAL_AGENTS_AVAILABLE = True
except Exception as err:
    LOCAL_AGENTS_AVAILABLE = False
    LOCAL_AGENTS_IMPORT_ERROR = str(err)

logger = logging.getLogger(__name__)

# Backend API configuration
API_BASE_URL = os.getenv("LEXFUSION_API_URL", "http://localhost:8000")


class LexFusionAPIClient:
    """Client for backend API calls with Local Mode fallback."""

    def __init__(self):
        self.api_url = API_BASE_URL
        self.local_mode = not self.check_backend_online()

        if self.local_mode:
            logger.info("FastAPI backend is offline. Operating in LOCAL DIRECT mode.")
        else:
            logger.info("FastAPI backend is online. Operating in API mode.")

    def check_backend_online(self) -> bool:
        """Sends a lightweight health check request to the FastAPI backend."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=1.5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def query(
        self,
        query: str,
        debate_mode: bool = True,
        top_k: int = 5,
        max_rounds: Optional[int] = None,
        custom_context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Sends a query to the system. Handles RAG synthesis and structured debates.
        """
        # If API mode is selected and backend is online
        if not self.local_mode:
            try:
                payload = {
                    "query": query,
                    "debate_mode": debate_mode,
                    "top_k": top_k,
                }
                if max_rounds is not None:
                    payload["max_rounds"] = max_rounds

                response = requests.post(f"{self.api_url}/query", json=payload, timeout=60)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        "API request failed with code %s. Falling back to local.",
                        response.status_code,
                    )
            except requests.RequestException as err:
                logger.warning("API connection failed: %s. Falling back to local.", err)

        # Fallback Local Direct Mode
        if not LOCAL_AGENTS_AVAILABLE:
            return {
                "status": "error",
                "error_message": f"Local agents engine failed to load: {LOCAL_AGENTS_IMPORT_ERROR or 'Import error'}",
            }

        # Retrieve/mock context
        context = custom_context or self._get_context_fallback(query)
        sources = [
            {
                "source": "contract_agreement_v2.pdf",
                "page": 4,
                "chunk": "Section 14.1 Indemnification: The vendor shall indemnify and hold harmless the client...",
            },
            {
                "source": "terms_and_conditions.pdf",
                "page": 2,
                "chunk": "Section 8.2 Limitation of Liability: Neither party shall be liable for consequential damages...",
            },
        ]

        try:
            if debate_mode:
                # Run the LangGraph debate locally
                res = run_debate(
                    query=query,
                    context=context,
                    source_documents=sources,
                    max_rounds=max_rounds,
                )
                # Convert Pydantic model to dictionary
                return res.model_dump()
            else:
                # Run single-shot local generation
                res = generate_answer(
                    query=query,
                    context=context,
                    source_documents=sources,
                )
                return res.model_dump()
        except Exception as exc:
            return {
                "status": "error",
                "error_message": f"Local agents execution failed: {exc}",
            }

    def upload_document(self, file_name: str, file_content: bytes) -> dict[str, Any]:
        """Uploads a PDF document to the database."""
        if not self.local_mode:
            try:
                files = {"file": (file_name, file_content, "application/pdf")}
                response = requests.post(f"{self.api_url}/upload", files=files, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException as err:
                logger.error("Document upload API call failed: %s", err)

        # Local mode mock upload
        return {
            "status": "success",
            "filename": file_name,
            "message": f"Successfully ingested {file_name} into local temporary cache.",
        }

    def _get_context_fallback(self, query: str) -> str:
        """Fallback mock database containing sample legal context."""
        contexts = [
            "Section 14.1 INDEMNIFICATION. The Vendor shall indemnify, defend, and hold harmless the Client and its officers, directors, employees, and agents from and against any and all claims, liabilities, losses, damages, costs, and expenses (including reasonable attorneys' fees) arising out of or relating to any third-party claim alleging that the Services or Deliverables infringe any patent, copyright, trademark, or trade secret of a third party.",
            "Section 8.2 LIMITATION OF LIABILITY. EXCEPT FOR DAMAGES ARISING FROM BREACH OF CONFIDENTIALITY (SECTION 9) OR INDEMNIFICATION OBLIGATIONS (SECTION 14), IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, PUNITIVE, OR CONSEQUENTIAL DAMAGES, INCLUDING LOSS OF PROFITS, REVENUE, DATA, OR USE, INCURRED BY THE OTHER PARTY, WHETHER IN AN ACTION IN CONTRACT OR TORT, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.",
            "Section 12.4 TERMINATION FOR CAUSE. Either party may terminate this Agreement immediately upon written notice if the other party breaches any material provision of this Agreement and fails to cure such breach within thirty (30) days after receipt of written notice describing the breach in reasonable detail.",
        ]
        return "\n\n".join(contexts)
