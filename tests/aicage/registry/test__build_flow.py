from unittest import TestCase, mock

from aicage.registry._build_flow import maybe_build


class BuildFlowTests(TestCase):
    def test_maybe_build_runs_build_and_save_when_needed(self) -> None:
        load_record = mock.Mock(return_value=None)
        should_rebuild = mock.Mock(return_value=True)
        run_build = mock.Mock()
        save_record = mock.Mock()

        built = maybe_build(
            load_record=load_record,
            should_rebuild=should_rebuild,
            run_build=run_build,
            save_record=save_record,
        )

        self.assertTrue(built)
        load_record.assert_called_once_with()
        should_rebuild.assert_called_once_with(None)
        run_build.assert_called_once_with()
        save_record.assert_called_once_with()

    def test_maybe_build_skips_when_not_needed(self) -> None:
        record = object()
        load_record = mock.Mock(return_value=record)
        should_rebuild = mock.Mock(return_value=False)
        run_build = mock.Mock()
        save_record = mock.Mock()

        built = maybe_build(
            load_record=load_record,
            should_rebuild=should_rebuild,
            run_build=run_build,
            save_record=save_record,
        )

        self.assertFalse(built)
        load_record.assert_called_once_with()
        should_rebuild.assert_called_once_with(record)
        run_build.assert_not_called()
        save_record.assert_not_called()
