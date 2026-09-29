from unittest.mock import patch

import pytest

import wiz_central_toolkit.codeguardwiz.__main__ as codeguardwiz_cli
import wiz_central_toolkit.debugwiz.__main__ as debugwiz_cli
import wiz_central_toolkit.diffwiz.__main__ as diffwiz_cli
import wiz_central_toolkit.jsonwiz.__main__ as jsonwiz_cli
import wiz_central_toolkit.pythonwiz.__main__ as pythonwiz_cli
import wiz_central_toolkit.tmuxwiz.__main__ as tmuxwiz_cli
import wiz_central_toolkit.todowiz.__main__ as todowiz_cli
import wiz_central_toolkit.writewiz.__main__ as writewiz_cli


@pytest.mark.parametrize(
    "cli_module",
    [
        codeguardwiz_cli,
        debugwiz_cli,
        diffwiz_cli,
        jsonwiz_cli,
        pythonwiz_cli,
        tmuxwiz_cli,
        todowiz_cli,
        writewiz_cli,
    ],
)
def test_wrapper_cli_execution(cli_module, capsys):
    with patch("sys.argv", ["wiz-tool"]):
        try:
            cli_module.main()
        except SystemExit:
            pass
