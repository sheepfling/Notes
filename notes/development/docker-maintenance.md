# Docker maintenance and local reverse-proxy notes

> Type: reference  
> Status: needs-review  
> Updated: 2026-08-01

The old notes were a record of keeping a local Docker environment usable. The durable lessons
are about identifying resources before deleting them, using Compose service names for container
networking, and treating path-prefix proxying as an application concern rather than a text-rewrite
trick.

## Inspect before pruning

Start with disk and object usage:

```bash
docker system df
docker ps -a
docker image ls
docker volume ls
docker network ls
```

For a Compose project, stop or recreate only that project first:

```bash
docker compose ps
docker compose down
docker compose up -d
```

`docker compose down` removes the project’s containers and network but does not remove named
volumes unless `--volumes` is supplied. Be especially cautious with database, GitLab, runner,
and cache volumes.

Use targeted cleanup commands only after reviewing their scope:

```bash
docker container prune
docker image prune
docker builder prune
```

Avoid `docker system prune -a --volumes` as a routine fix. It can remove stopped containers,
unused images, build cache, and volumes that are not currently attached but still contain data.
If a stateful service is involved, make and test a backup first.

## Connect services on a user-defined network

Create a dedicated network when independently managed containers need to communicate:

```bash
docker network create local-services
docker network connect local-services backend
docker network connect local-services reverse-proxy
```

Inspect the result with `docker network inspect local-services`. Inside the network, use the
container or Compose service name as the hostname. Container IP addresses are ephemeral and
should not be copied into configuration.

## Reverse proxy through a path prefix

An Nginx location can forward a prefix to an upstream service:

```nginx
location /app/ {
    proxy_pass http://backend:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

The trailing slash on `proxy_pass` changes how the matching location prefix is replaced. Test
both `/app/` and deeper paths, redirects, WebSocket connections, and static assets. Prefer
configuring the application with a base path or public URL when it supports one. Nginx
`sub_filter` can patch root-relative HTML or CSS references, but it is fragile for compressed,
JSON, JavaScript-generated, or absolute URLs and should be a last resort.

## BuildKit reminder

Modern Docker installations generally use BuildKit through `docker buildx` and Compose. If a
legacy builder warning appears, inspect the installed Docker version and buildx availability:

```bash
docker version
docker buildx version
```

Prefer an explicit, reproducible build command and pinned base images. Do not copy an old daemon
configuration change into a production host without checking the current Docker documentation.

## Recovery checklist

- Record which object or volume is consuming space before deleting anything.
- Export or snapshot stateful data before pruning.
- Restart only the affected Compose project first.
- Recheck health, logs, networks, and published ports after recreation.
- Keep destructive cleanup commands out of unattended timers.
