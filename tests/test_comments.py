"""Tests for /tasks/{task_id}/comments endpoints."""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client: TestClient, email: str, password: str = "pass1234") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def owner_token(client: TestClient) -> str:
    return _register_and_login(client, "owner@example.com")


@pytest.fixture()
def member_token(client: TestClient) -> str:
    return _register_and_login(client, "member@example.com")


@pytest.fixture()
def outsider_token(client: TestClient) -> str:
    return _register_and_login(client, "outsider@example.com")


@pytest.fixture()
def project(client: TestClient, owner_token: str) -> dict:
    resp = client.post(
        "/projects/",
        json={"name": "Test Project"},
        headers=_auth(owner_token),
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def project_with_member(client: TestClient, project: dict, member_token: str, owner_token: str) -> dict:
    """Add the member user to the project."""
    # Retrieve member's user id
    me_resp = client.get("/users/me", headers=_auth(member_token))
    member_id = me_resp.json()["id"]
    client.post(
        f"/projects/{project['id']}/members",
        json={"user_id": member_id},
        headers=_auth(owner_token),
    )
    return project


@pytest.fixture()
def task(client: TestClient, project_with_member: dict, owner_token: str) -> dict:
    resp = client.post(
        "/tasks/",
        json={"title": "Task 1", "project_id": project_with_member["id"]},
        headers=_auth(owner_token),
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def task2(client: TestClient, project_with_member: dict, owner_token: str) -> dict:
    resp = client.post(
        "/tasks/",
        json={"title": "Task 2", "project_id": project_with_member["id"]},
        headers=_auth(owner_token),
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def comment(client: TestClient, task: dict, member_token: str) -> dict:
    resp = client.post(
        f"/tasks/{task['id']}/comments/",
        json={"content": "Initial comment"},
        headers=_auth(member_token),
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Step 8 – create comment as project member
# ---------------------------------------------------------------------------

def test_create_comment_as_member(client: TestClient, task: dict, member_token: str):
    resp = client.post(
        f"/tasks/{task['id']}/comments/",
        json={"content": "Hello from member"},
        headers=_auth(member_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Hello from member"
    assert data["task_id"] == task["id"]
    assert "id" in data
    assert "author_id" in data


# ---------------------------------------------------------------------------
# Step 9 – non-member cannot create comment
# ---------------------------------------------------------------------------

def test_create_comment_as_non_member(client: TestClient, task: dict, outsider_token: str):
    resp = client.post(
        f"/tasks/{task['id']}/comments/",
        json={"content": "Sneaky comment"},
        headers=_auth(outsider_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Step 10 – unauthenticated POST returns 401
# ---------------------------------------------------------------------------

def test_create_comment_unauthenticated(client: TestClient, task: dict):
    resp = client.post(
        f"/tasks/{task['id']}/comments/",
        json={"content": "No token"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Step 11 – list comments scoped to a single task
# ---------------------------------------------------------------------------

def test_list_comments_scoped_to_task(
    client: TestClient,
    task: dict,
    task2: dict,
    member_token: str,
):
    client.post(
        f"/tasks/{task['id']}/comments/",
        json={"content": "Comment on task 1"},
        headers=_auth(member_token),
    )
    client.post(
        f"/tasks/{task2['id']}/comments/",
        json={"content": "Comment on task 2"},
        headers=_auth(member_token),
    )

    resp = client.get(f"/tasks/{task['id']}/comments/", headers=_auth(member_token))
    assert resp.status_code == 200
    comments = resp.json()
    assert all(c["task_id"] == task["id"] for c in comments)
    contents = [c["content"] for c in comments]
    assert "Comment on task 1" in contents
    assert "Comment on task 2" not in contents


# ---------------------------------------------------------------------------
# Step 12 – get comment by id
# ---------------------------------------------------------------------------

def test_get_comment_by_id(client: TestClient, task: dict, comment: dict, member_token: str):
    resp = client.get(
        f"/tasks/{task['id']}/comments/{comment['id']}",
        headers=_auth(member_token),
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == comment["id"]
    assert resp.json()["content"] == comment["content"]


# ---------------------------------------------------------------------------
# Step 13 – get comment scoped to wrong task returns 404
# ---------------------------------------------------------------------------

def test_get_comment_wrong_task(
    client: TestClient,
    task: dict,
    task2: dict,
    comment: dict,
    member_token: str,
):
    # comment belongs to task, not task2
    resp = client.get(
        f"/tasks/{task2['id']}/comments/{comment['id']}",
        headers=_auth(member_token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Step 14 – author can PATCH own comment
# ---------------------------------------------------------------------------

def test_patch_comment_as_author(client: TestClient, task: dict, comment: dict, member_token: str):
    resp = client.patch(
        f"/tasks/{task['id']}/comments/{comment['id']}",
        json={"content": "Updated content"},
        headers=_auth(member_token),
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated content"


# ---------------------------------------------------------------------------
# Step 15 – non-author cannot PATCH
# ---------------------------------------------------------------------------

def test_patch_comment_as_non_author(
    client: TestClient,
    task: dict,
    comment: dict,
    owner_token: str,
):
    resp = client.patch(
        f"/tasks/{task['id']}/comments/{comment['id']}",
        json={"content": "Overwrite"},
        headers=_auth(owner_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Step 16 – author can DELETE own comment
# ---------------------------------------------------------------------------

def test_delete_comment_as_author(client: TestClient, task: dict, comment: dict, member_token: str):
    resp = client.delete(
        f"/tasks/{task['id']}/comments/{comment['id']}",
        headers=_auth(member_token),
    )
    assert resp.status_code == 204
    # Confirm gone
    get_resp = client.get(
        f"/tasks/{task['id']}/comments/{comment['id']}",
        headers=_auth(member_token),
    )
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Step 17 – project owner can DELETE any comment
# ---------------------------------------------------------------------------

def test_delete_comment_as_project_owner(
    client: TestClient,
    task: dict,
    comment: dict,
    owner_token: str,
    member_token: str,
):
    resp = client.delete(
        f"/tasks/{task['id']}/comments/{comment['id']}",
        headers=_auth(owner_token),
    )
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Step 18 – member who is neither author nor owner cannot DELETE
# ---------------------------------------------------------------------------

def test_delete_comment_as_non_author_non_owner(
    client: TestClient,
    client_db,  # access to db session for direct fixture setup if needed
    task: dict,
    project_with_member: dict,
    comment: dict,
    owner_token: str,
):
    # Register a second member and add them to the project
    third_token = _register_and_login(client, "third@example.com")
    me_resp = client.get("/users/me", headers=_auth(third_token))
    third_id = me_resp.json()["id"]
    client.post(
        f"/projects/{project_with_member['id']}/members",
        json={"user_id": third_id},
        headers=_auth(owner_token),
    )
    resp = client.delete(
        f"/tasks/{task['id']}/comments/{comment['id']}",
        headers=_auth(third_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Step 19 – all five endpoints require authentication
# ---------------------------------------------------------------------------

def test_endpoints_require_auth(client: TestClient, task: dict, comment: dict):
    task_id = task["id"]
    comment_id = comment["id"]
    base = f"/tasks/{task_id}/comments"

    endpoints = [
        ("POST", f"{base}/", {"content": "x"}),
        ("GET", f"{base}/", None),
        ("GET", f"{base}/{comment_id}", None),
        ("PATCH", f"{base}/{comment_id}", {"content": "y"}),
        ("DELETE", f"{base}/{comment_id}", None),
    ]

    for method, url, payload in endpoints:
        if method == "POST":
            resp = client.post(url, json=payload)
        elif method == "GET":
            resp = client.get(url)
        elif method == "PATCH":
            resp = client.patch(url, json=payload)
        elif method == "DELETE":
            resp = client.delete(url)
        assert resp.status_code == 401, f"{method} {url} should return 401, got {resp.status_code}"
