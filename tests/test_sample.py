"""Basic golden-output test to prove the pattern works."""


def test_output_matches_golden(sample_output, golden_dir):
    golden_path = golden_dir / "expected_output.txt"
    expected = golden_path.read_text()
    assert sample_output == expected
