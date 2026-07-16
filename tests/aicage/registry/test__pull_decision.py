from unittest import TestCase, mock

from aicage.registry import _pull_decision


class PullDecisionTests(TestCase):
    def test_pull_decision_plan_requests_confirmation_when_digests_differ(self) -> None:
        with (
            mock.patch(
                "aicage.registry._pull_decision.get_local_repo_digest",
                return_value="sha256:local",
            ),
            mock.patch(
                "aicage.registry._pull_decision.get_remote_digest",
                return_value="sha256:remote",
            ),
        ):
            plan = _pull_decision.pull_decision_plan("image:tag")

        self.assertFalse(plan.should_pull)
        self.assertEqual("image:tag", plan.confirm_update_image_ref)

    def test_decide_pull_returns_true_when_local_missing(self) -> None:
        with mock.patch(
            "aicage.registry._pull_decision.get_local_repo_digest",
            return_value=None,
        ):
            self.assertTrue(_pull_decision.decide_pull("image:tag"))

    def test_decide_pull_returns_false_when_remote_unknown(self) -> None:
        with (
            mock.patch(
                "aicage.registry._pull_decision.get_local_repo_digest",
                return_value="sha256:local",
            ),
            mock.patch(
                "aicage.registry._pull_decision.get_remote_digest",
                return_value=None,
            ),
        ):
            self.assertFalse(_pull_decision.decide_pull("image:tag"))

    def test_decide_pull_returns_true_when_digests_differ(self) -> None:
        with (
            mock.patch(
                "aicage.registry._pull_decision.get_local_repo_digest",
                return_value="sha256:local",
            ),
            mock.patch(
                "aicage.registry._pull_decision.get_remote_digest",
                return_value="sha256:remote",
            ),
            mock.patch(
                "aicage.registry._pull_decision.prompt_update_image",
                return_value=True,
            ) as prompt_mock,
        ):
            self.assertTrue(
                _pull_decision.decide_pull("ghcr.io/aicage/aicage:codex-fedora")
            )
        prompt_mock.assert_called_once_with("ghcr.io/aicage/aicage:codex-fedora")

    def test_decide_pull_returns_false_when_user_keeps_local_image(self) -> None:
        with (
            mock.patch(
                "aicage.registry._pull_decision.get_local_repo_digest",
                return_value="sha256:local",
            ),
            mock.patch(
                "aicage.registry._pull_decision.get_remote_digest",
                return_value="sha256:remote",
            ),
            mock.patch(
                "aicage.registry._pull_decision.prompt_update_image",
                return_value=False,
            ) as prompt_mock,
        ):
            self.assertFalse(
                _pull_decision.decide_pull("ghcr.io/aicage/aicage:codex-fedora")
            )
        prompt_mock.assert_called_once_with("ghcr.io/aicage/aicage:codex-fedora")
