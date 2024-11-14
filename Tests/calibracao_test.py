from pytest import fixture


@fixture
def calib_test():
    return 42


def test_calib_value(calib_test):
    assert calib_test == 42


def test_calib_type(calib_test):
    assert isinstance(calib_test, int)


def test_calib_not_zero(calib_test):
    assert calib_test != 0
