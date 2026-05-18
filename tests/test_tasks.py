"""
Tests for /projects/{project_id}/tasks endpoints.
Relies on fixtures from conftest.py: client, db, user_token, make_user, make_token.

Expected conftest fixtures:
    client        — TestClient wrapping the FastAPI app
    db            — SQLAlchemy Session bound to test DB
    user_token    — (user: models.User, token: str) for a default authenticated user
    make_user()   — factory that creates and persists a User, returns models.User
    make_token()  — given a models.User returns a bearer token string
"""
import pytest

from app import models


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(db, owner_id: int) -> models.Project:
    project = models.Project(name="Test Project", owner_id=owner_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _add_member(db, project_id: int, user_id: int) -> None:
    member = models.ProjectMember(project_id=project_id, user_id=user_id)
    db.add(member)
    db.commit()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _task_url(project_id: int, suffix: str = "") -> str:
    return f"/projects/{project_id}/tasks{suffix}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def setup(db, user_token, make_user, make_token):
    """Returns a dict with everything most tests need."""
    user, token = user_token
    project = _make_project(db, owner_id=user.id)
    _add_member(db, project.id, user.id)

    outsider = make_user()
    outsider_token = make_token(outsider)

    member2 = make_user()
    member2_token = make_token(member2)
    _add_member(db, project.id, member2.id)

    return {
        "project": project,
        "user": user,
        "token": token,
        "outsider": outsider,
        "outsider_token": outsider_token,
        "member2": member2,
        "member2_token": member2_token,
    }


@pytest.fixture()
def existing_task(client, setup):
    """Creates a task via POST and returns the response JSON."""
    resp = client.post(
        _task_url(setup["project"].id, "/"),
        json={"title": "Initial task", "description": "desc"},
        headers=_auth(setup["token"]),
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# Auth tests — all endpoints must reject requests with no token (401)
# ---------------------------------------------------------------------------

class TestAuth:
    def test_create_no_auth(self, client, setup):
        r = client.post(_task_url(setup["project"].id, "/"), json={"title": "t"})
        assert r.status_code == 401

    def test_list_no_auth(self, client, setup):
        r = client.get(_task_url(setup["project"].id, "/"))
        assert r.status_code == 401

    def test_get_no_auth(self, client, setup):
        r = client.get(_task_url(setup["project"].id, "/1"))
        assert r.status_code == 401

    def test_update_no_auth(self, client, setup):
        r = client.patch(_task_url(setup["project"].id, "/1"), json={"title": "x"})
        assert r.status_code == 401

    def test_delete_no_auth(self, client, setup):
        r = client.delete(_task_url(setup["project"].id, "/1"))
        assert r.status_code == 401

    def test_status_no_auth(self, client, setup):
        r = client.patch(_task_url(setup["project"].id, "/1/status"), json={"status": "in_progress"})
        assert r.status_code == 401

    def test_assign_no_auth(self, client, setup):
        r = client.patch(_task_url(setup["project"].id, "/1/assign"), json={"assignee_id": 1})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Membership tests — authenticated but not in the project must get 403
# ---------------------------------------------------------------------------

class TestMembership:
    def test_create_non_member(self, client, setup):
        r = client.post(
            _task_url(setup["project"].id, "/"),
            json={"title": "t"},
            headers=_auth(setup["outsider_token"]),
        )
        assert r.status_code == 403

    def test_list_non_member(self, client, setup):
        r = client.get(_task_url(setup["project"].id, "/"), headers=_auth(setup["outsider_token"]))
        assert r.status_code == 403

    def test_get_non_member(self, client, setup, existing_task):
        r = client.get(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            headers=_auth(setup["outsider_token"]),
        )
        assert r.status_code == 403

    def test_update_non_member(self, client, setup, existing_task):
        r = client.patch(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            json={"title": "new"},
            headers=_auth(setup["outsider_token"]),
        )
        assert r.status_code == 403

    def test_delete_non_member(self, client, setup, existing_task):
        r = client.delete(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            headers=_auth(setup["outsider_token"]),
        )
        assert r.status_code == 403

    def test_status_non_member(self, client, setup, existing_task):
        r = client.patch(
            _task_url(setup["project"].id, f"/{existing_task['id']}/status"),
            json={"status": "in_progress"},
            headers=_auth(setup["outsider_token"]),
        )
        assert r.status_code == 403

    def test_assign_non_member(self, client, setup, existing_task):
        r = client.patch(
            _task_url(setup["project"].id, f"/{existing_task['id']}/assign"),
            json={"assignee_id": setup["user"].id},
            headers=_auth(setup["outsider_token"]),
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# CRUD happy path
# ---------------------------------------------------------------------------

class TestCRUD:
    def test_create_returns_201(self, client, setup):
        r = client.post(
            _task_url(setup["project"].id, "/"),
            json={"title": "My task", "description": "some work"},
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "My task"
        assert data["description"] == "some work"
        assert data["project_id"] == setup["project"].id
        assert data["status"] == "todo"
        assert data["assignee_id"] is None

    def test_list_contains_created_task(self, client, setup, existing_task):
        r = client.get(_task_url(setup["project"].id, "/"), headers=_auth(setup["token"]))
        assert r.status_code == 200
        ids = [t["id"] for t in r.json()]
        assert existing_task["id"] in ids

    def test_get_single(self, client, setup, existing_task):
        r = client.get(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 200
        assert r.json()["id"] == existing_task["id"]

    def test_get_missing_returns_404(self, client, setup):
        r = client.get(_task_url(setup["project"].id, "/999999"), headers=_auth(setup["token"]))
        assert r.status_code == 404

    def test_update_title_and_description(self, client, setup, existing_task):
        r = client.patch(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            json={"title": "Updated", "description": "new desc"},
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Updated"
        assert data["description"] == "new desc"

    def test_delete_returns_204(self, client, setup, existing_task):
        r = client.delete(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 204

    def test_get_after_delete_returns_404(self, client, setup, existing_task):
        client.delete(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            headers=_auth(setup["token"]),
        )
        r = client.get(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Status transition tests
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    def _set_status(self, client, setup, task_id: int, new_status: str, token: str | None = None):
        tok = token or setup["token"]
        return client.patch(
            _task_url(setup["project"].id, f"/{task_id}/status"),
            json={"status": new_status},
            headers=_auth(tok),
        )

    def test_todo_to_in_progress(self, client, setup, existing_task):
        r = self._set_status(client, setup, existing_task["id"], "in_progress")
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

    def test_in_progress_to_done(self, client, setup, existing_task):
        self._set_status(client, setup, existing_task["id"], "in_progress")
        r = self._set_status(client, setup, existing_task["id"], "done")
        assert r.status_code == 200
        assert r.json()["status"] == "done"

    def test_back_transition_done_to_in_progress(self, client, setup, existing_task):
        self._set_status(client, setup, existing_task["id"], "in_progress")
        self._set_status(client, setup, existing_task["id"], "done")
        r = self._set_status(client, setup, existing_task["id"], "in_progress")
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

    def test_back_transition_in_progress_to_todo(self, client, setup, existing_task):
        self._set_status(client, setup, existing_task["id"], "in_progress")
        r = self._set_status(client, setup, existing_task["id"], "todo")
        assert r.status_code == 200
        assert r.json()["status"] == "todo"

    def test_forward_skip_todo_to_done_is_rejected(self, client, setup, existing_task):
        r = self._set_status(client, setup, existing_task["id"], "done")
        assert r.status_code == 422

    def test_invalid_enum_value_is_rejected(self, client, setup, existing_task):
        r = self._set_status(client, setup, existing_task["id"], "flying")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Assignment tests
# ---------------------------------------------------------------------------

class TestAssignment:
    def test_assign_to_project_member_succeeds(self, client, setup, existing_task):
        r = client.patch(
            _task_url(setup["project"].id, f"/{existing_task['id']}/assign"),
            json={"assignee_id": setup["member2"].id},
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 200
        assert r.json()["assignee_id"] == setup["member2"].id

    def test_assign_to_non_member_returns_422(self, client, setup, existing_task):
        r = client.patch(
            _task_url(setup["project"].id, f"/{existing_task['id']}/assign"),
            json={"assignee_id": setup["outsider"].id},
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 422

    def test_create_with_assignee_member_succeeds(self, client, setup):
        r = client.post(
            _task_url(setup["project"].id, "/"),
            json={"title": "Assigned task", "assignee_id": setup["member2"].id},
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 201
        assert r.json()["assignee_id"] == setup["member2"].id

    def test_create_with_assignee_non_member_returns_403(self, client, setup):
        r = client.post(
            _task_url(setup["project"].id, "/"),
            json={"title": "Bad task", "assignee_id": setup["outsider"].id},
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 403

    def test_update_assignee_to_non_member_returns_403(self, client, setup, existing_task):
        r = client.patch(
            _task_url(setup["project"].id, f"/{existing_task['id']}"),
            json={"assignee_id": setup["outsider"].id},
            headers=_auth(setup["token"]),
        )
        assert r.status_code == 403
