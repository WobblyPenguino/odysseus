import unittest
from nova_improvement_lab.autonomous_candidate_factory import AutonomousCandidateFactory

class TestAutonomousCandidateFactory(unittest.TestCase):
    def setUp(self):
        self.factory = AutonomousCandidateFactory(strict_mode=True)

    def test_valid_candidate_acceptance(self):
        candidate = self.factory.create_candidate("cand_001", "print('Optimized consensus loop')")
        is_valid = self.factory.evaluate_candidate(candidate)
        self.assertTrue(is_valid)

    def test_unsafe_candidate_rejection(self):
        candidate = self.factory.create_candidate("cand_002", "rm -rf /")
        is_valid = self.factory.evaluate_candidate(candidate)
        self.assertFalse(is_valid)

    def test_empty_candidate_rejection(self):
        candidate = self.factory.create_candidate("cand_003", "")
        is_valid = self.factory.evaluate_candidate(candidate)
        self.assertFalse(is_valid)

if __name__ == "__main__":
    unittest.main()
