import pytest
import os
from pyway.helpers import Utils
from pyway.migration import Migration


@pytest.mark.helpers_test
def test_get_local_files() -> None:
    files = Utils.get_local_files(os.path.join('tests', 'data', 'schema'))
    assert len(files) == 3


@pytest.mark.helpers_test
def test_get_local_files_notfound() -> None:
    with pytest.raises(Exception):
        _ = Utils.get_local_files(os.path.join('tests', 'datanotfound'))
    assert True


@pytest.mark.helpers_test
def test_subtract_result() -> None:
    a = [Migration.from_name('V01_01__test1.sql', os.path.join('tests', 'data', 'schema')),
         Migration.from_name('V01_02__test2.sql', os.path.join('tests', 'data', 'schema'))]
    b = [Migration.from_name('V01_01__test1.sql', os.path.join('tests', 'data', 'schema'))]
    c = [Migration.from_name('V01_02__test2.sql', os.path.join('tests', 'data', 'schema'))]
    d = Utils.subtract(a, b)

    assert c[0].name == d[0].name


@pytest.mark.helpers_test
def test_subtract_noresult() -> None:
    a = [Migration.from_name('V01_01__test1.sql', os.path.join('tests', 'data', 'schema'))]
    b = [Migration.from_name('V01_01__test1.sql', os.path.join('tests', 'data', 'schema'))]
    c = Utils.subtract(a, b)

    assert c == []


@pytest.mark.helpers_test
def test_subtract_identical_content_different_versions() -> None:
    # Two migrations with identical content (same checksum) are still
    # distinct migrations - the unapplied one must remain pending
    a = [Migration('01.01', 'SQL', 'V01_01__dup1.sql', 'ABCD1234', None),
         Migration('01.02', 'SQL', 'V01_02__dup2.sql', 'ABCD1234', None)]
    b = [Migration('01.01', 'SQL', 'V01_01__dup1.sql', 'ABCD1234', None)]
    c = Utils.subtract(a, b)

    assert len(c) == 1
    assert c[0].name == 'V01_02__dup2.sql'


@pytest.mark.helpers_test
def test_subtract_applied_version_not_reapplied_on_checksum_change() -> None:
    # An already-applied version with a modified local file must not be
    # re-applied - validate reports the checksum mismatch instead
    a = [Migration('01.01', 'SQL', 'V01_01__test1.sql', 'NEWSUM', None)]
    b = [Migration('01.01', 'SQL', 'V01_01__test1.sql', 'OLDSUM', None)]
    c = Utils.subtract(a, b)

    assert c == []


@pytest.mark.helpers_test
def test_subtract_onlyonearray() -> None:
    a = [Migration.from_name('V01_01__test1.sql', os.path.join('tests', 'data', 'schema'))]
    b = []
    c = Utils.subtract(a, b)

    assert c == a


@pytest.mark.helpers_test
def test_expected_pattern() -> None:
    pattern = Utils.expected_pattern()
    assert pattern == "V{major}_{minor}__{description}.sql"


@pytest.mark.helpers_test
def test_get_version_from_name() -> None:
    with pytest.raises(Exception):
        _ = Utils.get_version_from_name("test1.sql")
    assert True


@pytest.mark.helpers_test
def test_load_checksum_from_name_failed() -> None:
    with pytest.raises(Exception):
        _ = Utils.load_checksum_from_name('test', 'test')
    assert True


@pytest.mark.helpers_test
def test_version_name() -> None:
    assert Utils.is_file_name_valid('V1_1__test1.sql')


@pytest.mark.helpers_test
def test_semantic_version_name() -> None:
    assert Utils.is_file_name_valid('V1_0_1__test1.sql')


@pytest.mark.helpers_test
def test_semantic_version_name_major_period() -> None:
    assert Utils.is_file_name_valid('V1.0_1__test1.sql')


@pytest.mark.helpers_test
def test_semantic_version_name_minor_period() -> None:
    assert Utils.is_file_name_valid('V1_0.1__test1.sql')


@pytest.mark.helpers_test
def test_semantic_version_name_major_minor_period() -> None:
    assert Utils.is_file_name_valid('V1.0.1__test1.sql')


@pytest.mark.helpers_test
def test_semantic_version_name_minor_over_2digits() -> None:
    assert Utils.is_file_name_valid('V1_0_100__test1.sql')


@pytest.mark.helpers_test
def test_invalid_name_no_separator_or_suffix() -> None:
    assert not Utils.is_file_name_valid('V1_1zzzzzz')


@pytest.mark.helpers_test
def test_invalid_name_missing_separator() -> None:
    assert not Utils.is_file_name_valid('V01_01_no_separator.sql')


@pytest.mark.helpers_test
def test_invalid_name_wrong_suffix() -> None:
    assert not Utils.is_file_name_valid('V01_01__init.txt')


@pytest.mark.helpers_test
def test_invalid_name_no_version() -> None:
    assert not Utils.is_file_name_valid('test1.sql')


@pytest.mark.helpers_test
def test_invalid_name_missing_description() -> None:
    assert not Utils.is_file_name_valid('V01_01__.sql')
