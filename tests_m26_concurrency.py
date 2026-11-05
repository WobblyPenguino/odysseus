import unittest
import concurrent.futures
from nova_improvement_lab.m26_leader_election import SwarmLeaderElection

class TestSwarmLeaderElectionConcurrency(unittest.TestCase):
    def test_concurrent_fencing_token_issuance(self):
        nodes = [{"id": "node_alpha", "priority": 10, "active": True}]
        election = SwarmLeaderElection(node_id="node_alpha", cluster_nodes=nodes)
        
        # Execute 50 concurrent requests for fencing tokens across 10 worker threads
        tokens = []
        def fetch_token():
            return election.get_fencing_token()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_token) for _ in range(50)]
            for future in concurrent.futures.as_completed(futures):
                tokens.append(future.result())

        # Verify all fencing tokens issued are strictly unique, sequential, and gap-free
        fencing_tokens = [t["fencing_token"] for t in tokens if t["is_current_node_leader"]]
        self.assertEqual(len(fencing_tokens), 50)
        self.assertEqual(len(set(fencing_tokens)), 50, "Race condition detected: Duplicate fencing tokens issued!")
        self.assertEqual(min(fencing_tokens), 1)
        self.assertEqual(max(fencing_tokens), 50)
        print("M26 Concurrency & Race-Condition Safety Test PASSED successfully.")

if __name__ == "__main__":
    unittest.main()
