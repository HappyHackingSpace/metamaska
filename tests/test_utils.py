
from metamaska.utils import remove_new_line, remove_whitespace, unquote


def test_unquote():
    assert unquote("\"onfocus=\"alert('Y000')\"+autofocus=\"") == "\"onfocus=\"alert('Y000')\" autofocus=\""


def test_remove_new_line():
    assert remove_new_line("payload\n") == "payload"


def test_remove_whitespace():
    assert remove_whitespace(" payload ") == "payload"
