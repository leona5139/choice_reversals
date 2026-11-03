import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from results import print_summary


class PromptVersionSummaryTest(unittest.TestCase):
    def test_versions_keep_separate_counts_and_costs(self):
        players = []
        for version, initial, cost in [
            ("prompt_a", {"A": 3, "B": 7}, 0.1),
            ("prompt_b", {"A": 5, "B": 5}, 0.2),
        ]:
            players.append({
                "treatment": "4A_4AR", "model": "test-model", "temperature": 1,
                "prompt_version": version, "cost": cost,
                "rounds": {"5": {
                    "task": "AR", "computer": {"A": 8, "B": 2},
                    "initial": initial, "revision": {"A": 5, "B": 5},
                }},
            })

        output = io.StringIO()
        with patch("results.load_players", return_value=players), redirect_stdout(output):
            print_summary("test")

        sections = output.getvalue().split("4A_4AR | test-model | t=1 | ")
        self.assertEqual(len(sections), 3)
        self.assertTrue(sections[1].startswith("prompt_a | 1 players | $0.1000\n"))
        self.assertIn("revised 1 of 1 choices; 1 of those to 5/5", sections[1])
        self.assertTrue(sections[2].startswith("prompt_b | 1 players | $0.2000\n"))
        self.assertIn("revised 0 of 1 choices; 0 of those to 5/5", sections[2])


if __name__ == "__main__":
    unittest.main()
