from wiz_central_toolkit.rustwiz.rust_wizard import RustWizard


def test_rustwiz_check_nonexistent():
    wizard = RustWizard()
    res = wizard.check(["nonexistent_file.rs"])
    assert isinstance(res, int)
    assert res != 0


def test_rustwiz_build_nonexistent():
    wizard = RustWizard()
    res = wizard.build("nonexistent_dir")
    assert isinstance(res, int)
    assert res != 0
