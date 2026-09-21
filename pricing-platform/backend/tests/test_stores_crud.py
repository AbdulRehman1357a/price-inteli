import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import add_user_with_role, auth_headers, register, store_payload


def test_create_store_success(client: TestClient) -> None:
    tokens = register(client)

    response = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens))

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["store_code"] == "NYC-001"
    assert data["status"] == "active"
    assert data["organization_id"] == response.json()["data"]["organization_id"]


def test_create_store_missing_required_field_returns_422(client: TestClient) -> None:
    tokens = register(client)
    payload = store_payload()
    del payload["address_line_1"]

    response = client.post("/api/v1/stores", json=payload, headers=auth_headers(tokens))

    assert response.status_code == 422


def test_create_store_duplicate_code_in_same_org_conflicts(client: TestClient) -> None:
    tokens = register(client)
    client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens))

    response = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "store_code_taken"


def test_same_store_code_allowed_across_different_orgs(client: TestClient) -> None:
    org_a = register(client, organization_name="Org A", email="admin-a@acme.com")
    org_b = register(client, organization_name="Org B", email="admin-b@acme.com")

    resp_a = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(org_a))
    resp_b = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(org_b))

    assert resp_a.status_code == 201
    assert resp_b.status_code == 201


def test_get_store_by_id(client: TestClient) -> None:
    tokens = register(client)
    created = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()[
        "data"
    ]

    response = client.get(f"/api/v1/stores/{created['id']}", headers=auth_headers(tokens))

    assert response.status_code == 200
    assert response.json()["data"]["store_code"] == "NYC-001"


def test_get_unknown_store_returns_404(client: TestClient) -> None:
    tokens = register(client)

    response = client.get(
        "/api/v1/stores/00000000-0000-0000-0000-000000000000", headers=auth_headers(tokens)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"


def test_update_store_partial(client: TestClient) -> None:
    tokens = register(client)
    created = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()[
        "data"
    ]

    response = client.put(
        f"/api/v1/stores/{created['id']}",
        json={"name": "Renamed Store", "status": "inactive"},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Renamed Store"
    assert data["status"] == "inactive"
    # Untouched fields survive the partial update.
    assert data["store_code"] == "NYC-001"
    assert data["city"] == "New York"


def test_update_store_to_duplicate_code_conflicts(client: TestClient) -> None:
    tokens = register(client)
    client.post("/api/v1/stores", json=store_payload(store_code="A-1"), headers=auth_headers(tokens))
    second = client.post(
        "/api/v1/stores", json=store_payload(store_code="A-2"), headers=auth_headers(tokens)
    ).json()["data"]

    response = client.put(
        f"/api/v1/stores/{second['id']}", json={"store_code": "A-1"}, headers=auth_headers(tokens)
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "store_code_taken"


def test_delete_store_soft_deletes(client: TestClient) -> None:
    tokens = register(client)
    created = client.post("/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)).json()[
        "data"
    ]

    delete_response = client.delete(f"/api/v1/stores/{created['id']}", headers=auth_headers(tokens))
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["deleted"] is True

    get_response = client.get(f"/api/v1/stores/{created['id']}", headers=auth_headers(tokens))
    assert get_response.status_code == 404

    list_response = client.get("/api/v1/stores", headers=auth_headers(tokens))
    assert created["id"] not in [s["id"] for s in list_response.json()["data"]]


def test_list_stores_pagination(client: TestClient) -> None:
    tokens = register(client)
    for i in range(5):
        client.post(
            "/api/v1/stores", json=store_payload(store_code=f"S-{i}"), headers=auth_headers(tokens)
        )

    response = client.get("/api/v1/stores?page=1&page_size=2", headers=auth_headers(tokens))

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 5
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 2
    assert body["meta"]["total_pages"] == 3


def test_list_stores_search_matches_name_code_or_city(client: TestClient) -> None:
    tokens = register(client)
    client.post(
        "/api/v1/stores",
        json=store_payload(store_code="LDN-01", name="London Bridge", city="London"),
        headers=auth_headers(tokens),
    )
    client.post(
        "/api/v1/stores",
        json=store_payload(store_code="NYC-01", name="Times Square", city="New York"),
        headers=auth_headers(tokens),
    )

    response = client.get("/api/v1/stores?search=london", headers=auth_headers(tokens))

    assert response.status_code == 200
    names = [s["name"] for s in response.json()["data"]]
    assert names == ["London Bridge"]


def test_list_stores_status_and_type_filters(client: TestClient) -> None:
    tokens = register(client)
    client.post(
        "/api/v1/stores",
        json=store_payload(store_code="A", store_type="flagship", status="active"),
        headers=auth_headers(tokens),
    )
    client.post(
        "/api/v1/stores",
        json=store_payload(store_code="B", store_type="outlet", status="inactive"),
        headers=auth_headers(tokens),
    )

    by_status = client.get("/api/v1/stores?status=inactive", headers=auth_headers(tokens)).json()["data"]
    assert [s["store_code"] for s in by_status] == ["B"]

    by_type = client.get("/api/v1/stores?store_type=flagship", headers=auth_headers(tokens)).json()[
        "data"
    ]
    assert [s["store_code"] for s in by_type] == ["A"]


def test_role_without_stores_permissions_is_denied(client: TestClient, db_session: Session) -> None:
    admin_tokens = register(client)
    organization_id = client.get("/api/v1/auth/me", headers=auth_headers(admin_tokens)).json()["data"][
        "user"
    ]["organization_id"]

    add_user_with_role(
        db_session,
        organization_id=uuid.UUID(organization_id),
        email="pricingmgr@acme.com",
        role_name="Pricing Manager",
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "pricingmgr@acme.com", "password": "SuperSecret1"}
    )
    pricing_tokens = login.json()["data"]

    response = client.get("/api/v1/stores", headers=auth_headers(pricing_tokens))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
