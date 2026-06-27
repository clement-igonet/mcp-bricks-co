# Docker Compose + Apple Container + Sockatiner

> Setup guide for running `docker compose up` with Apple's native `container` CLI on macOS (Apple Silicon)

---

## Architecture

```
docker compose up
      │
      │  (Mach IPC — no Unix socket needed)
      ▼
Homebrew docker-compose v5.2.0  ──►  com.apple.container.apiserver  (Mach service)
                                              │
                                              ▼
                                   Apple container runtime
                                   (vfkit + kata-containers kernel)
                                        │          │
                                   container1   container2 …

── Sockatiner (optional) ───────────────────────────────────────────────────────
If you need classic DOCKER_HOST socket for other tools (Portainer, k9s, etc.):

      docker CLI / third-party tool
            │
            │  unix:///var/run/docker.sock  (or DOCKER_HOST)
            ▼
      socktainer container  ──►  Apple container Mach IPC  ──►  containers
```

---

## Prerequisites

| Tool | Install | Purpose |
|---|---|---|
| Apple `container` CLI | `brew install container` | Native macOS container runtime (WWDC 2025) |
| `docker-compose` (Homebrew) | `brew install docker-compose` | Compose with Apple container backend (v5.2.0+) |
| `docker` CLI (optional) | `brew install docker` | Docker CLI without Docker Desktop |

> **Not required:** Docker Desktop. Apple's `container` CLI replaces it on Apple Silicon.

---

## Step-by-step setup

### 1 — Install and start Apple's container runtime

```bash
brew install container
container system start
container system status      # must show: status = running
```

### 2 — Install Docker Compose with Apple container backend

```bash
brew install docker-compose

# Wire it into the Docker CLI plugin directory
mkdir -p ~/.docker/cli-plugins
ln -sf /opt/homebrew/opt/docker-compose/bin/docker-compose \
       ~/.docker/cli-plugins/docker-compose

docker compose version       # → Docker Compose version 5.2.0
```

### 3 — Build the image

Apple's container CLI uses its own build service (BuildKit shim):

```bash
cd /Users/clement_igonet/project/bricks.co

# Build with Apple container builder (arm64 native, Rosetta available)
container build -t mcp-bricks-co:latest ./mcp-bricks

# Verify
container image ls | grep mcp-bricks-co
```

### 4 — Run with Docker Compose (Apple container backend)

Docker Compose 5.2.0 from Homebrew talks to Apple's `container-apiserver` via
Mach IPC automatically — **no `DOCKER_HOST` override needed**.

```bash
cd /Users/clement_igonet/project/bricks.co
docker compose up -d
```

Check running containers via **either** tool:

```bash
container ls                       # Apple container CLI view
docker compose ps                  # Compose view (via Apple backend)
```

---

## Current docker-compose.yml

```yaml
services:
  mcp-bricks:
    build:
      context: ./mcp-bricks
      dockerfile: Dockerfile
    image: mcp-bricks-co:latest
    container_name: mcp-bricks-co
    stdin_open: true
    volumes:
      - bricks_session:/data
    environment:
      - COOKIE_FILE=/data/session.json

volumes:
  bricks_session:
```

---

## Sockatiner — Docker socket proxy (optional)

Use this if you need a classic `/var/run/docker.sock` for tools that don't yet
support the Apple container Mach IPC backend (Portainer, Watchtower, CI agents, etc.).

### How it works

The sockatiner is a container that:
1. Receives Docker API calls over a Unix socket
2. Forwards them to Apple's `container-apiserver` via Mach IPC
3. Returns Docker-compatible responses

### docker-compose.yml with sockatiner

```yaml
services:
  sockatiner:
    image: ghcr.io/apple/container-builder-shim/builder:0.12.0
    container_name: sockatiner
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock    # exposes socket to host
    environment:
      - CONTAINER_APP_ROOT=/Library/Application Support/com.apple.container

  mcp-bricks:
    build:
      context: ./mcp-bricks
      dockerfile: Dockerfile
    image: mcp-bricks-co:latest
    container_name: mcp-bricks-co
    stdin_open: true
    depends_on:
      - sockatiner
    volumes:
      - bricks_session:/data
    environment:
      - COOKIE_FILE=/data/session.json

volumes:
  bricks_session:
```

### Point Docker CLI to the sockatiner socket

```bash
export DOCKER_HOST=unix:///var/run/docker.sock
# OR add a Docker context:
docker context create apple-container \
  --docker "host=unix:///var/run/docker.sock"
docker context use apple-container
```

---

## Cheat sheet

```bash
# Start Apple container runtime
container system start

# Build image
container build -t mcp-bricks-co:latest ./mcp-bricks

# Compose up (native, no DOCKER_HOST needed)
docker compose up -d

# Logs
docker compose logs -f mcp-bricks

# Stop
docker compose down

# List containers (Apple native view)
container ls

# Inspect a container
container inspect mcp-bricks-co

# Volume data
container exec mcp-bricks-co cat /data/session.json

# Restart after code change
docker compose build mcp-bricks && docker compose up -d --no-deps mcp-bricks
```

---

## Differences vs Docker Desktop

| Feature | Docker Desktop | Apple `container` CLI |
|---|---|---|
| Platform | macOS (x86 + ARM via Rosetta) | Apple Silicon native (arm64) |
| Networking | NAT / host.docker.internal | vmnet (192.168.64.x) |
| Docker socket | `~/.docker/run/docker.sock` | Mach IPC (no Unix socket by default) |
| Compose | Plugin for Docker CLI | Homebrew docker-compose v5.2.0+ |
| Volumes | Docker VM | Direct virtio-fs mount |
| Kernel | Alpine / moby | kata-containers (vmlinux 6.18) |
| Rosetta | ✅ (x86 images) | ✅ via `build.rosetta = true` |
| Resource usage | Heavy (full VM) | Lightweight (per-container VM) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `container system status` shows stopped | `container system start` |
| `docker compose` ignores Apple container | Check Homebrew docker-compose is linked in `~/.docker/cli-plugins/` |
| Container not visible in `docker ps` | Docker Desktop context is active → `docker context use apple-container` |
| Build fails | `container system logs` — check BuildKit shim |
| Volume data lost after `docker compose down` | Use named volumes (already done in this project's compose file) |
| MCP server unreachable from Claude | Use `uv run` on host (bypasses Cloudflare IP restriction inside container VM) |

---

*Tested: macOS 25.5.0 · Apple Silicon (arm64) · container CLI v1.0.0 · docker-compose v5.2.0*
