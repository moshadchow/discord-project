# Phase 0 --- Foundations

## Objective

Set up the frontend foundation for the Discord Issue Management Admin
Portal using a modern React + TypeScript stack. Establish a scalable
project structure, development tooling, and core dependencies before
implementing business features.

## Technology Stack

-   React 18
-   TypeScript
-   Vite

## Core Dependencies

-   react-router
-   @tanstack/react-query
-   axios
-   tailwindcss
-   react-hook-form
-   zod
-   dayjs
-   @heroicons/react

## Development Tooling

Configure:

-   ESLint
-   Prettier

Requirements:

-   Enforce consistent coding standards.
-   Automatically format code.
-   Integrate ESLint with TypeScript.
-   Provide scripts for linting and formatting.

## Environment Configuration

Create a `.env` file.

Example:

``` env
VITE_API_BASE_URL=http://localhost:8000/api
```

All API calls must use this base URL.

## Project Structure

``` text
src/
├── api/
├── components/
├── hooks/
├── lib/
├── pages/
└── types/
```

### Responsibilities

-   api: API services and Axios client
-   components: Reusable UI components
-   hooks: Custom React hooks
-   lib: Utilities and helpers
-   pages: Route pages
-   types: Shared TypeScript models

## Acceptance Criteria

-   Vite + React 18 + TypeScript project created.
-   All required packages installed.
-   Tailwind CSS configured.
-   ESLint and Prettier configured.
-   `.env` created for API base URL.
-   Folder structure implemented.
-   Development server starts successfully.
