import pytest
from httpx import AsyncClient

AUTH_HEADERS = {"Authorization": "Bearer test-token-user999-owner@example.com"}
OTHER_USER_HEADERS = {"Authorization": "Bearer test-token-user888-other@example.com"}


@pytest.mark.asyncio
async def test_add_domain_success(async_client: AsyncClient):
    payload = {"hostname": "https://secure-store.in/products"}
    response = await async_client.post("/api/v1/domains", json=payload, headers=AUTH_HEADERS)

    assert response.status_code == 201
    data = response.json()
    assert data["hostname"] == "secure-store.in"
    assert data["status"] == "pending"
    assert "verify_token" in data
    assert data["dns_record_value"] == f"datasecurely-verify={data['verify_token']}"
    assert "well_known_url" in data


@pytest.mark.asyncio
async def test_add_duplicate_domain_conflict(async_client: AsyncClient):
    payload = {"hostname": "duplicate-test.com"}
    res1 = await async_client.post("/api/v1/domains", json=payload, headers=AUTH_HEADERS)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/domains", json=payload, headers=AUTH_HEADERS)
    assert res2.status_code == 409
    assert "already been added" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_add_invalid_domain_unprocessable(async_client: AsyncClient):
    payload = {"hostname": "192.168.1.1"}
    response = await async_client.post("/api/v1/domains", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 422
    assert "Direct IP addresses" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_and_get_domain(async_client: AsyncClient):
    # Add domain
    add_res = await async_client.post(
        "/api/v1/domains",
        json={"hostname": "list-check.com"},
        headers=AUTH_HEADERS,
    )
    domain_id = add_res.json()["id"]

    # List
    list_res = await async_client.get("/api/v1/domains", headers=AUTH_HEADERS)
    assert list_res.status_code == 200
    items = list_res.json()["domains"]
    assert any(d["id"] == domain_id for d in items)

    # Get by ID
    get_res = await async_client.get(f"/api/v1/domains/{domain_id}", headers=AUTH_HEADERS)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == domain_id
    assert get_res.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_delete_domain(async_client: AsyncClient):
    add_res = await async_client.post(
        "/api/v1/domains",
        json={"hostname": "delete-check.com"},
        headers=AUTH_HEADERS,
    )
    domain_id = add_res.json()["id"]

    # Delete
    del_res = await async_client.delete(f"/api/v1/domains/{domain_id}", headers=AUTH_HEADERS)
    assert del_res.status_code == 204

    # Verify not found
    get_res = await async_client.get(f"/api/v1/domains/{domain_id}", headers=AUTH_HEADERS)
    assert get_res.status_code == 404
