import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import agent_service
from tests.helpers import (
    add_user_with_role,
    adjustment_item,
    auth_headers,
    category_payload,
    product_payload,
    register,
    store_payload,
)

_DEFAULT_PRICES = {"selling_price": "100.0000", "cost_price": "50.0000"}


def _setup(
    client: TestClient, tokens: dict, sku: str, *, on_hand: str, decrease: str | None = None, **overrides
) -> dict:
    headers = auth_headers(tokens)
    category = client.post("/api/v1/categories", json=category_payload(), headers=headers).json()["data"]
    store = client.post("/api/v1/stores", json=store_payload(), headers=headers).json()["data"]
    payload = product_payload(category_id=category["id"], sku=sku, **{**_DEFAULT_PRICES, **overrides})
    product = client.post("/api/v1/products", json=payload, headers=headers).json()["data"]

    inv = client.post(
        "/api/v1/inventory",
        json={"store_id": store["id"], "product_id": product["id"], "quantity_on_hand": on_hand},
        headers=headers,
    )
    assert inv.status_code == 201, inv.text

    if decrease is not None:
        item = adjustment_item(
            store_id=store["id"],
            product_id=product["id"],
            adjustment_type="decrease",
            adjustment_quantity=decrease,
            reason="Sold",
        )
        bulk = client.post("/api/v1/inventory/bulk-update", json={"items": [item]}, headers=headers)
        assert bulk.status_code == 200, bulk.text

    return {"category": category, "store": store, "product": product}


def _create_agent(client: TestClient, tokens: dict, **overrides) -> dict:
    payload = {"agent_type": "pricing_optimization", "name": "Nightly Price Optimizer"}
    payload.update(overrides)
    response = client.post("/api/v1/ai-agents", json=payload, headers=auth_headers(tokens))
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _run_and_process(client: TestClient, tokens: dict, db_session: Session, agent_id: str) -> dict:
    response = client.post(f"/api/v1/ai-agents/{agent_id}/run", headers=auth_headers(tokens))
    assert response.status_code == 201, response.text
    run_id = response.json()["data"]["id"]
    agent_service.process_agent_run(uuid.UUID(run_id), db=db_session)
    return client.get(f"/api/v1/ai-agent-runs/{run_id}", headers=auth_headers(tokens)).json()["data"]


def test_create_and_list_agent(client: TestClient) -> None:
    tokens = register(client)
    agent = _create_agent(client, tokens)

    assert agent["agent_type"] == "pricing_optimization"
    assert agent["status"] == "active"
    assert agent["configuration"]["scope"] == "all"

    listing = client.get("/api/v1/ai-agents", headers=auth_headers(tokens)).json()["data"]
    assert len(listing) == 1


def test_run_creates_pending_recommendation_under_default_policy(
    client: TestClient, db_session: Session
) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "AGENT-SCARCE-1", on_hand="1000", decrease="950")
    agent = _create_agent(
        client, tokens, configuration={"scope": "products", "product_ids": [ctx["product"]["id"]]}
    )

    run = _run_and_process(client, tokens, db_session, agent["id"])

    assert run["status"] == "completed"
    assert run["output"]["candidates_evaluated"] == 1
    assert run["output"]["auto_applied"] == 0
    item = run["output"]["items"][0]
    assert item["action"] == "created_pending_recommendation"
    assert item["execution_result"]["applied"] is False

    recommendations = client.get("/api/v1/ai-recommendations", headers=auth_headers(tokens)).json()["data"]
    assert any(r["id"] == item["recommendation_id"] and r["status"] == "pending" for r in recommendations)


def test_auto_execute_within_limits_applies_a_real_price(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "AGENT-SCARCE-2", on_hand="1000", decrease="950")
    agent = _create_agent(
        client, tokens, configuration={"scope": "products", "product_ids": [ctx["product"]["id"]]}
    )
    policy_payload = {
        "mode": "auto_execute_within_limits",
        "min_confidence": "0.5",
        "max_price_change_percent": "20",
        "min_margin_percent": "10",
        "approval_required": False,
        "auto_execute": True,
    }
    policy_resp = client.put(
        "/api/v1/ai-policies/pricing_optimization", json=policy_payload, headers=auth_headers(tokens)
    )
    assert policy_resp.status_code == 200, policy_resp.text

    run = _run_and_process(client, tokens, db_session, agent["id"])

    item = run["output"]["items"][0]
    assert item["action"] == "auto_approved_and_applied"
    assert run["output"]["auto_applied"] == 1

    prices = client.get(
        f"/api/v1/pricing?product_id={ctx['product']['id']}", headers=auth_headers(tokens)
    ).json()["data"]
    assert len(prices) >= 1
    assert any(
        abs(float(p["selling_price"]) - float(item["recommendation"]["recommended_price"])) < 0.0001
        for p in prices
    )


def test_policy_price_change_limit_blocks_auto_execute(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "AGENT-SCARCE-3", on_hand="1000", decrease="950")
    agent = _create_agent(
        client, tokens, configuration={"scope": "products", "product_ids": [ctx["product"]["id"]]}
    )
    client.put(
        "/api/v1/ai-policies/pricing_optimization",
        json={
            "mode": "auto_execute_within_limits",
            "max_price_change_percent": "1",
            "approval_required": False,
            "auto_execute": True,
        },
        headers=auth_headers(tokens),
    )

    run = _run_and_process(client, tokens, db_session, agent["id"])

    item = run["output"]["items"][0]
    assert item["action"] == "created_pending_recommendation"
    assert "exceeds the policy maximum" in item["execution_result"]["reason"]


def test_unimplemented_agent_type_run_fails_honestly(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    agent = _create_agent(client, tokens, agent_type="inventory_health", name="Inventory Watcher")

    run = _run_and_process(client, tokens, db_session, agent["id"])

    assert run["status"] == "failed"
    assert "not implemented" in run["error_message"]


def test_inactive_agent_cannot_be_run(client: TestClient) -> None:
    tokens = register(client)
    agent = _create_agent(client, tokens, status="inactive")

    response = client.post(f"/api/v1/ai-agents/{agent['id']}/run", headers=auth_headers(tokens))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "agent_inactive"


def test_delete_blocked_once_agent_has_run_history(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    ctx = _setup(client, tokens, "AGENT-DEL-1", on_hand="100")
    agent = _create_agent(
        client, tokens, configuration={"scope": "products", "product_ids": [ctx["product"]["id"]]}
    )
    _run_and_process(client, tokens, db_session, agent["id"])

    response = client.delete(f"/api/v1/ai-agents/{agent['id']}", headers=auth_headers(tokens))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "agent_has_runs"


def test_delete_succeeds_with_no_run_history(client: TestClient) -> None:
    tokens = register(client)
    agent = _create_agent(client, tokens)

    response = client.delete(f"/api/v1/ai-agents/{agent['id']}", headers=auth_headers(tokens))

    assert response.status_code == 200
    assert client.get(f"/api/v1/ai-agents/{agent['id']}", headers=auth_headers(tokens)).status_code == 404


def test_list_policies_returns_defaults_for_all_agent_types(client: TestClient) -> None:
    tokens = register(client)

    policies = client.get("/api/v1/ai-policies", headers=auth_headers(tokens)).json()["data"]

    assert len(policies) == 5
    types = {p["agent_type"] for p in policies}
    assert types == {
        "pricing_optimization",
        "inventory_health",
        "promotion",
        "device_operations",
        "integration_monitoring",
    }
    assert all(p["mode"] == "recommendation_only" for p in policies)


def test_agents_are_tenant_isolated(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Agent Org A", email="agenta@a.com")
    agent = _create_agent(client, tokens_a)

    tokens_b = register(client, organization_name="Agent Org B", email="agentb@b.com")
    response = client.get(f"/api/v1/ai-agents/{agent['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404


def test_viewer_can_read_but_not_create_agent(client: TestClient, db_session: Session) -> None:
    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    organization_id = uuid.UUID(me["organization"]["id"])

    add_user_with_role(
        db_session, organization_id=organization_id, email="agentviewer@acme.com", role_name="Viewer"
    )
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": "agentviewer@acme.com", "password": "SuperSecret1"}
    ).json()["data"]

    read = client.get("/api/v1/ai-agents", headers=auth_headers(viewer_tokens))
    assert read.status_code == 200

    create = client.post(
        "/api/v1/ai-agents",
        json={"agent_type": "pricing_optimization", "name": "Nope"},
        headers=auth_headers(viewer_tokens),
    )
    assert create.status_code == 403
