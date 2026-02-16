import os
from unittest import TestCase, mock

from aicage._proxy import (
    proxy_build_args_from_host,
    proxy_env_vars_from_host,
    proxy_run_env_args_from_host,
)
from aicage.runtime.run_args import EnvVar


class ProxyTests(TestCase):
    def test_proxy_env_vars_from_host_uses_only_uppercase(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "HTTP_PROXY": "http://proxy-http:8080",
                "HTTPS_PROXY": "http://proxy-https:8080",
                "http_proxy": "http://ignored:8080",
            },
            clear=True,
        ):
            result = proxy_env_vars_from_host()

        self.assertEqual(
            [
                EnvVar(name="HTTP_PROXY", value="http://proxy-http:8080"),
                EnvVar(name="HTTPS_PROXY", value="http://proxy-https:8080"),
            ],
            result,
        )

    def test_proxy_build_args_from_host(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "HTTP_PROXY": "http://proxy-http:8080",
                "NO_PROXY": "localhost,127.0.0.1",
            },
            clear=True,
        ):
            result = proxy_build_args_from_host()

        self.assertEqual(
            [
                "--build-arg",
                "HTTP_PROXY=http://proxy-http:8080",
                "--build-arg",
                "NO_PROXY=localhost,127.0.0.1",
            ],
            result,
        )

    def test_proxy_run_env_args_from_host(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "ALL_PROXY": "socks5://proxy-socks:1080",
            },
            clear=True,
        ):
            result = proxy_run_env_args_from_host()

        self.assertEqual(["-e", "ALL_PROXY=socks5://proxy-socks:1080"], result)
