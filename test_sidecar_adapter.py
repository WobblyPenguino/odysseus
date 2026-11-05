import unittest
import os
import json
from sidecar_adapter import SidecarAdapter

class TestSidecarAdapterPipeline(unittest.TestCase):
    def setUp(self):
        self.state_file = "integration_audit_state.json"
        self.epoch_file = "cluster_state_epoch.json"
        for f in [self.state_file, self.epoch_file]:
            if os.path.exists(f):
                os.remove(f)
            
        self.cluster_nodes = [{"id": "sidecar_node_1", "priority": 100, "active": True}]
        self.adapter = SidecarAdapter(node_id="sidecar_node_1", cluster_nodes=self.cluster_nodes)

    def tearDown(self):
        for f in [self.state_file, self.epoch_file]:
            if os.path.exists(f):
                os.remove(f)

    def test_adapter_success_pipeline(self):
        telemetry_packet = {"error_rate": 0.01, "latency_ms": 100.0}
        lane_batches = [["tx_1", "tx_2"], ["tx_1", "tx_2"], ["tx_1", "tx_2"], ["tx_3", "tx_4"]]
        
        res = self.adapter.process_main_payload(telemetry_packet, lane_batches)
        self.assertEqual(res["status"], "ACCEPTED")
        self.assertEqual(res["epoch"], 1)
        self.assertEqual(res["fencing_token"], 1)
        self.assertTrue(os.path.exists(self.state_file))

        with open(self.state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.assertEqual(state["epoch"], 1)
        self.assertEqual(state["fencing_token"], 1)
        print("Sidecar Adapter E2E Pipeline Verification PASSED successfully.")

    def test_adapter_fail_closed_telemetry(self):
        telemetry_packet = {"error_rate": 0.20, "latency_ms": 100.0}
        lane_batches = [["tx_1", "tx_2"], ["tx_1", "tx_2"], ["tx_1", "tx_2"], ["tx_3", "tx_4"]]
        
        res = self.adapter.process_main_payload(telemetry_packet, lane_batches)
        self.assertEqual(res["status"], "REJECTED")
        self.assertIn("Telemetry gate check failed", res["reason"])

if __name__ == "__main__":
    unittest.main()
