# Running AnythingLLM for Free Using Your ChatGPT Plus Account

## The Goal

[AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) is an open-source AI chat app you can run on your own computer. It supports documents, web search, agents, and more. Normally you connect it to OpenAI using an API key — which costs money per request.

This post walks through how we connected AnythingLLM to OpenAI using a **ChatGPT OAuth token** (the same login you use on chatgpt.com), so your ChatGPT Plus subscription covers the cost instead.

The trick came from studying how [opencode](https://github.com/sst/opencode) — an AI coding tool — does the same thing internally.

---

## Step 1: Install AnythingLLM with Docker

[Docker](https://www.docker.com/) lets you run apps in isolated containers without installing dependencies manually.

```bash
# Pull the image
docker pull mintplexlabs/anythingllm

# Run it with local storage
export STORAGE_LOCATION=$HOME/anythingllm
mkdir -p $STORAGE_LOCATION && touch "$STORAGE_LOCATION/.env"

docker run -d -p 3001:3001 \
  --cap-add SYS_ADMIN \
  -v ${STORAGE_LOCATION}:/app/server/storage \
  -v ${STORAGE_LOCATION}/.env:/app/server/.env \
  -e STORAGE_DIR="/app/server/storage" \
  --name anythingllm \
  mintplexlabs/anythingllm
```

AnythingLLM is now running at `http://localhost:3001`.

---

## Step 2: Understand the OAuth Token

[opencode](https://github.com/sst/opencode) stores its credentials in `~/.local/share/opencode/auth.json`. After logging into OpenAI through opencode, the file looks like this:

```json
{
  "openai": {
    "type": "oauth",
    "access": "<JWT token>",
    "refresh": "<refresh token>",
    "expires": 1781939072952,
    "accountId": "..."
  }
}
```

The `access` field is a short-lived JWT (JSON Web Token) issued by `https://auth.openai.com`. It is valid for use as a `Bearer` token when calling OpenAI's API — the same credential your browser uses when you chat on chatgpt.com.

---

## Step 3: Why You Can't Just Use the Token Directly

When you paste this token as the OpenAI API key in AnythingLLM, you get:

```
401 Missing scopes: api.responses.write
```

This happens because the token only has scopes for the **ChatGPT web app** (`openid`, `profile`, `email`, `offline_access`). The official OpenAI API (`api.openai.com`) requires a separate scope called `api.responses.write` that only developer API keys have.

---

## Step 4: How opencode Solves This

By reading the [opencode source code](https://github.com/sst/opencode), we found that it never calls `api.openai.com` at all. Instead, it routes every request to:

```
https://chatgpt.com/backend-api/codex/responses
```

This is the same backend endpoint the ChatGPT web app uses. It accepts the OAuth token and has no scope restrictions. opencode rewrites the URL using a custom `fetch` interceptor before the request leaves the process.

Key things opencode does:
1. Uses a dummy API key (`opencode-oauth-dummy-key`) so the SDK doesn't reject a missing key
2. Strips the SDK's auto-generated `Authorization` header
3. Injects the real OAuth token as `Authorization: Bearer <access>`
4. Adds `ChatGPT-Account-Id` header
5. Rewrites the URL to `chatgpt.com/backend-api/codex/responses`

---

## Step 5: Build a Local Proxy

Since we can't modify AnythingLLM's internals easily, we built a small Node.js proxy server (`proxy.js`) that sits between AnythingLLM and OpenAI.

```
AnythingLLM → localhost:11435 (proxy) → chatgpt.com/backend-api/codex/responses
```

The proxy handles several format differences between the OpenAI API and the ChatGPT backend:

| Problem | Fix |
|---|---|
| ChatGPT endpoint requires `instructions` (system prompt as separate field) | Extract `system` messages from `messages[]` → `instructions` field |
| ChatGPT endpoint only accepts streaming | Force `stream: true`, collect chunks for non-streaming clients |
| ChatGPT endpoint requires `store: false` | Always add it |
| Unsupported models like `gpt-4o` | Remap to `gpt-5.4` automatically |
| Agent mode sends Responses API format directly | Pass response events through as-is (no conversion) |

The proxy also handles **automatic token refresh** — when the access token expires it uses the refresh token to get a new one from `https://auth.openai.com/oauth/token`.

---

## Step 6: Configure AnythingLLM

We pointed AnythingLLM at the proxy using the OpenAI SDK's built-in environment variable `OPENAI_BASE_URL`. This redirects **all** OpenAI SDK calls — including the agent mode — without touching any code inside the container.

The `~/anythingllm/.env` file:

```env
LLM_PROVIDER=openai
OPEN_AI_KEY=opencode-oauth-dummy-key
OPEN_MODEL_PREF=gpt-5.4
OPENAI_API_KEY=opencode-oauth-dummy-key
OPENAI_BASE_URL=http://host.docker.internal:11435/v1
EMBEDDING_ENGINE=native
```

A setup script (`setup-openai-auth.js`) reads `auth.json`, checks the token expiry, and writes this config automatically.

---

## The Result

AnythingLLM now runs fully using your ChatGPT Plus account:

- **Regular chat** works via `/v1/chat/completions` → proxy → chatgpt.com
- **Agent mode** works via `/v1/responses` → proxy → chatgpt.com (with tool use, web scraping, etc.)
- **Embeddings** use the built-in local model (no API cost)
- **Token refresh** is automatic

### Final Architecture

```
[Browser]
    ↓
[AnythingLLM :3001]  ←  ~/anythingllm/.env
    ↓ OpenAI SDK (OPENAI_BASE_URL)
[Local Proxy :11435]
    ↓ Bearer <OAuth JWT>
[chatgpt.com/backend-api/codex/responses]
    ↓
[GPT-5.4 / GPT-5.4-mini]
```

---

## References

- [AnythingLLM GitHub](https://github.com/Mintplex-Labs/anything-llm)
- [opencode GitHub](https://github.com/sst/opencode)
- [opencode codex plugin source](https://github.com/sst/opencode/blob/main/packages/opencode/src/plugin/openai/codex.ts)
- [OpenAI Responses API docs](https://platform.openai.com/docs/api-reference/responses)
- [OpenAI Node SDK — OPENAI_BASE_URL](https://github.com/openai/openai-node#baseurl)
- [Docker — AnythingLLM setup guide](https://github.com/Mintplex-Labs/anything-llm/blob/master/docker/HOW_TO_USE_DOCKER.md)
