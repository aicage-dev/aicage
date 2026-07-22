from unittest import TestCase, mock

from aicage.runtime.menu.textual import _execution_app

from ._test_support import _call_work


class ExecutionAppTests(TestCase):
    def test_compose_yields_execution_screen(self) -> None:
        app = _execution_app.ExecutionApp(mock.Mock())

        widgets = list(app.compose())

        self.assertEqual(1, len(widgets))
        self.assertIsInstance(widgets[0], _execution_app.ExecutionScreen)

    def test_init_sets_container_setup_subtitle(self) -> None:
        app = _execution_app.ExecutionApp(mock.Mock())

        self.assertEqual("container setup", app.sub_title)

    def test_format_title_bolds_app_name_and_dims_subtitle(self) -> None:
        app = _execution_app.ExecutionApp(mock.Mock())

        title = app.format_title("aicage", "container setup")

        self.assertEqual("aicage — container setup", str(title))

    def test_on_mount_starts_execution(self) -> None:
        app = _execution_app.ExecutionApp(mock.Mock())

        with mock.patch.object(app, "_run_execution") as run_mock:
            app.on_mount()

        run_mock.assert_called_once_with()

    def test_action_cancel_interrupts_process_group(self) -> None:
        app = _execution_app.ExecutionApp(mock.Mock())

        with mock.patch(
            "aicage.runtime.menu.textual._execution_app.os.killpg"
        ) as killpg_mock:
            app.action_cancel()

        killpg_mock.assert_called_once()

    def test_run_execution_exits_with_error(self) -> None:
        operation = mock.Mock(side_effect=RuntimeError("boom"))
        app = _execution_app.ExecutionApp(operation)
        screen = mock.Mock()

        with (
            mock.patch.object(app, "query_one", return_value=screen),
            mock.patch.object(app, "call_from_thread") as call_from_thread_mock,
        ):
            _call_work(app, "_run_execution")

        call_from_thread_mock.assert_called_once()
        self.assertIsInstance(call_from_thread_mock.call_args.args[1], RuntimeError)

    def test_run_execution_exits_with_none_on_success(self) -> None:
        operation = mock.Mock()
        app = _execution_app.ExecutionApp(operation)
        screen = mock.Mock()

        with (
            mock.patch.object(app, "query_one", return_value=screen),
            mock.patch.object(app, "call_from_thread") as call_from_thread_mock,
        ):
            _call_work(app, "_run_execution")

        call_from_thread_mock.assert_called_once_with(app.exit, None)
