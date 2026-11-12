import unittest
from unittest.mock import patch
from pathlib import Path

from interview_app_frontend.utils.styles import inject_styles


class TestStylesInjection(unittest.TestCase):
    def test_inject_styles_uses_streamlit_markdown_with_shared_css(self):
        with patch("interview_app_frontend.utils.styles.st.markdown") as mock_markdown:
            inject_styles()

        rendered = mock_markdown.call_args.args[0]
        self.assertIsInstance(rendered, str)
        css = rendered
        self.assertIn("<style>", css)
        self.assertIn(".question-shell", css)
        self.assertIn(".feedback-card", css)
        self.assertIn(".setup-field-error", css)
        self.assertIn(".setup-required-asterisk", css)
        self.assertIn(".setup-required-marker", css)


if __name__ == "__main__":
    unittest.main()
