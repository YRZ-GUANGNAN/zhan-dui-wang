import asyncio
import datetime as dt
import os

import jwt
import pytest
from fastapi import HTTPException, UploadFile, WebSocketDisconnect
from fastapi.testclient import TestClient

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-with-sufficient-entropy")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")

from backend import api_service


client = TestClient(api_service.app)


def token(user_id=1, expires_in=300):
    now = dt.datetime.now(dt.timezone.utc)
    return jwt.encode(
        {
            "userId": user_id,
            "sub": f"user-{user_id}",
            "iat": now,
            "exp": now + dt.timedelta(seconds=expires_in),
        },
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )


def auth(user_id=1):
    return {"Authorization": f"Bearer {token(user_id)}"}


def test_health_is_public():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_id_header_is_returned():
    response = client.get(
        "/api/health",
        headers={"X-Request-ID": "request-id-test-123"},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-id-test-123"


def test_invalid_request_id_is_replaced():
    response = client.get("/api/health", headers={"X-Request-ID": "bad id"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "bad id"
    assert len(response.headers["X-Request-ID"]) == 24


def test_malformed_json_returns_bad_request_with_request_id():
    response = client.post(
        "/api/admin/login",
        content="{bad-json",
        headers={
            "Content-Type": "application/json",
            "X-Request-ID": "bad-json-test-123",
        },
    )
    assert response.status_code == 400
    assert response.headers["X-Request-ID"] == "bad-json-test-123"
    assert response.json() == {"detail": "Invalid JSON"}


def test_readiness_checks_database(monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.connection = self
            self.closed = False

        def cursor(self):
            return self

        def execute(self, sql):
            assert sql == "SELECT 1"

        def fetchone(self):
            return (1,)

        def close(self):
            self.closed = True

    fake = FakeConnection()
    monkeypatch.setattr(api_service, "db", lambda: fake)
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert fake.closed is True


def test_private_api_requires_token():
    response = client.get("/api/conversations", params={"userId": 1})
    assert response.status_code == 401


def test_expired_token_is_rejected():
    response = client.get(
        "/api/conversations",
        params={"userId": 1},
        headers={"Authorization": f"Bearer {token(1, expires_in=-1)}"},
    )
    assert response.status_code == 401


def test_query_user_id_cannot_be_spoofed():
    response = client.get(
        "/api/conversations",
        params={"userId": 2},
        headers=auth(1),
    )
    assert response.status_code == 403


def test_path_user_id_cannot_be_spoofed():
    response = client.put(
        "/api/users/2/profile",
        json={"nickname": "not-allowed"},
        headers=auth(1),
    )
    assert response.status_code == 403


def test_multipart_sender_id_cannot_be_spoofed():
    response = client.post(
        "/api/messages/image",
        data={"senderId": "2", "receiverId": "3"},
        files={"file": ("image.png", b"\x89PNG\r\n\x1a\ncontent", "image/png")},
        headers=auth(1),
    )
    assert response.status_code == 403


def test_admin_conversations_route_is_not_shadowed():
    admin_routes = [
        route
        for route in api_service.app.routes
        if getattr(route, "path", None) == "/api/admin/conversations"
    ]
    assert len(admin_routes) == 1
    assert admin_routes[0].endpoint.__name__ == "admin_conversations"


def test_admin_login_success_is_audited(monkeypatch):
    events = []

    def fake_log_audit(_request, event, level=api_service.logging.INFO, **fields):
        events.append((event, level, fields))

    monkeypatch.setattr(api_service, "log_audit", fake_log_audit)
    response = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "test-admin-password"},
    )

    assert response.status_code == 200
    assert events == [
        ("admin_login_success", api_service.logging.INFO, {"username": "admin"})
    ]


def test_admin_login_failure_is_audited(monkeypatch):
    events = []

    def fake_log_audit(_request, event, level=api_service.logging.INFO, **fields):
        events.append((event, level, fields))

    monkeypatch.setattr(api_service, "log_audit", fake_log_audit)
    response = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert events == [
        ("admin_login_failed", api_service.logging.WARNING, {"username": "admin"})
    ]


def test_admin_delete_user_is_audited(monkeypatch):
    events = []

    class FakeCursor:
        def __init__(self):
            self.connection = self
            self.sql = None
            self.args = None
            self.committed = False
            self.closed = False

        def cursor(self):
            return self

        def execute(self, sql, args):
            self.sql = sql
            self.args = args

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    fake = FakeCursor()

    def fake_log_audit(_request, event, level=api_service.logging.INFO, **fields):
        events.append((event, level, fields))

    monkeypatch.setattr(api_service, "check_admin", lambda _request: True)
    monkeypatch.setattr(api_service, "db", lambda: fake)
    monkeypatch.setattr(api_service, "log_audit", fake_log_audit)

    response = client.delete("/api/admin/users/42")

    assert response.status_code == 200
    assert fake.sql == "DELETE FROM users WHERE id=%s"
    assert fake.args == (42,)
    assert fake.committed is True
    assert fake.closed is True
    assert events == [
        ("admin_delete_user", api_service.logging.INFO, {"target_user_id": 42})
    ]


def test_image_type_comes_from_content(tmp_path, monkeypatch):
    monkeypatch.setattr(api_service, "UPLOAD_ROOT", str(tmp_path))
    upload = UploadFile(filename="payload.html", file=None)

    async def read(_size):
        return b"\x89PNG\r\n\x1a\n" + b"safe-image-data"

    upload.read = read
    url = asyncio.run(api_service.save_image(upload, "avatars"))
    assert url.startswith("/uploads/avatars/")
    assert url.endswith(".png")
    assert list((tmp_path / "avatars").glob("*.png"))


def test_non_image_upload_is_rejected():
    upload = UploadFile(filename="payload.html", file=None)

    async def read(_size):
        return b"<html>not an image</html>"

    upload.read = read
    with pytest.raises(HTTPException) as exc:
        asyncio.run(api_service.save_image(upload, "avatars"))
    assert exc.value.status_code == 415


def test_websocket_rejects_invalid_token():
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "auth", "token": "invalid"})
            websocket.receive_json()
    assert exc.value.code == 4401


def test_websocket_delivers_ack(monkeypatch):
    def fake_persist(sender_id, receiver_id, content, client_id, image_url=None):
        assert image_url is None
        return {
            "id": 99,
            "clientId": client_id,
            "content": content,
            "imageUrl": None,
            "createTime": "2026-06-28 22:00:00",
            "sender": {"id": sender_id},
            "receiver": {"id": receiver_id},
        }

    monkeypatch.setattr(api_service, "persist_message", fake_persist)
    with client.websocket_connect("/ws") as sender:
        sender.send_json({"type": "auth", "token": token(1)})
        assert sender.receive_json() == {"type": "ready", "userId": 1}

        sender.send_json({
            "type": "message",
            "receiverId": 2,
            "content": "hello",
            "clientId": "client-message-1",
        })
        ack = sender.receive_json()

        assert ack["type"] == "ack"
        assert ack["clientId"] == "client-message-1"
        assert ack["message"]["id"] == 99


def test_connection_manager_routes_messages():
    class FakeSocket:
        def __init__(self):
            self.messages = []

        async def send_json(self, payload):
            self.messages.append(payload)

    async def exercise():
        manager = api_service.ChatConnectionManager()
        socket = FakeSocket()
        assert await manager.connect(2, socket) is True
        await manager.send_to_user(2, {"type": "message", "message": {"id": 99}})
        manager.disconnect(2, socket)
        assert socket.messages == [
            {"type": "message", "message": {"id": 99}}
        ]
        assert 2 not in manager.connections

    asyncio.run(exercise())
