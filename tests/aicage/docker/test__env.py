from unittest import TestCase, mock

from aicage.docker._env import resolve_user_ids


class EnvTests(TestCase):
    def test_resolve_user_ids_handles_missing(self) -> None:
        with (
            mock.patch("aicage.docker._env.os.getuid", None, create=True),
            mock.patch("aicage.docker._env.os.getgid", None, create=True),
            mock.patch.dict("aicage.docker._env.os.environ", {"USER": "tester"}, clear=True),
            mock.patch("aicage.docker._env.os.name", "posix"),
        ):
            env_flags = resolve_user_ids()
        self.assertEqual(["-e", "AICAGE_USER=tester"], env_flags)

    def test_resolve_user_ids_includes_uid_gid(self) -> None:
        with (
            mock.patch("aicage.docker._env.os.getuid", return_value=1000, create=True),
            mock.patch("aicage.docker._env.os.getgid", return_value=1001, create=True),
            mock.patch.dict("aicage.docker._env.os.environ", {"USER": "tester"}, clear=True),
            mock.patch("aicage.docker._env.os.name", "posix"),
        ):
            env_flags = resolve_user_ids()
        self.assertEqual(
            ["-e", "AICAGE_UID=1000", "-e", "AICAGE_GID=1001", "-e", "AICAGE_USER=tester"],
            env_flags,
        )

    def test_resolve_user_ids_sets_root_on_windows(self) -> None:
        with (
            mock.patch("aicage.docker._env.os.getuid", side_effect=AttributeError, create=True),
            mock.patch("aicage.docker._env.os.getgid", side_effect=AttributeError, create=True),
            mock.patch.dict("aicage.docker._env.os.environ", {"USER": "tester"}, clear=True),
            mock.patch("aicage.docker._env.os.name", "nt"),
        ):
            env_flags = resolve_user_ids()
        self.assertEqual(["-e", "AICAGE_USER=root"], env_flags)
