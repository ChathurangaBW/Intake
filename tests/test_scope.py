from intake.scope import ScopeManifest, ScopeValidator


def test_domain_scope_allows_exact_and_subdomain() -> None:
    validator = ScopeValidator(
        ScopeManifest(engagement_id="eng-1", domains=["example.test"])
    )

    assert validator.target_allowed("example.test")
    assert validator.target_allowed("https://api.example.test/v1")


def test_domain_scope_rejects_suffix_confusion() -> None:
    validator = ScopeValidator(
        ScopeManifest(engagement_id="eng-1", domains=["example.test"])
    )

    assert not validator.target_allowed("badexample.test")


def test_cidr_scope_allows_address_inside_network() -> None:
    validator = ScopeValidator(ScopeManifest(engagement_id="eng-1", cidrs=["192.0.2.0/28"]))

    assert validator.target_allowed("192.0.2.5")
    assert not validator.target_allowed("198.51.100.5")


def test_operation_denied_takes_precedence() -> None:
    validator = ScopeValidator(
        ScopeManifest(
            engagement_id="eng-1",
            allowed_operations=["artifact.identify", "ghidra.analyze"],
            denied_operations=["dynamic.execute"],
        )
    )

    assert validator.operation_allowed("ghidra.analyze")
    assert not validator.operation_allowed("dynamic.execute")
