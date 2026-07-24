# Feature: Implement User Registration API

## Objective

Implement a **User Registration** REST API based on the project architecture and conventions described in `AGENTS.md`.

The registration functionality must integrate with the **existing user management system** (SQLModel, Repository, Service, Dependency Injection, Authentication), while preserving all existing authentication functionality.

---

## API Routing Requirements

All authentication-related APIs, including **User Registration**, must remain under the existing authentication base path:

```
/api/auth
```

The registration endpoint must be:

```
POST /api/auth/register
```

Do **not** create a separate `/api/users` route.

---

## Swagger Documentation

Keep all authentication endpoints grouped under a dedicated Swagger tag named:

```
Auth
```

Do **not** place any authentication endpoint under the default Swagger group.

The following endpoints should all appear under the **Auth** section:

```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/profile
```

---

## Architecture

Follow the existing project architecture described in `AGENTS.md`.

```
Route
    ↓
Service
    ↓
Repository
    ↓
SQLModel
```

Reuse the existing:

- SQLModel models
- Repository pattern
- Service layer
- Dependency Injection
- Authentication framework
- Password hashing utilities
- JWT implementation

Do not bypass the Service or Repository layers.

---

## Registration Workflow

The registration process must:

1. Validate the request.
2. Verify that the username is unique.
3. Verify that the email (if provided) is unique.
4. Validate that `password` and `confirm_password` match.
5. Hash the password using the existing security utilities.
6. Create the user through the existing `UserRepository`.
7. Persist the user to the database.
8. Return a successful response without exposing the password hash.

---

## Request Model

Create a dedicated request schema.

Example:

```python
RegisterUserRequest
```

Suggested fields:

- username
- password
- confirm_password
- full_name
- email
- role (optional)

---

## Response Model

Create a dedicated response schema.

Example:

```json
{
  "success": true,
  "message": "User registered successfully.",
  "data": {
    "id": 1,
    "username": "admin",
    "full_name": "System Administrator",
    "email": "admin@example.com",
    "role": "User",
    "is_active": true,
    "created_at": "..."
  }
}
```

Never expose:

- password
- password_hash

---

## Repository Layer

Reuse and extend the existing `UserRepository` where necessary.

Typical methods include:

- create_user()
- get_by_username()
- get_by_email()

Avoid duplicating existing repository functionality.

---

## Service Layer

Implement the registration business logic using the existing authentication architecture.

Responsibilities include:

- request validation
- duplicate checks
- password hashing
- user creation
- exception handling

Business logic must remain in the service layer.

---

## Routing

Keep all authentication-related endpoints within the existing authentication router.

Authentication endpoints should be:

```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/profile
```

Ensure the router is tagged as:

```python
tags=["Auth"]
```

so that Swagger groups these endpoints under **Auth** instead of the default section.

---

## Error Handling

Return appropriate HTTP status codes.

- **201 Created** — User registered successfully
- **400 Bad Request** — Validation error
- **401 Unauthorized** — Authentication failure (existing behavior)
- **409 Conflict** — Username or email already exists
- **500 Internal Server Error** — Unexpected server error

Follow the existing API response conventions.

---

## Security

- Never store plaintext passwords.
- Always hash passwords using the existing password hashing utility.
- Never return password hashes.
- Reuse the existing JWT and authentication infrastructure.

---

## Testing

Add unit tests for:

- successful registration
- duplicate username
- duplicate email
- password mismatch
- invalid request payload
- password hashing
- repository interaction
- endpoint responses

Follow the existing testing approach using fake repositories, dependency overrides, and FastAPI `TestClient`.

---

## Acceptance Criteria

- Implement `POST /api/auth/register`.
- Keep all authentication APIs under `/api/auth`.
- Group all authentication endpoints under the **Auth** Swagger tag.
- Do not create a separate `/api/users` router.
- Existing authentication endpoints must continue to function without modification.
- Passwords must be securely hashed before persistence.
- Duplicate usernames and emails must be rejected.
- No password or password hash should be returned in any API response.
- Follow the existing Repository → Service → Route architecture and coding conventions defined in `AGENTS.md`.