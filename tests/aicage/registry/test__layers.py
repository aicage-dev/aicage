from unittest import TestCase, mock

from aicage.registry import _layers as layers


class LayersTests(TestCase):
    def test_base_layer_missing_returns_false_when_base_unknown(self) -> None:
        with (
            mock.patch("aicage.registry._layers.get_local_rootfs_layers", return_value=None),
            mock.patch("aicage.registry._layers.get_logger") as get_logger_mock,
        ):
            self.assertFalse(layers.base_layer_missing("base", "final"))
        get_logger_mock.return_value.warning.assert_called_once()

    def test_base_layer_missing_returns_false_when_final_unknown(self) -> None:
        with (
            mock.patch(
                "aicage.registry._layers.get_local_rootfs_layers",
                side_effect=[["layer-a"], None],
            ),
            mock.patch("aicage.registry._layers.get_logger") as get_logger_mock,
        ):
            self.assertFalse(layers.base_layer_missing("base", "final"))
        get_logger_mock.return_value.warning.assert_called_once()

    def test_base_layer_missing_returns_true_when_missing(self) -> None:
        with mock.patch(
            "aicage.registry._layers.get_local_rootfs_layers",
            side_effect=[["layer-a"], ["layer-b"]],
        ):
            self.assertTrue(layers.base_layer_missing("base", "final"))

    def test_base_layer_missing_returns_false_when_present(self) -> None:
        with mock.patch(
            "aicage.registry._layers.get_local_rootfs_layers",
            side_effect=[["layer-a"], ["layer-a", "layer-b"]],
        ):
            self.assertFalse(layers.base_layer_missing("base", "final"))
