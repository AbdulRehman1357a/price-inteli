from fastapi.testclient import TestClient

from tests.helpers import auth_headers, register


def test_user_list_never_crosses_organizations(client: TestClient) -> None:
    org_a_tokens = register(
        client, organization_name="Org A", email="admin-a@acme.com", password="SuperSecret1"
    )
    org_b_tokens = register(
        client, organization_name="Org B", email="admin-b@acme.com", password="SuperSecret1"
    )

    org_a_users = client.get("/api/v1/users", headers=auth_headers(org_a_tokens)).json()["data"]
    org_b_users = client.get("/api/v1/users", headers=auth_headers(org_b_tokens)).json()["data"]

    assert [u["email"] for u in org_a_users] == ["admin-a@acme.com"]
    assert [u["email"] for u in org_b_users] == ["admin-b@acme.com"]

    org_a_id = org_a_users[0]["organization_id"]
    org_b_id = org_b_users[0]["organization_id"]
    assert org_a_id != org_b_id
    assert all(u["organization_id"] == org_a_id for u in org_a_users)
    assert all(u["organization_id"] == org_b_id for u in org_b_users)


def test_me_reflects_only_the_callers_own_organization(client: TestClient) -> None:
    org_a_tokens = register(
        client, organization_name="Org A", email="admin-a@acme.com", password="SuperSecret1"
    )
    org_b_tokens = register(
        client, organization_name="Org B", email="admin-b@acme.com", password="SuperSecret1"
    )

    me_a = client.get("/api/v1/auth/me", headers=auth_headers(org_a_tokens)).json()["data"]
    me_b = client.get("/api/v1/auth/me", headers=auth_headers(org_b_tokens)).json()["data"]

    assert me_a["organization"]["name"] == "Org A"
    assert me_b["organization"]["name"] == "Org B"
    assert me_a["organization"]["id"] != me_b["organization"]["id"]
