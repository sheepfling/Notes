# GitLab CE in Docker Desktop on macOS

> Type: how-to  
> Status: historical  
> Updated: 2026-08-01

> Reconstructed from exploratory notes and refreshed on 2026-08-01.
>
> This guide is for a small, local development instance on one Mac. It is not
> a production or internet-facing deployment.

## What the old notes contained

The source note mixed two independent experiments:

1. **Gitea** with `gitea/act_runner`.
2. **GitLab CE** with `gitlab/gitlab-runner`.

The GitLab experiment eventually used:

- GitLab CE `17.4.5-ce.0`.
- Persistent data below `~/srv/gitlab/`.
- Host ports `7920` for HTTP, `7921` for an attempted HTTPS mapping, and
  `7922` for SSH.
- A separate runner configuration below `~/srv/gitlab-runner/config`.
- `host.docker.internal` while testing communication from a container back to
  a service published by Docker Desktop.

The raw note also contained plaintext passwords and several access and runner
tokens. They are intentionally absent from this cleaned guide.

## Security cleanup required

Assume every credential copied into the old note is compromised. Revoke or
rotate all the following before reusing the installation:

- GitLab personal access token.
- GitLab runner authentication token.
- GitLab initial `root` password and any reused account password.
- Gitea personal access token.
- Gitea runner registration token.
- Any password reused on another service.

Do not store replacement credentials in this repository, shell history,
Compose files, or general notes. Store them in a password manager. GitLab
runner authentication tokens are written to the runner's persistent
`config.toml`; protect that directory accordingly.

## First decide: recover or rebuild

### Recover an old installation

Do **not** delete `~/srv/gitlab` until its contents have been inspected and
backed up.

```bash
docker ps -a --filter name=gitlab
docker inspect gitlab 2>/dev/null || true

ls -la ~/srv/gitlab
du -sh ~/srv/gitlab/* 2>/dev/null || true

docker logs --tail 200 gitlab 2>/dev/null || true
```

Create an offline copy before experimenting:

```bash
mkdir -p ~/Backups
tar -C ~/srv -czf \
  "$HOME/Backups/gitlab-host-data-$(date +%Y%m%d-%H%M%S).tar.gz" \
  gitlab gitlab-runner
```

If the data was last used by GitLab `17.4.5-ce.0`, start it with that exact
version first. Do **not** point the old volumes directly at a current GitLab
image. GitLab upgrades require ordered upgrade stops and completion of
background migrations between stops.

### Build a disposable fresh instance

Use the supporting files in this collection:

- [`compose.yaml`](compose.yaml)
- [`.env.example`](.env.example)
- [`.gitlab-ci.yml`](.gitlab-ci.yml)

The versions are pinned to GitLab CE and GitLab Runner `19.2.1`, which were
current patch images when this note was refreshed. Recheck the official image
tags before a later installation.

## Fresh installation

### 1. Prerequisites

Install and start Docker Desktop. Allocate enough memory and disk space for
GitLab, its embedded PostgreSQL/Redis services, repository data, and CI job
images.

Create local storage:

```bash
mkdir -p ~/srv/gitlab/{config,logs,data}
mkdir -p ~/srv/gitlab-runner/config
```

GitLab should have a hostname rather than `localhost`. Add a loopback-only
development hostname:

```bash
echo "127.0.0.1 gitlab.test" | sudo tee -a /etc/hosts
```

Avoid adding the line twice:

```bash
grep -nE '(^|[[:space:]])gitlab\.test([[:space:]]|$)' /etc/hosts
```

### 2. Configure the packet

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and replace `/Users/REPLACE_ME` with the absolute path to your home
directory:

```bash
printf '%s\n' "$HOME"
```

Compose does not reliably expand `~` inside an environment-file value, so use
an absolute path.

### 3. Validate and start GitLab

```bash
docker compose config
docker compose pull gitlab
docker compose up -d gitlab

docker compose ps
docker compose logs -f gitlab
```

The first boot can spend substantial time configuring GitLab. A temporary
`502` while Puma and the other embedded services start does not by itself mean
the installation failed.

Open:

```text
http://gitlab.test:7920
```

Retrieve the one-time initial root password without copying it into a note:

```bash
docker compose exec gitlab \
  grep '^Password:' /etc/gitlab/initial_root_password
```

Sign in as `root`, change the password, and store the replacement in a
password manager.

### 4. Verify HTTP and SSH

```bash
curl --fail --show-error --head http://gitlab.test:7920/users/sign_in

ssh -T -p 7922 git@gitlab.test
```

The SSH command can report that interactive shell access is unavailable while
still proving that GitLab handled the connection.

## Register the Docker runner

### 1. Create the runner in GitLab

Create a project, group, or instance runner in the GitLab UI. Copy its runner
**authentication token**, which begins with `glrt-`.

Legacy runner registration tokens are deprecated; do not restore the older
registration-token workflow from the exploratory note.

### 2. Register it without storing the token in a file

Use a temporary environment variable in the current shell:

```bash
read -rsp "Runner authentication token: " RUNNER_TOKEN
printf '\n'

export RUNNER_TOKEN

docker compose run --rm runner register \
  --non-interactive \
  --url "http://gitlab:7920" \
  --token "$RUNNER_TOKEN" \
  --executor "docker" \
  --docker-image "python:3.12-slim" \
  --docker-pull-policy "if-not-present" \
  --description "mac-docker-runner"

unset RUNNER_TOKEN
```

The runner manager and GitLab service share the explicit `gitlab-local`
Docker network, so the runner uses the service name `gitlab` rather than
`localhost` or a transient container IP.

### 3. Put CI job containers on the same network

Open:

```text
~/srv/gitlab-runner/config/config.toml
```

In the generated runner section, ensure the Docker executor contains:

```toml
[[runners]]
  url = "http://gitlab:7920"
  executor = "docker"

  [runners.docker]
    image = "python:3.12-slim"
    network_mode = "gitlab-local"
    privileged = false
    volumes = ["/cache"]
```

Keep the generated token and other generated fields. Do not replace the whole
file with the small excerpt above.

Start the persistent runner manager:

```bash
docker compose up -d runner

docker compose ps
docker compose logs --tail 100 runner
```

### Why `network_mode` matters

The runner manager is on the Compose network, but the Docker executor creates
additional helper and job containers. Setting `network_mode = "gitlab-local"`
lets those containers resolve and reach `http://gitlab:7920`.

`host.docker.internal` remains useful when a container must call a service
published by the macOS host, but it is unnecessary for this container-to-
container path.

## Smoke-test CI

Create a test project and add the supplied `.gitlab-ci.yml`:

```yaml
default:
  image: python:3.12-slim

test:
  script:
    - python --version
    - python -c "print('GitLab runner is working')"
```

Commit and push it. Confirm that the pipeline is picked up by
`mac-docker-runner`.

## Daily operations

```bash
# Status
docker compose ps

# Logs
docker compose logs --tail 200 gitlab
docker compose logs --tail 200 runner

# Stop without deleting persistent data
docker compose stop

# Start again
docker compose up -d

# Restart one service
docker compose restart gitlab
docker compose restart runner

# Enter the GitLab container
docker compose exec gitlab bash
```

## Backup

GitLab's application backup is stored beneath `/var/opt/gitlab/backups`,
which this Compose file persists under `$GITLAB_HOME/data/backups`.

```bash
docker compose exec -T gitlab gitlab-backup create
```

Back up the configuration and secrets separately:

```bash
mkdir -p ~/Backups

tar -C "$GITLAB_HOME" -czf \
  "$HOME/Backups/gitlab-config-$(date +%Y%m%d-%H%M%S).tar.gz" \
  config
```

Protect backups because `config/gitlab-secrets.json` and the runner
`config.toml` contain secrets.

Keep at least three copies of important GitLab data, on two different storage types, with one
copy offline or off site. A backup is not established until a restore has been tested. On a
disposable GitLab instance, restore the application backup and configuration, start the services,
and verify repository access and a small CI job. Record the GitLab image version and backup format
with the backup so the restore starts from a compatible version.

Do not put backup archives, secrets, tokens, runner state, or generated database dumps in this
Notes repository.

## Upgrade policy

Never use an unpinned `latest` tag for an instance whose data matters.

For each upgrade:

1. Read the GitLab upgrade path and version-specific notes.
2. Back up GitLab data, configuration, and secrets.
3. Pause CI work.
4. Change `GITLAB_IMAGE` and `GITLAB_RUNNER_IMAGE` to the intended compatible
   versions.
5. Pull and recreate the containers.
6. Verify health and wait for migrations to finish before the next stop.

```bash
docker compose pull
docker compose up -d
docker compose logs -f gitlab
```

A historical `17.4.5` instance cannot jump directly to `19.2.1`. At the time
of this refresh, the route includes required stops in the GitLab 17, 18, and
19 release lines. Verify the exact latest patch at every stop with GitLab's
current upgrade-path documentation.

## Troubleshooting

### Port already in use

```bash
lsof -nP -iTCP:7920 -sTCP:LISTEN
lsof -nP -iTCP:7922 -sTCP:LISTEN
```

### GitLab remains unhealthy

```bash
docker compose ps
docker compose logs --tail 500 gitlab
docker compose exec gitlab gitlab-ctl status
docker compose exec gitlab gitlab-rake gitlab:check SANITIZE=true
```

### Runner cannot contact GitLab

```bash
docker compose exec runner \
  wget -S -O /dev/null http://gitlab:7920/users/sign_in

docker network inspect gitlab-local
```

Confirm that the generated runner section uses:

```toml
url = "http://gitlab:7920"

[runners.docker]
  network_mode = "gitlab-local"
```

### Browser works, but clone URLs are wrong

Confirm these two GitLab settings agree with the published ports:

```ruby
external_url 'http://gitlab.test:7920'
gitlab_rails['gitlab_shell_ssh_port'] = 7922
```

Then reconfigure:

```bash
docker compose exec gitlab gitlab-ctl reconfigure
```

## What was intentionally removed

The exploratory note's Gitea commands belong in a separate Gitea note. The
following were also removed:

- Repeated failed commands.
- Container IP addresses, which are ephemeral.
- Plaintext passwords and tokens.
- An HTTPS port mapping without an actual TLS configuration.
- The obsolete Compose `version:` key.
- Legacy runner registration-token instructions.
- `latest` tags in the durable configuration.

## Official references

- GitLab Docker installation:
  https://docs.gitlab.com/install/docker/installation/
- GitLab Docker configuration:
  https://docs.gitlab.com/install/docker/configuration/
- Run GitLab Runner in Docker:
  https://docs.gitlab.com/runner/install/docker/
- Register GitLab Runner:
  https://docs.gitlab.com/runner/register/
- GitLab upgrade paths:
  https://docs.gitlab.com/update/upgrade_paths/
- Upgrade Docker installations:
  https://docs.gitlab.com/update/docker/
- Docker Desktop host networking:
  https://docs.docker.com/desktop/troubleshoot-and-support/faqs/general/
