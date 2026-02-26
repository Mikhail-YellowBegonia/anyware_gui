import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APPS_DIR = ROOT / "apps"
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

import app_anyware_llm_ui_demo as demo


class TestLLMUiDemo(unittest.TestCase):
    def test_build_demo_page(self) -> None:
        page = demo.build_demo_page()
        self.assertEqual(page.page_id, "llm_ui_demo")
        panel = next((child for child in page.children if child.component_id == "llm_panel"), None)
        self.assertIsNotNone(panel)


if __name__ == "__main__":
    unittest.main()
