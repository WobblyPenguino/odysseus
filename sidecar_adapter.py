from nova_improvement_lab.m24_consensus_engine import MultiLaneConsensusEngine
from nova_improvement_lab.m25_telemetry_gate import TelemetryConsensusGate
from nova_improvement_lab.m26_leader_election import SwarmLeaderElection
from nova_improvement_lab.m29_epoch_persistence import EpochPersistenceManager

class SidecarAdapter:
    def __init__(self, node_id: str, cluster_nodes: list[dict], lane_count: int = 4):
        self.consensus = MultiLaneConsensusEngine(lane_count=lane_count, quorum_threshold_ratio=0.67)
        self.telemetry_gate = TelemetryConsensusGate(max_error_rate=0.05, max_latency_ms=500.0)
        self.election = SwarmLeaderElection(node_id=node_id, cluster_nodes=cluster_nodes)
        self.persistence = EpochPersistenceManager("integration_audit_state.json")

    def process_main_payload(self, telemetry_packet: dict, lane_batches: list[list[str]]) -> dict:
        telemetry_res = self.telemetry_gate.evaluate_telemetry(telemetry_packet)
        if not telemetry_res.get("allowed", False):
            return {
                "status": "REJECTED",
                "reason": "Telemetry gate check failed (fail-closed triggered)",
                "details": telemetry_res
            }

        consensus_res = self.consensus.evaluate_lanes(lane_batches)
        if not consensus_res.get("consensus_verified", False):
            return {
                "status": "REJECTED",
                "reason": "Multi-lane quorum consensus failed",
                "details": consensus_res
            }

        global_root = consensus_res["global_merkle_root"]

        fencing_info = self.election.get_fencing_token()
        if not fencing_info.get("is_current_node_leader", False):
            return {
                "status": "REJECTED",
                "reason": "Node does not hold active leadership in current epoch",
                "details": fencing_info
            }

        try:
            self.persistence.save_state(
                epoch=fencing_info["epoch"],
                fencing_token=fencing_info["fencing_token"],
                global_merkle_root=global_root
            )
        except Exception as e:
            return {
                "status": "ERROR",
                "reason": f"Durable state persistence failed: {str(e)}"
            }

        return {
            "status": "ACCEPTED",
            "epoch": fencing_info["epoch"],
            "fencing_token": fencing_info["fencing_token"],
            "global_merkle_root": global_root
        }
