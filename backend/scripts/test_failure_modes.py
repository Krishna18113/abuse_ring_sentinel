import os
import sys
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure backend root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.app import app
from app.risk.investigator import investigate_customer
from app.ai.service import explain_risk, generate_fallback_explanation

class TestFailureModes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
    def test_invalid_customer_id(self):
        """Verify invalid customer ID returns 404 with clean error detail."""
        resp = self.client.get("/api/risk/customers/C_INVALID_99999/investigation")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("detail", resp.json())
        print("  [PASS] Invalid customer ID returned HTTP 404 cleanly.")

    def test_gemini_api_failure_fallback(self):
        """Verify that when Gemini API throws an exception, system falls back deterministically."""
        pkg = investigate_customer("C_46046")
        
        with patch("app.ai.service.query_gemini_explanation", side_effect=Exception("API Connection Refused / 503")):
            explanation = explain_risk(pkg)
            self.assertIsNotNone(explanation)
            self.assertIn("headline", explanation)
            self.assertIn("summary", explanation)
            self.assertIn("key_signals", explanation)
            self.assertIn("observed_evidence", explanation)
            self.assertIn("Review required:", explanation["summary"])
            print("  [PASS] Gemini API failure gracefully triggered deterministic fallback.")

    def test_missing_api_key_fallback(self):
        """Verify deterministic fallback runs when GEMINI_API_KEY is unset."""
        pkg = investigate_customer("C_00003")
        fallback = generate_fallback_explanation(pkg)
        self.assertEqual(fallback["headline"], "Low Coordinated Risk Observed")
        self.assertIn("No immediate action required", fallback["recommended_action"])
        print("  [PASS] Deterministic fallback functions with 0 external dependencies.")

    def test_single_node_or_empty_graph(self):
        """Verify graph endpoint on isolated/low-connection accounts produces valid React Flow payload."""
        resp = self.client.get("/api/risk/customers/C_00003/graph")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreaterEqual(len(data["nodes"]), 1)
        self.assertEqual(data["nodes"][0]["data"]["is_target"], True)
        print("  [PASS] Graph endpoint returns valid React Flow topology for low-degree nodes.")

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 7: FAILURE MODES & FAULT-TOLERANCE VALIDATION")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFailureModes)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)
