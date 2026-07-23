from intake.workers.local_static import _extract_ascii_strings, _magic_summary


def test_magic_summary_detects_elf() -> None:
    summary = _magic_summary(b"\x7fELF" + b"\x00" * 20)
    assert summary["file_type_hint"] == "elf"


def test_extract_ascii_strings_samples_printable_sequences() -> None:
    strings = _extract_ascii_strings(b"\x00hello-world\x00AB\x00another-string")
    assert "hello-world" in strings
    assert "another-string" in strings
    assert "AB" not in strings
