from unittest.mock import patch

import wiz_central_toolkit.bannerwiz.__main__ as bannerwiz_cli


def test_bannerwiz_cli_default(capsys):
    with patch("sys.argv", ["bannerwiz"]):
        bannerwiz_cli.main()
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_bannerwiz_cli_custom_text(capsys):
    with patch("sys.argv", ["bannerwiz", "WIZARD"]):
        bannerwiz_cli.main()
    captured = capsys.readouterr()
    assert len(captured.out) > 0
