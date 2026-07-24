## Swagger Documentation

Organize the API documentation using dedicated Swagger tags.

### Authentication APIs

Keep all authentication endpoints under the **Auth** tag.

```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/profile
```

These endpoints must be grouped under:

```python
tags=["Auth"]
```

---

### Issue Management APIs

Keep all issue-related endpoints under the **Messages** tag.

```
GET    /api/issues/message/{discord_message_id}
GET    /api/issues/channel/{channel_id}
GET    /api/issues/sender/{sender}
POST   /api/issues/reply
DELETE /api/issues/message/{discord_message_id}
```

These endpoints must be grouped under:

```python
tags=["Messages"]
```

Do **not** allow either the authentication or issue endpoints to appear under the default Swagger section.

---

## Acceptance Criteria

- All `/api/auth/*` endpoints are grouped under the **Auth** Swagger tag.
- All `/api/issues/*` endpoints are grouped under the **Messages** Swagger tag.
- No API endpoint appears under the default Swagger group.
- Existing endpoint URLs remain unchanged.