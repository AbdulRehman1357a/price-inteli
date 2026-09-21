import uuid

from fastapi.testclient import TestClient

from tests.helpers import add_user_with_role, auth_headers, output_channel_payload, register, store_payload


def test_create_esl_channel_success(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels", json=output_channel_payload(), headers=auth_headers(tokens)
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["name"] == "Front Window ESL"
    assert data["output_type"] == "esl_simulator"
    assert data["status"] == "active"
    assert data["store_id"] is None


def test_create_channel_with_store(client: TestClient) -> None:
    tokens = register(client)
    store = client.post(
        "/api/v1/stores", json=store_payload(), headers=auth_headers(tokens)
    ).json()["data"]

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(store_id=store["id"]),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text
    assert response.json()["data"]["store_id"] == store["id"]


def test_create_channel_rejects_unknown_store(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(store_id="00000000-0000-0000-0000-000000000000"),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 404


def test_create_qr_channel_valid_configuration(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(
            name="QR Kiosk", output_type="qr_code", configuration={"box_size": 6, "error_correction": "H"}
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text


def test_create_qr_channel_rejects_unknown_configuration_key(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(output_type="qr_code", configuration={"not_a_real_key": True}),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_create_qr_channel_rejects_invalid_error_correction(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(output_type="qr_code", configuration={"error_correction": "Z"}),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_create_channel_rejects_wrong_configuration_type(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(output_type="pdf_label", configuration={"label_width_mm": "sixty"}),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_create_pdf_channel_accepts_format_configuration(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(
            name="PDF",
            output_type="pdf_label",
            configuration={
                "show_qr": True,
                "qr_position": "left",
                "qr_size_mm": 16,
                "show_unit_price": False,
                "banner_position": "top",
            },
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 201, response.text


def test_create_pdf_channel_rejects_unknown_qr_position(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(
            output_type="pdf_label", configuration={"qr_position": "middle"}
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_create_pdf_channel_rejects_unknown_banner_position(client: TestClient) -> None:
    tokens = register(client)

    response = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(
            output_type="pdf_label", configuration={"banner_position": "up"}
        ),
        headers=auth_headers(tokens),
    )

    assert response.status_code == 422


def test_list_channels(client: TestClient) -> None:
    tokens = register(client)
    client.post("/api/v1/outputs/channels", json=output_channel_payload(), headers=auth_headers(tokens))
    client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(name="QR", output_type="qr_code"),
        headers=auth_headers(tokens),
    )

    response = client.get(
        "/api/v1/outputs/channels", params={"output_type": "qr_code"}, headers=auth_headers(tokens)
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["output_type"] == "qr_code"


def test_get_channel_by_id(client: TestClient) -> None:
    tokens = register(client)
    created = client.post(
        "/api/v1/outputs/channels", json=output_channel_payload(), headers=auth_headers(tokens)
    ).json()["data"]

    response = client.get(f"/api/v1/outputs/channels/{created['id']}", headers=auth_headers(tokens))

    assert response.status_code == 200
    assert response.json()["data"]["id"] == created["id"]


def test_update_channel_status_and_configuration(client: TestClient) -> None:
    tokens = register(client)
    created = client.post(
        "/api/v1/outputs/channels",
        json=output_channel_payload(output_type="esl_simulator"),
        headers=auth_headers(tokens),
    ).json()["data"]

    response = client.put(
        f"/api/v1/outputs/channels/{created['id']}",
        json={"status": "inactive", "configuration": {"theme": "dark"}},
        headers=auth_headers(tokens),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "inactive"
    assert data["configuration"] == {"theme": "dark"}


def test_channel_not_visible_across_organizations(client: TestClient) -> None:
    tokens_a = register(client, organization_name="Org A", email="a@example.com")
    created = client.post(
        "/api/v1/outputs/channels", json=output_channel_payload(), headers=auth_headers(tokens_a)
    ).json()["data"]

    tokens_b = register(client, organization_name="Org B", email="b@example.com")
    response = client.get(f"/api/v1/outputs/channels/{created['id']}", headers=auth_headers(tokens_b))

    assert response.status_code == 404


def test_viewer_cannot_create_channel(client: TestClient, db_session) -> None:
    tokens = register(client)
    me = client.get("/api/v1/auth/me", headers=auth_headers(tokens)).json()["data"]
    viewer = add_user_with_role(
        db_session,
        organization_id=uuid.UUID(me["organization"]["id"]),
        email="viewer@example.com",
        role_name="Viewer",
    )
    viewer_tokens = client.post(
        "/api/v1/auth/login", json={"email": viewer.email, "password": "SuperSecret1"}
    ).json()["data"]

    response = client.post(
        "/api/v1/outputs/channels", json=output_channel_payload(), headers=auth_headers(viewer_tokens)
    )

    assert response.status_code == 403
