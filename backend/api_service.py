"""湛对网 统一API服务 (替代Java后端)"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi import UploadFile, File, Form
from pymysql import connect
from pymysql.cursors import DictCursor
import bcrypt, jwt as pyjwt, datetime as dt, secrets, json, uvicorn, random
import os

app = FastAPI(title="湛对网API")

# Rate limiting
import collections, time as time_mod
_rate_limits = collections.defaultdict(list)
def rate_limit(key: str, max_req: int = 30, window: int = 60):
    now = time_mod.time()
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < window]
    if len(_rate_limits[key]) >= max_req:
        raise HTTPException(429, "请求太频繁，请稍后再试")
    _rate_limits[key].append(now)

def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DB = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": required_env("DB_USER"),
    "password": required_env("DB_PASSWORD"),
    "database": required_env("DB_NAME"),
    "charset": "utf8mb4",
    "connect_timeout": 5,
    "read_timeout": 10,
    "write_timeout": 10,
}
JWT_SECRET = required_env("JWT_SECRET")

def db(): return connect(**DB)


PUBLIC_API_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/health",
    "/api/public/stats",
    "/api/admin/login",
}


@app.middleware("http")
async def authenticate_api_request(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in PUBLIC_API_PATHS and not path.startswith("/api/admin/"):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return JSONResponse({"detail": "Authentication required"}, status_code=401)
        try:
            payload = pyjwt.decode(authorization[7:], JWT_SECRET, algorithms=["HS256"])
            request.state.user_id = int(payload["userId"])
        except (pyjwt.PyJWTError, KeyError, TypeError, ValueError):
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        for key in ("userId", "senderId"):
            claimed = request.query_params.get(key)
            if claimed is not None:
                try:
                    if int(claimed) != request.state.user_id:
                        return JSONResponse({"detail": "Forbidden"}, status_code=403)
                except ValueError:
                    return JSONResponse({"detail": f"Invalid {key}"}, status_code=400)
    return await call_next(request)


def require_self(request: Request, claimed_user_id) -> int:
    try:
        claimed = int(claimed_user_id)
    except (TypeError, ValueError):
        raise HTTPException(400, "Invalid userId")
    if claimed != request.state.user_id:
        raise HTTPException(403, "Forbidden")
    return claimed


MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(4 * 1024 * 1024)))
UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", "/opt/zhandui/uploads")


def image_extension(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    raise HTTPException(415, "仅支持 JPG、PNG 或 WebP 图片")


async def save_image(file: UploadFile, category: str) -> str:
    data = await file.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(400, "图片不能为空")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "图片大小超过限制")
    extension = image_extension(data)
    directory = os.path.join(UPLOAD_ROOT, category)
    os.makedirs(directory, exist_ok=True)
    filename = f"{secrets.token_hex(16)}.{extension}"
    path = os.path.join(directory, filename)
    with open(path, "xb") as output:
        output.write(data)
    return f"/uploads/{category}/{filename}"
def ok(data): return data

# ===== AUTH =====
@app.post("/api/auth/login")
async def login(req: Request):
    rate_limit(f"login_{req.client.host}", 10, 60)
    data = await req.json()
    u = data.get("username","").strip()
    p = data.get("password","").strip()
    if not u or not p: raise HTTPException(400, "用户名密码不能为空")
    c = db().cursor(DictCursor)
    c.execute("SELECT id,username,password,nickname FROM users WHERE username=%s",(u,))
    user = c.fetchone()
    c.connection.close()
    if not user: raise HTTPException(401, "用户不存在")
    if not bcrypt.checkpw(p.encode(), user['password'].encode()): raise HTTPException(401, "密码错误")
    token = pyjwt.encode({"userId":user['id'],"sub":user['username'],"iat":dt.datetime.utcnow(),"exp":dt.datetime.utcnow()+dt.timedelta(days=7)}, JWT_SECRET, algorithm="HS256")
    return {"token":token,"userId":user['id'],"username":user['username']}

@app.post("/api/auth/register")
async def register(req: Request):
    rate_limit(f"register_{req.client.host}", 5, 60)  # 5 reg/minute
    data = await req.json()
    u = data.get("username","").strip()
    p = data.get("password","").strip()
    e = data.get("email","").strip()
    n = data.get("nickname",u)
    g = data.get("gender","")
    if len(u)<3: raise HTTPException(400, "用户名至少3位")
    if len(p)<6: raise HTTPException(400, "密码至少6位")
    if not e: e = f"{u}@zhandui.com"
    hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
    c = db().cursor()
    try:
        c.execute("INSERT INTO users (username,password,email,nickname,gender,is_active,show_on_planet,create_time) VALUES (%s,%s,%s,%s,%s,1,1,NOW())",(u,hashed,e,n,g))
        c.connection.commit()
        uid = c.lastrowid
    except Exception:
        c.connection.close()
        raise HTTPException(400, "注册失败，请检查用户名或邮箱是否已存在")
    c.connection.close()
    token = pyjwt.encode({"userId":uid,"sub":u,"iat":dt.datetime.utcnow(),"exp":dt.datetime.utcnow()+dt.timedelta(days=7)}, JWT_SECRET, algorithm="HS256")
    return {"token":token,"userId":uid,"username":u}

# ===== USERS =====
@app.get("/api/users/recommend")
async def recommend(request: Request, userId: str = ""):
    user_id = require_self(request, userId or request.state.user_id)
    c = db().cursor(DictCursor)
    # Simple: get random active users excluding self
    c.execute("SELECT id,username,nickname,age,gender,location,bio,avatar,background FROM users WHERE id!=%s AND is_active=1 ORDER BY RAND() LIMIT 20", (user_id,))
    users = c.fetchall()
    c.connection.close()
    for u in users:
        u['score']=random.randint(30,95)
        u['interests']=[]
        u['photos']=[]
    return users

@app.get("/api/users/list")
async def list_users(request: Request, excludeId: str = "0"):
    exclude_id = request.state.user_id
    c = db().cursor(DictCursor)
    c.execute("SELECT id,username,nickname,age,gender,location,bio,avatar FROM users WHERE id!=%s AND is_active=1 ORDER BY id DESC LIMIT 50",(exclude_id,))
    users = c.fetchall()
    c.connection.close()
    return users

@app.get("/api/users/search")
async def search(request: Request, keyword: str = "", excludeId: str = "0"):
    exclude_id = request.state.user_id
    c = db().cursor(DictCursor)
    c.execute("SELECT id,username,nickname,age,gender,location,bio,avatar FROM users WHERE id!=%s AND is_active=1 AND (nickname LIKE %s OR username LIKE %s) LIMIT 30",(exclude_id, f"%{keyword}%", f"%{keyword}%"))
    users = c.fetchall()
    c.connection.close()
    return users

@app.get("/api/users/{uid}")
async def get_user(uid: int, request: Request):
    c = db().cursor(DictCursor)
    c.execute("SELECT id,username,nickname,age,gender,location,bio,avatar,background,email FROM users WHERE id=%s",(uid,))
    u = c.fetchone()
    c.connection.close()
    if not u: raise HTTPException(404, "用户不存在")
    if uid != request.state.user_id:
        u.pop("email", None)
    return u

@app.put("/api/users/{uid}/profile")
async def update_profile(uid: int, req: Request):
    require_self(req, uid)
    data = await req.json()
    fields = {k:v for k,v in data.items() if v is not None and k in ['nickname','age','gender','bio','location','email']}
    if not fields: raise HTTPException(400, "无更新字段")
    c = db().cursor()
    sets = ", ".join([f"{k}=%s" for k in fields])
    vals = list(fields.values()) + [uid]
    c.execute(f"UPDATE users SET {sets} WHERE id=%s", vals)
    c.connection.commit()
    c.connection.close()
    return {"ok":True}

@app.post("/api/users/{uid}/avatar")
async def upload_avatar(uid: int, request: Request, file: UploadFile = File(...)):
    require_self(request, uid)
    """上传头像"""
    avatar_url = await save_image(file, "avatars")
    c = db().cursor()
    c.execute("UPDATE users SET avatar=%s WHERE id=%s", (avatar_url, uid))
    c.connection.commit()
    c.connection.close()
    return {"avatar": avatar_url}

@app.post("/api/users/{uid}/background")
async def upload_background(uid: int, request: Request, file: UploadFile = File(...)):
    require_self(request, uid)
    """上传背景图"""
    bg_url = await save_image(file, "backgrounds")
    c = db().cursor()
    c.execute("UPDATE users SET background=%s WHERE id=%s", (bg_url, uid))
    c.connection.commit()
    c.connection.close()
    return {"background": bg_url}

@app.put("/api/users/{uid}/showOnPlanet")
async def toggle_planet(uid: int, request: Request, value: bool = True):
    require_self(request, uid)
    c = db().cursor()
    c.execute("UPDATE users SET show_on_planet=%s WHERE id=%s",(1 if value else 0, uid))
    c.connection.commit()
    c.connection.close()
    return {"showOnPlanet":value}

# ===== FRIENDS =====
@app.get("/api/friends/my/{uid}")
async def my_friends(uid: int, request: Request):
    require_self(request, uid)
    c = db().cursor(DictCursor)
    c.execute("SELECT f.id as friendship_id, u.id, u.username, u.nickname, u.age, u.gender, u.location, u.avatar FROM friendships f JOIN users u ON u.id = CASE WHEN f.user_id=%s THEN f.friend_id ELSE f.user_id END WHERE (f.user_id=%s OR f.friend_id=%s) ORDER BY f.create_time DESC LIMIT 100", (uid,uid,uid))
    friends = c.fetchall()
    c.connection.close()
    return friends

@app.get("/api/friends/requests/{uid}")
async def friend_requests(uid: int, request: Request):
    require_self(request, uid)
    c = db().cursor(DictCursor)
    c.execute("SELECT f.id as friendship_id, u.id, u.username, u.nickname, u.age, u.gender, u.location, u.avatar FROM friendships f JOIN users u ON u.id=f.user_id WHERE f.friend_id=%s",(uid,))
    reqs = c.fetchall()
    c.connection.close()
    return reqs

@app.post("/api/friends/request/{fid}")
async def send_request(fid: int, request: Request, userId: int = 0):
    user_id = require_self(request, userId)
    if fid == user_id:
        raise HTTPException(400, "不能添加自己为好友")
    c = db().cursor()
    try:
        c.execute("INSERT INTO friendships (user_id, friend_id, status, create_time) VALUES (%s,%s,'PENDING',NOW())",(user_id,fid))
        c.connection.commit()
    except Exception as e:
        c.connection.close()
        raise HTTPException(400, f"请求失败: {e}")
    c.connection.close()
    return {"ok":True}

@app.post("/api/friends/accept/{fsid}")
async def accept_request(fsid: int, request: Request, userId: int = 0):
    user_id = require_self(request, userId)
    c = db().cursor()
    c.execute("UPDATE friendships SET status='ACCEPTED' WHERE id=%s AND friend_id=%s",(fsid,user_id))
    c.connection.commit()
    c.connection.close()
    return {"ok":True}

@app.delete("/api/friends/reject/{fsid}")
async def reject_request(fsid: int, request: Request, userId: int = 0):
    user_id = require_self(request, userId)
    c = db().cursor()
    c.execute("DELETE FROM friendships WHERE id=%s AND friend_id=%s",(fsid,user_id))
    c.connection.commit()
    c.connection.close()
    return {"ok":True}

@app.delete("/api/friends/remove/{fid}")
async def remove_friend(fid: int, request: Request, userId: int = 0):
    """删除好友关系"""
    user_id = require_self(request, userId)
    c = db().cursor()
    c.execute("DELETE FROM friendships WHERE (user_id=%s AND friend_id=%s) OR (user_id=%s AND friend_id=%s)",(user_id,fid,fid,user_id))
    c.connection.commit()
    c.connection.close()
    return {"ok":True}

@app.delete("/api/messages/conversation")
async def delete_conversation(request: Request, userId: int = 0, otherUserId: int = 0):
    """删除与某人的所有聊天记录"""
    user_id = require_self(request, userId)
    c = db().cursor()
    c.execute("DELETE FROM messages WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s)",(user_id,otherUserId,otherUserId,user_id))
    c.connection.commit()
    c.connection.close()
    return {"ok":True}

# ===== MESSAGES =====
@app.get("/api/messages/conversation")
async def conversation(request: Request, userId: int = 0, otherUserId: int = 0):
    user_id = require_self(request, userId)
    c = db().cursor(DictCursor)
    c.execute("SELECT m.id, m.content, m.image_url as imageUrl, m.create_time as createTime, m.sender_id, m.receiver_id FROM messages m WHERE (m.sender_id=%s AND m.receiver_id=%s) OR (m.sender_id=%s AND m.receiver_id=%s) ORDER BY m.create_time LIMIT 100",(user_id,otherUserId,otherUserId,user_id))
    msgs = c.fetchall()
    c.connection.close()
    result = []
    for m in msgs:
        result.append({
            "id": m['id'], "content": m['content'], "imageUrl": m['imageUrl'],
            "createTime": str(m['createTime']), "sender": {"id": m['sender_id']}, "receiver": {"id": m['receiver_id']}
        })
    return result

@app.post("/api/messages")
async def send_message(req: Request):
    data = await req.json()
    sid = req.state.user_id
    rid = int(req.query_params.get("receiverId", data.get("receiverId",0)))
    content = data.get("content","")
    if not rid or rid == sid:
        raise HTTPException(400, "无效的接收者")
    if not content.strip() or len(content) > 2000:
        raise HTTPException(400, "消息内容长度无效")
    c = db().cursor()
    c.execute("INSERT INTO messages (sender_id, receiver_id, content, create_time) VALUES (%s,%s,%s,NOW())",(sid,rid,content))
    c.connection.commit()
    mid = c.lastrowid
    c.connection.close()
    return {"id":mid,"content":content,"sender":{"id":sid},"receiver":{"id":rid}}


@app.post("/api/messages/image")
async def send_image(req: Request):
    form = await req.form()
    sid = require_self(req, form.get("senderId"))
    try:
        rid = int(form.get("receiverId", 0))
    except (TypeError, ValueError):
        raise HTTPException(400, "无效的接收者")
    if not rid or rid == sid:
        raise HTTPException(400, "无效的接收者")
    file = form.get("file")
    if not file or not hasattr(file, "read"):
        raise HTTPException(400, "请选择图片")
    image_url = await save_image(file, "messages")
    c = db().cursor()
    c.execute(
        "INSERT INTO messages (sender_id, receiver_id, content, image_url, create_time) VALUES (%s,%s,%s,%s,NOW())",
        (sid, rid, "[图片]", image_url),
    )
    c.connection.commit()
    mid = c.lastrowid
    c.connection.close()
    return {
        "id": mid,
        "content": "[图片]",
        "imageUrl": image_url,
        "sender": {"id": sid},
        "receiver": {"id": rid},
    }


@app.get("/api/messages/unread/{uid}")
async def unread(uid: int, request: Request):
    require_self(request, uid)
    c = db().cursor(DictCursor)
    c.execute("SELECT m.* FROM messages m WHERE m.receiver_id=%s AND m.is_read=0",(uid,))
    msgs = c.fetchall()
    c.connection.close()
    return msgs

@app.put("/api/messages/read/{mid}")
async def mark_read(mid: int, request: Request, userId: int = 0):
    user_id = require_self(request, userId)
    c = db().cursor()
    c.execute("UPDATE messages SET is_read=1 WHERE id=%s AND receiver_id=%s",(mid,user_id))
    c.connection.commit()
    c.connection.close()
    return {"ok":True}

# ===== POSTS (忆涟) =====
@app.get("/api/posts/feed")
async def post_feed():
    c = db().cursor(DictCursor)
    c.execute("SELECT p.id,p.user_id,p.content,p.image_url,p.create_time,u.username,u.nickname,u.avatar FROM posts p LEFT JOIN users u ON p.user_id=u.id ORDER BY p.create_time DESC LIMIT 50")
    posts = c.fetchall()
    c.connection.close()
    result = []
    for p in posts:
        result.append({"id":p['id'],"userId":p['user_id'],"content":p['content'],"imageUrl":p['image_url'],"createTime":str(p['create_time']),"user":{"username":p['username'],"nickname":p['nickname'] or p['username'],"avatar":p['avatar']}})
    return result

@app.post("/api/posts")
async def create_post(req: Request):
    try:
        form = await req.form()
        uid = require_self(req, form.get("userId"))
        content = form.get("content","")
        if not content.strip() or len(content) > 5000:
            raise HTTPException(400, "内容长度无效")
        img = form.get("image")
        image_url = None
        if img and hasattr(img,'filename') and img.filename:
            image_url = await save_image(img, "posts")
        c = db().cursor()
        c.execute("INSERT INTO posts (user_id,content,image_url,create_time) VALUES (%s,%s,%s,NOW())",(uid,content,image_url))
        c.connection.commit()
        pid = c.lastrowid
        c.connection.close()
        return {"id":pid,"userId":int(uid),"content":content,"imageUrl":image_url}
    except HTTPException:
        raise
    except Exception:
        return JSONResponse({"error":"发布失败，请稍后重试"},500)

@app.delete("/api/posts/{pid}")
async def delete_post(pid: int, request: Request, userId: int = 0):
    user_id = require_self(request, userId)
    c = db().cursor()
    c.execute("DELETE FROM posts WHERE id=%s AND user_id=%s",(pid,user_id))
    c.connection.commit()
    c.connection.close()
    return {"ok":True}

@app.get("/api/posts/user/{uid}")
async def user_posts(uid: int):
    """获取某个用户的所有帖子"""
    c = db().cursor(DictCursor)
    c.execute("SELECT p.id,p.user_id,p.content,p.image_url,p.create_time,u.username,u.nickname,u.avatar FROM posts p LEFT JOIN users u ON p.user_id=u.id WHERE p.user_id=%s ORDER BY p.create_time DESC", (uid,))
    posts = c.fetchall()
    c.connection.close()
    return [{"id":p['id'],"userId":p['user_id'],"content":p['content'],"imageUrl":p['image_url'],"createTime":str(p['create_time']),"user":{"username":p['username'],"nickname":p['nickname'] or p['username'],"avatar":p['avatar']}} for p in posts]

# ===== LIKES =====
@app.get("/api/posts/{pid}/likes")
async def post_likes(pid: int, request: Request, userId: int = 0):
    user_id = require_self(request, userId)
    c = db().cursor()
    c.execute("SELECT COUNT(*) FROM post_likes WHERE post_id=%s",(pid,))
    count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM post_likes WHERE post_id=%s AND user_id=%s",(pid,user_id))
    liked = c.fetchone()[0] > 0
    c.connection.close()
    return {"count":count,"liked":liked}

@app.post("/api/posts/{pid}/like")
async def like_post(pid: int, request: Request, userId: int = 0):
    user_id = require_self(request, userId)
    c = db().cursor()
    try: c.execute("INSERT IGNORE INTO post_likes (post_id,user_id) VALUES (%s,%s)",(pid,user_id)); c.connection.commit()
    except: pass
    c.execute("SELECT COUNT(*) FROM post_likes WHERE post_id=%s",(pid,))
    count = c.fetchone()[0]
    c.connection.close()
    return {"count":count}

@app.delete("/api/posts/{pid}/like")
async def unlike_post(pid: int, request: Request, userId: int = 0):
    user_id = require_self(request, userId)
    c = db().cursor()
    c.execute("DELETE FROM post_likes WHERE post_id=%s AND user_id=%s",(pid,user_id))
    c.connection.commit()
    c.connection.close()
    return {"count":0}

# ===== COMMENTS =====
@app.get("/api/posts/{pid}/comments")
async def post_comments(pid: int):
    c = db().cursor(DictCursor)
    # Try comments table first, fallback to post_comments
    try:
        c.execute("SELECT c.id,c.content,c.user_id,c.create_time,u.nickname FROM comments c LEFT JOIN users u ON c.user_id=u.id WHERE c.post_id=%s ORDER BY c.create_time",(pid,))
    except:
        return []
    comments = c.fetchall()
    c.connection.close()
    return [{"id":c['id'],"content":c['content'],"user":{"nickname":c.get('nickname','')}} for c in comments]

@app.post("/api/posts/{pid}/comment")
async def add_comment(pid: int, req: Request):
    data = await req.json()
    uid = require_self(req, data.get("userId",0))
    content = data.get("content","").strip()
    if not content or len(content) > 1000:
        raise HTTPException(400, "评论内容长度无效")
    c = db().cursor()
    try:
        c.execute("INSERT INTO comments (post_id,user_id,content,create_time) VALUES (%s,%s,%s,NOW())",(pid,uid,content))
        c.connection.commit()
    except Exception as e:
        c.connection.close()
        # Fallback: use post_comments table
        c2 = db().cursor()
        c2.execute("INSERT INTO post_comments (post_id,user_id,content,create_time) VALUES (%s,%s,%s,NOW())",(pid,uid,content))
        c2.connection.commit()
        c2.connection.close()
        return {"ok":True}
    c.connection.close()
    return {"ok":True}

# ===== STATS =====
@app.get("/api/stats/overview")
async def stats():
    c = db().cursor()
    c.execute("SELECT COUNT(*) FROM users"); users=c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM posts"); posts=c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM friendships"); friends=c.fetchone()[0]
    c.connection.close()
    return {"users":users,"posts":posts,"friends":friends}

# ===== HEALTH =====
@app.get("/api/health")
async def health(): return {"status":"ok"}

# ===== PUBLIC STATS =====
@app.get("/api/public/stats")
async def public_stats():
    """公开统计，30秒缓存"""
    global _stats_cache
    now = time_mod.time()
    if '_stats_cache' in dir() and hasattr(public_stats, '_cache_time') and now - public_stats._cache_time < 30:
        return public_stats._cached
    c = db().cursor()
    c.execute("SELECT COUNT(*) FROM users"); users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM posts"); items = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM friendships"); friendships = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages"); messages = c.fetchone()[0]
    c2 = db().cursor(DictCursor)
    c2.execute("SELECT p.content,p.create_time,u.nickname FROM posts p LEFT JOIN users u ON p.user_id=u.id ORDER BY p.create_time DESC LIMIT 3")
    recent = []
    for r in c2.fetchall():
        try:
            d = json.loads(r['content'])
            recent.append({"name": d.get('name','物品'), "nickname": r['nickname'] or '匿名', "time": str(r['create_time'])})
        except:
            recent.append({"name": "物品", "nickname": r['nickname'] or '匿名', "time": str(r['create_time'])})
    c.connection.close(); c2.connection.close()
    result = {"users": users, "items": items, "friendships": friendships, "messages": messages, "recent": recent, "mood": random.choice(["今天想换点什么？", "每件物品都有故事", "有人正在寻找你拥有的", "交换让世界变小"])}
    public_stats._cached = result
    public_stats._cache_time = now
    return result

# ===== CONVERSATIONS (聊天列表) =====
@app.get("/api/conversations")
async def get_conversations(request: Request):
    uid = request.query_params.get("userId")
    if not uid: raise HTTPException(400, "userId required")
    uid = require_self(request, uid)
    c = db().cursor(DictCursor)
    c.execute("""
        SELECT
            CASE WHEN m.sender_id=%s THEN m.receiver_id ELSE m.sender_id END as other_id,
            COALESCE(u.nickname, u.username) as other_name,
            u.avatar as other_avatar,
            m.content as last_content,
            m.create_time as last_time,
            (SELECT COUNT(*) FROM messages m2 WHERE m2.receiver_id=%s AND m2.sender_id=(CASE WHEN m.sender_id=%s THEN m.receiver_id ELSE m.sender_id END) AND m2.is_read=0) as unread
        FROM messages m
        JOIN users u ON u.id = CASE WHEN m.sender_id=%s THEN m.receiver_id ELSE m.sender_id END
        WHERE (m.sender_id=%s OR m.receiver_id=%s)
        AND m.id IN (SELECT MAX(m3.id) FROM messages m3 WHERE m3.sender_id=%s OR m3.receiver_id=%s GROUP BY CASE WHEN m3.sender_id=%s THEN m3.receiver_id ELSE m3.sender_id END)
        ORDER BY m.create_time DESC LIMIT 50
    """, (uid, uid, uid, uid, uid, uid, uid, uid, uid))
    rows = c.fetchall()
    c.connection.close()
    result = []
    for r in rows:
        result.append({"userId": r['other_id'], "nickname": r['other_name'] or "", "avatar": r['other_avatar'] or "",
                       "lastMessage": r['last_content'] or "", "lastTime": str(r['last_time']) if r['last_time'] else "", "unread": r['unread'] or 0})
    return {"conversations": result}

# ===== ADMIN PANEL =====
ADMIN_USER = required_env("ADMIN_USER")
ADMIN_PASS = required_env("ADMIN_PASSWORD")
admin_sessions = {}

@app.post("/api/admin/login")
async def admin_login(req: Request):
    rate_limit(f"admin_login_{req.client.host}", 5, 60)
    data = await req.json()
    if data.get("username") == ADMIN_USER and data.get("password") == ADMIN_PASS:
        token = secrets.token_hex(32)
        admin_sessions[token] = dt.datetime.utcnow() + dt.timedelta(hours=24)
        resp = JSONResponse({"ok": True})
        resp.set_cookie("admin_token", token, httponly=True, secure=True, samesite="strict", max_age=86400)
        return resp
    raise HTTPException(401, "账号或密码错误")

def check_admin(request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in admin_sessions: raise HTTPException(401)
    if admin_sessions[token] < dt.datetime.utcnow(): del admin_sessions[token]; raise HTTPException(401)
    return True


@app.get("/api/admin/conversations")
async def admin_conversations(request: Request):
    """获取所有用户之间的对话列表"""
    check_admin(request)
    c = db().cursor(DictCursor)
    c.execute("""
        SELECT
            CASE WHEN m.sender_id < m.receiver_id THEN m.sender_id ELSE m.receiver_id END as uid1,
            CASE WHEN m.sender_id < m.receiver_id THEN m.receiver_id ELSE m.sender_id END as uid2,
            u1.nickname as name1, u1.username as uname1,
            u2.nickname as name2, u2.username as uname2,
            COUNT(*) as msg_count,
            MAX(m.create_time) as last_time,
            (SELECT content FROM messages WHERE (sender_id=uid1 AND receiver_id=uid2) OR (sender_id=uid2 AND receiver_id=uid1) ORDER BY create_time DESC LIMIT 1) as last_msg
        FROM messages m
        JOIN users u1 ON u1.id = CASE WHEN m.sender_id < m.receiver_id THEN m.sender_id ELSE m.receiver_id END
        JOIN users u2 ON u2.id = CASE WHEN m.sender_id < m.receiver_id THEN m.receiver_id ELSE m.sender_id END
        GROUP BY uid1, uid2
        ORDER BY last_time DESC LIMIT 100
    """)
    convs = c.fetchall()
    c.connection.close()
    result = []
    for r in convs:
        result.append({
            "uid1": r['uid1'], "uid2": r['uid2'],
            "name1": r['name1'] or r['uname1'], "name2": r['name2'] or r['uname2'],
            "msgCount": r['msg_count'], "lastTime": str(r['last_time']) if r['last_time'] else "",
            "lastMsg": r['last_msg'] or ""
        })
    return {"conversations": result}

@app.get("/api/admin/messages/{uid1}/{uid2}")
async def admin_messages(uid1: int, uid2: int, request: Request):
    """查看两个用户之间的完整对话"""
    check_admin(request)
    c = db().cursor(DictCursor)
    c.execute("SELECT m.id,m.sender_id,m.receiver_id,m.content,m.create_time,u1.nickname as sender_name,u2.nickname as receiver_name FROM messages m LEFT JOIN users u1 ON m.sender_id=u1.id LEFT JOIN users u2 ON m.receiver_id=u2.id WHERE (m.sender_id=%s AND m.receiver_id=%s) OR (m.sender_id=%s AND m.receiver_id=%s) ORDER BY m.create_time LIMIT 200", (uid1,uid2,uid2,uid1))
    msgs = c.fetchall()
    c.connection.close()
    return [{"id":m['id'],"senderId":m['sender_id'],"receiverId":m['receiver_id'],"senderName":m['sender_name'] or str(m['sender_id']),"content":m['content'],"time":str(m['create_time']) if m['create_time'] else ""} for m in msgs]

@app.get("/api/admin/stats")
async def admin_stats(request: Request):
    check_admin(request)
    c = db().cursor()
    c.execute("SELECT COUNT(*) FROM users"); users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM posts"); posts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM friendships"); friends = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages"); msgs = c.fetchone()[0]
    c.connection.close()
    return {"users":users,"posts":posts,"friends":friends,"pending_requests":0,"messages":msgs}

@app.get("/api/admin/users")
async def admin_users(request: Request, page: int = 1, keyword: str = ""):
    check_admin(request)
    c = db().cursor(DictCursor)
    offset = (page-1)*20
    if keyword:
        c.execute("SELECT COUNT(*) FROM users WHERE username LIKE %s OR nickname LIKE %s", (f"%{keyword}%", f"%{keyword}%"))
        total = c.fetchone()['COUNT(*)']
        c.execute("SELECT id,username,nickname,gender,create_time FROM users WHERE username LIKE %s OR nickname LIKE %s ORDER BY id DESC LIMIT 20 OFFSET %s", (f"%{keyword}%", f"%{keyword}%", offset))
    else:
        c.execute("SELECT COUNT(*) FROM users"); total = c.fetchone()['COUNT(*)']
        c.execute("SELECT id,username,nickname,gender,create_time FROM users ORDER BY id DESC LIMIT 20 OFFSET %s", (offset,))
    users = [{"id":r['id'],"username":r['username'],"nickname":r['nickname'],"gender":r['gender'],"created_at":str(r['create_time']) if r['create_time'] else ""} for r in c.fetchall()]
    c.connection.close()
    return {"users":users,"total":total,"page":page}

@app.delete("/api/admin/users/{uid}")
async def admin_delete_user(uid: int, request: Request):
    check_admin(request)
    c = db().cursor(); c.execute("DELETE FROM users WHERE id=%s",(uid,)); c.connection.commit(); c.connection.close()
    return {"ok":True}

@app.get("/api/admin/posts")
async def admin_posts(request: Request, page: int = 1, keyword: str = ""):
    check_admin(request)
    c = db().cursor(DictCursor)
    offset = (page-1)*20
    if keyword:
        c.execute("SELECT COUNT(*) FROM posts WHERE content LIKE %s", (f"%{keyword}%",)); total = c.fetchone()['COUNT(*)']
        c.execute("SELECT p.id,p.user_id,p.content,p.create_time,COALESCE(u.nickname,u.username) as author FROM posts p LEFT JOIN users u ON p.user_id=u.id WHERE p.content LIKE %s ORDER BY p.id DESC LIMIT 20 OFFSET %s", (f"%{keyword}%", offset))
    else:
        c.execute("SELECT COUNT(*) FROM posts"); total = c.fetchone()['COUNT(*)']
        c.execute("SELECT p.id,p.user_id,p.content,p.create_time,COALESCE(u.nickname,u.username) as author FROM posts p LEFT JOIN users u ON p.user_id=u.id ORDER BY p.id DESC LIMIT 20 OFFSET %s", (offset,))
    posts = [{"id":r['id'],"user_id":r['user_id'],"content":r['content'],"create_time":str(r['create_time']) if r['create_time'] else "","author":r['author']} for r in c.fetchall()]
    c.connection.close()
    return {"posts":posts,"total":total,"page":page}

@app.delete("/api/admin/posts/{pid}")
async def admin_delete_post(pid: int, request: Request):
    check_admin(request)
    c = db().cursor(); c.execute("DELETE FROM posts WHERE id=%s",(pid,)); c.connection.commit(); c.connection.close()
    return {"ok":True}

@app.get("/api/admin/logout")
async def admin_logout():
    resp = JSONResponse({"ok":True}); resp.delete_cookie("admin_token"); return resp

@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/", response_class=HTMLResponse)
async def admin_page():
    return HTMLResponse(ADMIN_HTML)

ADMIN_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>湛对网 - 管理后台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:#f0f5ff;min-height:100vh}
.login-box{max-width:360px;margin:100px auto;background:#fff;padding:40px;border-radius:20px;box-shadow:0 10px 40px rgba(0,0,0,0.08)}
.login-box h1{text-align:center;color:#3b82f6;font-size:24px;margin-bottom:24px}
.login-box input{width:100%;padding:14px;margin-bottom:14px;border:1.5px solid #e2e8f0;border-radius:12px;font-size:15px;outline:none}
.login-box input:focus{border-color:#3b82f6}
.login-box button{width:100%;padding:14px;background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer}
.login-box .err{color:#ef4444;text-align:center;margin-top:12px;font-size:14px}
.dash{max-width:1100px;margin:0 auto;padding:20px}
.dash h1{font-size:22px;margin-bottom:20px}
.stats{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}
.stat{background:#fff;border-radius:14px;padding:16px 20px;box-shadow:0 2px 8px rgba(0,0,0,0.04);min-width:120px}
.stat .n{font-size:28px;font-weight:800;color:#3b82f6}
.stat .l{color:#94a3b8;font-size:12px}
.tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.tabs button{padding:8px 20px;border:none;border-radius:10px;cursor:pointer;font-size:14px;font-weight:600;background:#fff;color:#64748b}
.tabs button.on{background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff}
.toolbar{margin-bottom:12px}
.toolbar input{padding:10px 14px;border:1px solid #e2e8f0;border-radius:10px;width:200px;outline:none;margin-right:8px}
.toolbar button{padding:10px 16px;background:#3b82f6;color:#fff;border:none;border-radius:10px;cursor:pointer}
table{width:100%;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.04);margin-bottom:20px}
th,td{padding:12px 16px;text-align:left;font-size:14px}
th{background:#f8fafc;color:#64748b;font-weight:600}
td{border-bottom:1px solid #f1f5f9}
.del{background:none;border:none;color:#ef4444;cursor:pointer;font-size:13px}
.view{background:none;border:none;color:#3b82f6;cursor:pointer;font-size:13px;margin-right:8px}
.logout-btn{float:right;background:none;border:1px solid #ef4444;color:#ef4444;padding:6px 16px;border-radius:8px;cursor:pointer;font-size:13px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:999}
.modal>div{background:#fff;border-radius:16px;padding:24px;max-width:600px;max-height:80vh;overflow-y:auto;width:90%}
.modal .close{float:right;background:none;border:none;font-size:20px;cursor:pointer;color:#94a3b8}
.msg-line{padding:6px 0;border-bottom:1px solid #f5f5f5;font-size:14px}
.msg-line .sender{font-weight:600;color:#3b82f6}
.msg-line .time{color:#94a3b8;font-size:12px}
.msg-content{margin-top:2px;color:#333}
</style>
</head>
<body>
<div id="loginPage" class="login-box">
  <h1>湛对网管理</h1>
  <input id="u" placeholder="账号" autofocus>
  <input id="p" type="password" placeholder="密码" onkeydown="if(event.key==='Enter')login()">
  <button onclick="login()">登录</button>
  <div id="err" class="err"></div>
</div>
<div id="dash" class="dash" style="display:none">
  <button class="logout-btn" onclick="logout()">退出</button>
  <h1>管理后台</h1>
  <div id="stats" class="stats"></div>
  <div class="tabs">
    <button id="tabUsers" class="on" onclick="switchTab('users')">👥 用户</button>
    <button id="tabItems" onclick="switchTab('items')">📦 忆涟</button>
    <button id="tabChats" onclick="switchTab('chats')">💬 对话</button>
  </div>
  <div class="toolbar">
    <input id="kw" placeholder="搜索..." onkeydown="if(event.key==='Enter')load()">
    <button onclick="load()">搜索</button>
  </div>
  <div id="content"></div>
</div>
<div id="modal" class="modal" style="display:none" onclick="if(event.target===this)this.style.display='none'">
  <div><button class="close" onclick="document.getElementById('modal').style.display='none'">✕</button><div id="modalContent"></div></div>
</div>
<script>
var tab='users';
async function api(url,opt){
  opt=opt||{};
  var r=await fetch(url,opt);
  if(r.status===401){document.getElementById('loginPage').style.display='block';document.getElementById('dash').style.display='none';throw new Error('unauth')}
  if(!r.ok){throw new Error(await r.text())}
  return r.json()
}
async function login(){
  try{
    await fetch('/api/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('u').value,password:document.getElementById('p').value})});
    document.getElementById('loginPage').style.display='none';
    document.getElementById('dash').style.display='block';
    loadStats();load();
  }catch(e){document.getElementById('err').textContent='账号或密码错误'}
}
async function loadStats(){
  var s=await api('/api/admin/stats');
  document.getElementById('stats').innerHTML='<div class=stat><div class=n>'+s.users+'</div><div class=l>用户</div></div><div class=stat><div class=n>'+s.posts+'</div><div class=l>忆涟物品</div></div><div class=stat><div class=n>'+s.friends+'</div><div class=l>好友</div></div><div class=stat><div class=n>'+s.messages+'</div><div class=l>消息</div></div>'
}
async function load(){
  var kw=document.getElementById('kw').value;
  if(tab==='users'){
    var d=await api('/api/admin/users?keyword='+kw);
    var h='<table><thead><tr><th>ID</th><th>用户名</th><th>昵称</th><th>性别</th><th>注册时间</th><th>操作</th></tr></thead><tbody>';
    d.users.forEach(function(u){h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.nickname||'-')+'</td><td>'+(u.gender||'-')+'</td><td>'+(u.created_at||'').split(' ')[0]+'</td><td><button class=del onclick=delUser('+u.id+')>删除</button></td></tr>'});
    h+='</tbody></table>';document.getElementById('content').innerHTML=h
  }else if(tab==='items'){
    var d=await api('/api/admin/posts?keyword='+kw);
    var h='<table><thead><tr><th>ID</th><th>发布者</th><th>物品信息</th><th>时间</th><th>操作</th></tr></thead><tbody>';
    d.posts.forEach(function(p){
      var info=''; try{var j=JSON.parse(p.content);info='<b>'+j.name+'</b><br>'+j.story.slice(0,60)+(j.story.length>60?'...':'')+'<br><small>'+j.category+' | '+j.want+' | '+j.location+'</small>'}catch(e){info=(p.content||'').slice(0,100)}
      h+='<tr><td>'+p.id+'</td><td>'+(p.author||'-')+'</td><td style=max-width:350px;font-size:13px>'+info+'</td><td>'+(p.create_time||'').split('T')[0]+'</td><td><button class=del onclick=delPost('+p.id+')>删除</button></td></tr>'
    });
    h+='</tbody></table>';document.getElementById('content').innerHTML=h
  }else if(tab==='chats'){
    var d=await api('/api/admin/conversations');
    var h='<table><thead><tr><th>用户A</th><th>用户B</th><th>消息数</th><th>最后消息</th><th>时间</th><th>操作</th></tr></thead><tbody>';
    d.conversations.forEach(function(c){
      h+='<tr><td>'+c.name1+'</td><td>'+c.name2+'</td><td>'+c.msgCount+'</td><td style=max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap>'+(c.lastMsg||'')+'</td><td>'+(c.lastTime||'').split('T')[0]+'</td><td><button class=view onclick=viewChat('+c.uid1+','+c.uid2+')>查看</button></td></tr>'
    });
    h+='</tbody></table>';document.getElementById('content').innerHTML=h
  }
}
function switchTab(t){tab=t;document.getElementById('tabUsers').className=t==='users'?'on':'';document.getElementById('tabItems').className=t==='items'?'on':'';document.getElementById('tabChats').className=t==='chats'?'on':'';load()}
async function delUser(id){if(confirm('删除用户#'+id+'?')){await api('/api/admin/users/'+id,{method:'DELETE'});loadStats();load()}}
async function delPost(id){if(confirm('删除物品#'+id+'?')){await api('/api/admin/posts/'+id,{method:'DELETE'});loadStats();load()}}
async function viewChat(uid1,uid2){
  document.getElementById('modal').style.display='flex';
  document.getElementById('modalContent').innerHTML='加载中...';
  var msgs=await api('/api/admin/messages/'+uid1+'/'+uid2);
  var h='<h3>对话记录</h3>';
  msgs.forEach(function(m){h+='<div class=msg-line><span class=sender>'+m.senderName+'</span> <span class=time>'+m.time+'</span><div class=msg-content>'+m.content+'</div></div>'});
  if(msgs.length===0)h+='<p style=color:#94a3b8>暂无消息</p>';
  document.getElementById('modalContent').innerHTML=h
}
async function logout(){await fetch('/api/admin/logout');location.reload()}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
