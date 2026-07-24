# Refactor Specification: Eliminate Duplicate Discord Logic

## Objective

Refactor the FastAPI implementation so that **all Discord operations are performed exclusively through the MCP tools**.

The FastAPI application must **never communicate directly with Discord.py**.

This eliminates duplicate implementations, ensures consistent behavior, and guarantees that all Discord operations (reply, send, delete, reactions, etc.) are handled by a single layer.

---

# Current Problem

Currently there are two independent Discord implementations.

## Implementation #1 (Correct)

```
FastAPI
      │
      ▼
MCP Tool
      │
      ▼
Discord.py
```

Located in:

```
src/discord_mcp/server.py
```

Contains:

- send_message
- reply_message
- moderate_message
- add_reaction
- remove_reaction
- etc.

This is the correct implementation.

---

## Implementation #2 (Incorrect)

```
FastAPI
      │
      ▼
IssueQueryService
      │
      ▼
Discord.py
```

Located in:

```
api/service.py
```

Examples:

```python
channel.send(...)

channel.fetch_message(...)

message.delete(...)
```

This duplicates the MCP implementation.

---

# Target Architecture

There must be only ONE Discord implementation.

```
               FastAPI REST API
                      │
                      ▼
              IssueQueryService
                      │
                      ▼
             DiscordGateway
                      │
                      ▼
               MCP Client
                      │
                      ▼
               MCP Server
                      │
                      ▼
              Discord.py Bot
                      │
                      ▼
                 Discord API
```

Discord.py should never be imported or used inside the FastAPI business layer.

---

# Create Discord Gateway

Create

```
api/discord_gateway.py
```

Purpose:

Provide a clean abstraction for invoking MCP tools.

Example methods:

```python
class DiscordGateway:

    async def send_message(...)

    async def reply_message(...)

    async def delete_message(...)

    async def add_reaction(...)

    async def remove_reaction(...)
```

The gateway is responsible only for communicating with the MCP server.

No business logic.

No SQLModel.

No FastAPI.

---

# Dependency Injection

Create:

```
get_discord_gateway()
```

Inject it into services.

Never inject Discord.py client.

Remove:

```
get_discord_client()
```

---

# Service Layer

Update

```
IssueQueryService
```

Remove every occurrence of

```python
client.fetch_channel()

channel.send()

channel.fetch_message()

message.reply()

message.delete()

message.add_reaction()

message.remove_reaction()
```

The service layer should instead call

```python
discord_gateway.reply_message(...)
```

or

```python
discord_gateway.delete_message(...)
```

etc.

The service layer must contain only business logic.

---

# Reply Flow

Current

```
Issue Service

↓

channel.send()

↓

Insert DB
```

Replace with

```
Issue Service

↓

discord_gateway.reply_message()

↓

Receive MCP response

↓

Insert DB
```

The inserted database record should use

```
reply_response.message_id
reply_response.timestamp
```

returned by the MCP tool.

---

# Delete Flow

Current

```
Issue Service

↓

message.delete()

↓

Delete DB
```

Replace with

```
Issue Service

↓

discord_gateway.delete_message()

↓

Delete DB
```

The service should never call Discord.py directly.

---

# Error Handling

The Discord Gateway converts MCP failures into Python exceptions.

Example

```python
DiscordGatewayException

DiscordPermissionException

DiscordMessageNotFoundException

DiscordChannelNotFoundException
```

The service layer handles these exceptions.

---

# MCP Response Models

Create

```
api/mcp_models.py
```

Examples

```python
ReplyMessageResult

DeleteMessageResult

SendMessageResult

ReactionResult
```

Avoid parsing raw JSON inside business logic.

---

# Remove Direct Discord Imports

After refactoring,

the following modules must NOT import

```python
discord
discord.ext.commands
```

- api/service.py
- api/routes.py
- api/repository.py

Discord should only exist inside

```
server.py
```

and the Discord Gateway.

---

# Database Persistence

The service layer is responsible for persistence only.

Workflow

```
Reply Message

↓

Gateway.reply_message()

↓

Receive reply result

↓

Create SQLModel object

↓

Insert into database
```

Delete

```
Gateway.delete_message()

↓

Delete SQL row
```

---

# Logging

Gateway

- MCP request
- MCP response
- MCP failures

Service

- Business events
- Database events

Repository

- SQL events

No duplicated logging.

---

# Testing

Gateway

Mock MCP responses.

Service

Mock Gateway.

Repository

Mock SQLModel session.

No service test should mock Discord.py.

No repository test should know Discord exists.

---

# Acceptance Criteria

✅ FastAPI no longer imports Discord.py.

✅ All Discord operations are routed through MCP tools.

✅ Only `server.py` communicates with Discord.py.

✅ `reply_message` creates a native Discord reply.

✅ `moderate_message` performs all Discord deletions.

✅ Service layer contains business logic only.

✅ No duplicate Discord implementation exists.

✅ Database records are created only after successful MCP operations.

✅ Database records are deleted only after successful MCP operations.

✅ Single source of truth for Discord integration.

---

# Refactoring Deliverables

Create

```
api/
    discord_gateway.py
    mcp_models.py
```

Modify

```
api/
    service.py
    deps.py
    routes.py
```

No changes should be required to the repository layer.

The final architecture must enforce a strict separation of concerns where Discord operations are centralized in the MCP server, and the FastAPI application communicates with Discord exclusively through the MCP Gateway.