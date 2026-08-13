import pytest

from financial_os.operations.sync_owner_allowlist import parse_single_owner


def test_parse_single_owner_accepts_stable_firebase_subject() -> None:
    assert parse_single_owner(" google:Abc_123-def ") == ("google:Abc_123-def",)


def test_parse_single_owner_deduplicates_identical_subject() -> None:
    assert parse_single_owner("google:owner-1,google:owner-1") == ("google:owner-1",)


@pytest.mark.parametrize(
    "raw_allowlist",
    [
        "",
        "google:first,google:second",
        "email:owner@example.test",
        "google:owner; DROP TABLE auth_subjects",
    ],
)
def test_parse_single_owner_rejects_unsafe_or_ambiguous_values(raw_allowlist: str) -> None:
    with pytest.raises(ValueError):
        parse_single_owner(raw_allowlist)
