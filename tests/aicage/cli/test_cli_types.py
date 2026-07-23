from unittest import TestCase

from aicage.cli_types import ParsedArgs


class ParsedArgsTests(TestCase):
    def test_parsed_args_fields(self) -> None:
        parsed = ParsedArgs(
            dry_run=True,
            docker_args="--net=host",
            agent="codex",
            agent_args=["--flag"],
            docker_socket=False,
            shares=["/test-tmp/one", "/test-tmp/two:ro"],
            config_action=None,
        )

        self.assertTrue(parsed.dry_run)
        self.assertEqual("--net=host", parsed.docker_args)
        self.assertEqual("codex", parsed.agent)
        self.assertEqual(["--flag"], parsed.agent_args)
        self.assertFalse(parsed.docker_socket)
        self.assertEqual(["/test-tmp/one", "/test-tmp/two:ro"], parsed.shares)
        self.assertIsNone(parsed.config_action)
        self.assertIsNone(parsed.config_agent)
        self.assertEqual("ui", parsed.menu)
