# Phase 3 --- Auth Frontend Specification

## Objective

Implement a secure authentication layer for the React + TypeScript
frontend.

## Login

Build a login page using:

-   React Hook Form
-   Zod

Fields:

-   Username or Email
-   Password

Features:

-   Client-side validation
-   Loading state
-   Authentication error handling
-   Redirect to dashboard after login

## Token Storage

-   Store JWT access token in memory.
-   Store refresh token using an HTTP-only cookie (preferred).
-   Never store tokens in localStorage.

## Axios Interceptors

### Request

-   Attach JWT access token automatically.

### Response

On HTTP 401:

1.  Call `POST /auth/refresh`
2.  Retry the failed request.
3.  If refresh fails:
    -   Clear auth state.
    -   Redirect to `/login`.

Exclude the `/login` route from redirect logic to prevent redirect
loops.

## Protected Routes

Create a reusable protected route component.

Requirements:

-   Authenticated users only.
-   Redirect unauthenticated users to `/login`.
-   Preserve requested URL for post-login redirect.

## Session Timeout

-   Detect expired access tokens.
-   Refresh automatically.
-   If refresh fails:
    -   End the session.
    -   Redirect to `/login`.
    -   Optionally notify the user.

## Security

-   Use HTTP-only refresh cookies.
-   Keep JWT access token in memory.
-   Prevent infinite refresh attempts.
-   Prevent redirect loops.

## Testing

Verify:

-   Login
-   Invalid credentials
-   Token refresh
-   Protected routes
-   Session timeout
-   Logout
-   Redirect loop prevention

## Acceptance Criteria

-   Login works correctly.
-   JWT is attached automatically.
-   Tokens refresh transparently.
-   Failed refresh redirects to `/login`.
-   Protected routes require authentication.
-   Session timeout is handled gracefully.
