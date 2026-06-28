import asyncio
import datetime as dt
import os

import jwt
import pytest
from fastapi import HTTPException, UploadFile
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
