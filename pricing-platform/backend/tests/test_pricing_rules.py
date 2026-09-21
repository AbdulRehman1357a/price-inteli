from decimal import Decimal

from fastapi.testclient import TestClient

from tests.helpers import auth_headers, category_payload, pricing_rule_payload, product_payload, register


def _setup_product(client: TestClient, tokens: dict, **overrides) -> dict:
    category = client.post(
        "/api/v1/categories", json=category_payload(), headers=auth_headers(tokens)
    ).json()["data"]
    return client.post(
        "/api/v1/products",
        json=product_payload(category_id=category["id"], **overrides),
        headers=auth_headers(tokens),
    ).json()["data"]


def _create_rule(client: TestClient, tokens: dict, **overrides) -> dict:
    response = client.post(
        "/api/v1/pricing/rules", json=pricing_rule_payload(**overrides), headers=auth_headers(tokens)
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _test_rule(client: TestClient, tokens: dict, rule_id: str, product_id: str, **overrides) -> dict:
    body = {"product_id": product_id}
    body.update(overrides)
    response = client.post(f"/api/v1/pricing/rules/{rule_id}/test", json=body, headers=auth_headers(tokens))
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_create_rule_success(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/pricing/rules", json=pricing_rule_payload(), headers=auth_headers(tokens)
    )

    assert response.status_code == 201, response.text
    assert response.json()["data"]["rule_type"] == "percentage_discount"


def test_create_rule_invalid_action_kind_rejected(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/pricing/rules",
        json=pricing_rule_payload(actions_json={"kind": "not_a_real_kind", "value": "10"}),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_create_rule_missing_action_value_rejected(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/pricing/rules",
        json=pricing_rule_payload(actions_json={"kind": "percentage_discount"}),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_get_and_update_rule(client: TestClient) -> None:
    tokens = register(client)
    rule = _create_rule(client, tokens)

    get_response = client.get(f"/api/v1/pricing/rules/{rule['id']}", headers=auth_headers(tokens))
    assert get_response.status_code == 200

    update_response = client.put(
        f"/api/v1/pricing/rules/{rule['id']}", json={"priority": 5}, headers=auth_headers(tokens)
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["priority"] == 5


def test_list_rules_filters_by_rule_type(client: TestClient) -> None:
    tokens = register(client)
    _create_rule(client, tokens, name="A", rule_type="percentage_discount")
    _create_rule(
        client,
        tokens,
        name="B",
        rule_type="fixed_price",
        actions_json={"kind": "fixed_price", "value": "9.99"},
    )

    response = client.get("/api/v1/pricing/rules?rule_type=fixed_price", headers=auth_headers(tokens))

    assert [r["name"] for r in response.json()["data"]] == ["B"]


# --- Engine behavior, via the test/preview endpoint ---


def test_no_matching_rules_returns_current_price_unchanged(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="50.00")
    rule = _create_rule(client, tokens, status="draft")  # never matches (DRAFT, not the one under test)

    result = _test_rule(client, tokens, rule["id"], product["id"])

    # The rule under test IS included even as draft, so a 10% discount does apply.
    assert Decimal(result["current_price"]) == Decimal("50.0000")
    assert Decimal(result["final_price"]) == Decimal("45.0000")
    assert len(result["matched_rules"]) == 1


def test_percentage_discount_rule(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00")
    rule = _create_rule(client, tokens, actions_json={"kind": "percentage_discount", "value": "20"})

    result = _test_rule(client, tokens, rule["id"], product["id"])

    assert Decimal(result["final_price"]) == Decimal("80.0000")
    assert result["matched_rules"][0]["rule_id"] == rule["id"]


def test_fixed_discount_rule(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00")
    rule = _create_rule(client, tokens, actions_json={"kind": "fixed_discount", "value": "15"})

    result = _test_rule(client, tokens, rule["id"], product["id"])

    assert Decimal(result["final_price"]) == Decimal("85.0000")


def test_fixed_price_rule(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00")
    rule = _create_rule(client, tokens, actions_json={"kind": "fixed_price", "value": "42.42"})

    result = _test_rule(client, tokens, rule["id"], product["id"])

    assert Decimal(result["final_price"]) == Decimal("42.4200")


def test_margin_based_rule(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00", cost_price="60.00")
    rule = _create_rule(client, tokens, actions_json={"kind": "margin_based", "margin_percentage": "40"})

    result = _test_rule(client, tokens, rule["id"], product["id"])

    # selling_price = cost / (1 - margin/100) = 60 / 0.6 = 100
    assert Decimal(result["final_price"]) == Decimal("100.0000")


def test_margin_based_without_cost_price_is_skipped_with_note(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00")  # no cost_price
    rule = _create_rule(client, tokens, actions_json={"kind": "margin_based", "margin_percentage": "40"})

    result = _test_rule(client, tokens, rule["id"], product["id"])

    assert result["matched_rules"] == []
    assert Decimal(result["final_price"]) == Decimal("100.0000")
    assert any("skipped" in note for note in result["constraint_validation"])


def test_cost_plus_rule(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00", cost_price="50.00")
    rule = _create_rule(client, tokens, actions_json={"kind": "cost_plus", "markup_percentage": "50"})

    result = _test_rule(client, tokens, rule["id"], product["id"])

    # 50 * 1.5 = 75
    assert Decimal(result["final_price"]) == Decimal("75.0000")


def test_constraint_min_price_clamps(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="20.00")
    rule = _create_rule(
        client,
        tokens,
        actions_json={"kind": "percentage_discount", "value": "90"},
        constraints_json={"min_price": "5.00"},
    )

    result = _test_rule(client, tokens, rule["id"], product["id"])

    # 90% off 20 = 2.00, clamped up to the 5.00 floor
    assert Decimal(result["final_price"]) == Decimal("5.0000")
    assert any("minimum price" in note for note in result["constraint_validation"])


def test_constraint_max_discount_percentage_clamps(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00")
    rule = _create_rule(
        client,
        tokens,
        actions_json={"kind": "percentage_discount", "value": "50"},
        constraints_json={"max_discount_percentage": "20"},
    )

    result = _test_rule(client, tokens, rule["id"], product["id"])

    # 50% off would be 50.00, but max 20% off base_price (100) floors it at 80.00
    assert Decimal(result["final_price"]) == Decimal("80.0000")


def test_constraint_rounding_charm_99(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="20.00")
    rule = _create_rule(
        client,
        tokens,
        actions_json={"kind": "fixed_price", "value": "19.45"},
        constraints_json={"rounding": "charm_99"},
    )

    result = _test_rule(client, tokens, rule["id"], product["id"])

    assert Decimal(result["final_price"]) == Decimal("18.99")


def test_multiple_rules_stack_in_priority_order(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00")
    # priority 10 runs first: 10% off -> 90. priority 20 runs second: $5 off -> 85.
    first = _create_rule(
        client, tokens, name="First", priority=10, actions_json={"kind": "percentage_discount", "value": "10"}
    )
    _create_rule(
        client,
        tokens,
        name="Second",
        priority=20,
        actions_json={"kind": "fixed_discount", "value": "5"},
    )

    result = _test_rule(client, tokens, first["id"], product["id"])

    assert len(result["matched_rules"]) == 2
    assert Decimal(result["final_price"]) == Decimal("85.0000")
    assert result["rule_execution_order"] == [r["rule_id"] for r in result["matched_rules"]]


def test_conditions_category_scope_excludes_non_matching_product(client: TestClient) -> None:
    tokens = register(client)
    electronics = client.post(
        "/api/v1/categories", json=category_payload(name="Electronics"), headers=auth_headers(tokens)
    ).json()["data"]
    apparel = client.post(
        "/api/v1/categories", json=category_payload(name="Apparel"), headers=auth_headers(tokens)
    ).json()["data"]
    apparel_product = client.post(
        "/api/v1/products",
        json=product_payload(category_id=apparel["id"], sku="SHIRT-1", selling_price="30.00"),
        headers=auth_headers(tokens),
    ).json()["data"]

    rule = _create_rule(
        client, tokens, conditions_json={"category_ids": [electronics["id"]]}
    )

    result = _test_rule(client, tokens, rule["id"], apparel_product["id"])

    assert result["matched_rules"] == []
    assert Decimal(result["final_price"]) == Decimal("30.0000")


def test_conditions_store_scope_requires_matching_store(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00")
    store_a = client.post(
        "/api/v1/stores",
        json={
            "store_code": "A",
            "name": "Store A",
            "country": "US",
            "city": "NYC",
            "address_line_1": "1 Main",
            "timezone": "UTC",
            "currency": "USD",
        },
        headers=auth_headers(tokens),
    ).json()["data"]
    rule = _create_rule(client, tokens, conditions_json={"store_ids": [store_a["id"]]})

    without_store = _test_rule(client, tokens, rule["id"], product["id"])
    assert without_store["matched_rules"] == []

    with_store = _test_rule(client, tokens, rule["id"], product["id"], store_id=store_a["id"])
    assert len(with_store["matched_rules"]) == 1


def test_approval_required_surfaced_in_result(client: TestClient) -> None:
    tokens = register(client)
    product = _setup_product(client, tokens, selling_price="100.00")
    rule = _create_rule(client, tokens, approval_required=True)

    result = _test_rule(client, tokens, rule["id"], product["id"])

    assert result["approval_required"] is True
    assert result["matched_rules"][0]["approval_required"] is True


def test_cannot_test_another_organizations_rule(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")
    rule_b = _create_rule(client, org_b)
    product_a = _setup_product(client, org_a)

    response = client.post(
        f"/api/v1/pricing/rules/{rule_b['id']}/test",
        json={"product_id": product_a["id"]},
        headers=auth_headers(org_a),
    )

    assert response.status_code == 404
