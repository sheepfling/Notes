# Legacy note assessment

> Type: assessment  
> Status: historical  
> Updated: 2026-08-01

The original note was an unstructured lab log rather than one reproducible
installation procedure.

## Gitea portion

The first portion tested:

- `gitea/gitea:1.22.4`
- Host ports `3000` and `2222`
- Persistent data at `~/srv/gitea/data`
- `gitea/act_runner:0.2.11`
- Both a shared Docker network and `host.docker.internal`

Those commands should be preserved only in a separate Gitea-specific guide.

## GitLab portion

The latter portion tested:

- GitLab EE with an unpinned `latest` tag.
- GitLab CE `17.4.5-ce.0`.
- Persistent directories at `~/srv/gitlab/{config,logs,data}`.
- Host ports `7920`, `7921`, and `7922`.
- A local hostname and `GITLAB_OMNIBUS_CONFIG`.
- GitLab Runner in Docker with a persistent config directory and the host
  Docker socket.

## Problems corrected in the durable guide

- Secrets embedded directly in notes and commands.
- Gitea and GitLab procedures interleaved.
- Multiple commands labeled as winners without one final architecture.
- HTTP external URL and port mapping not consistently aligned.
- HTTPS exposed without a completed certificate/TLS configuration.
- Use of transient container IPs.
- Use of `latest` for stateful GitLab data.
- Incomplete Docker-executor runner configuration.
- Legacy runner registration-token terminology.
- Destructive `rm -rf` commands adjacent to data paths.
