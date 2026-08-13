from pathlib import Path

import financial_os.services.validation as validation


def test_schema_path_honors_runtime_contracts_directory(
    monkeypatch,
    tmp_path: Path,
) -> None:
    schema_path = tmp_path / "extraction-result.schema.json"
    schema_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("FINANCIAL_OS_CONTRACTS_DIR", str(tmp_path))

    assert validation._schema_path() == schema_path


def test_load_schema_from_runtime_contracts_directory(
    monkeypatch,
    tmp_path: Path,
) -> None:
    schema_path = tmp_path / "extraction-result.schema.json"
    schema_path.write_text('{"type":"object"}', encoding="utf-8")
    monkeypatch.setenv("FINANCIAL_OS_CONTRACTS_DIR", str(tmp_path))
    monkeypatch.setattr(validation, "_schema_cache", None)

    assert validation.load_extraction_schema() == {"type": "object"}
