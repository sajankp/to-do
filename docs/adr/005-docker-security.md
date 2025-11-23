# ADR-005: Docker Multi-Stage Build with Non-Root User

**Status:** Accepted

**Date:** 2024

**Deciders:** Project team

**Related PR:** [#40 - Fix: Size reduction and non-root user runs](https://github.com/sajankp/to-do/pull/40)

---

## Context

Docker containerization was needed for:
- Consistent deployment across environments
- Easy local development setup
- Production deployment on Render/cloud platforms
- CI/CD pipeline integration

Initial Dockerfile had security and efficiency concerns:
- Running as root user (security risk)
- Large image size
- Dependencies rebuilt on every change

### Alternatives Considered

1. **Single-Stage Build as Root**
   - Pros: Simple, straightforward
   - Cons: Security risk, larger images, slower builds

2. **Rootless Containers (Podman)**
   - Pros: No root needed
   - Cons: Less mature tooling, platform compatibility

3. **Multi-Stage Build + Non-Root User** ✅
   - Pros: Smaller images, better security, faster rebuilds
   - Cons: Slightly more complex Dockerfile

---

## Decision

We implemented **multi-stage Docker build** with **non-root user** (PR #40).

### Implementation

#### Dockerfile Structure

**Stage 1: Builder**
```dockerfile
FROM python:3.13-slim AS builder
RUN useradd -m appuser
USER appuser
WORKDIR /code
COPY ./requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
```

**Stage 2: Runtime**
```dockerfile
FROM python:3.13-slim
RUN useradd -m appuser
USER appuser
WORKDIR /code
COPY --from=builder /home/appuser/.local /home/appuser/.local
COPY ./app ./app
ENV PATH=/home/appuser/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Key Decisions

1. **Non-Root User (`appuser`)**
   - Created in both stages
   - Owns application files
   - Runs uvicorn process

2. **Multi-Stage Build**
   - Builder stage: Installs dependencies
   - Runtime stage: Copies only what's needed
   - Reduces final image size

3. **User-Local Pip Installs**
   - `pip install --user` in home directory
   - No need for system-wide permissions
   - Easier to copy between stages

4. **Port 8000** (not 80)
   - Non-root can't bind to privileged ports (<1024)
   - Port mapping handled by container runtime

---

## Consequences

### Positive

✅ **Security**: Non-root user limits attack surface  
✅ **Image Size**: Smaller final image (build artifacts excluded)  
✅ **Build Speed**: Dependencies cached separately from app code  
✅ **Best Practices**: Follows Docker security recommendations  
✅ **Container Scanning**: Passes security scans (fewer vulnerabilities)  
✅ **Platform Compatibility**: Works on Render, AWS, GCP, etc.  

### Negative

⚠️ **Complexity**: Two-stage Dockerfile harder to understand initially  
⚠️ **Port Change**: Had to change from port 80 to 8000 (non-privileged)  
⚠️ **Permissions**: Need to ensure file permissions match appuser  

### Metrics

- **Image Size Reduction**: ~30% smaller (exact metrics in PR #40)
- **Build Time**: Faster rebuilds when only app code changes
- **Security**: No root processes running in container

---

## Security Improvements (PR #40)

1. **Non-root execution**
   - Process runs as `appuser` (UID 1000)
   - Limited blast radius if container compromised

2. **Minimal final image**
   - Only runtime dependencies
   - No build tools (gcc, etc.)

3. **No cache in install**
   - `--no-cache-dir` reduces image size
   - Forces fresh downloads (no stale packages)

4. **Explicit EXPOSE**
   - Documents expected port
   - Good for orchestration tools

---

## Deployment Considerations

### Local Development
```bash
docker build -t fasttodo .
docker run -p 80:8000 --env-file .env fasttodo
```
(Port mapping 80:8000 allows localhost:80 access)

### Production (Render)
- Render handles port mapping automatically
- Environment variables injected via platform
- Health checks work on port 8000

### Future: Kubernetes
- Deployment YAML would specify port 8000
- Security context can enforce non-root
- Resource limits easier with user separation

---

## Related Decisions

- **ADR-001**: FastAPI chosen (now containerized)
- **Environment Security** (PR #41): Credentials moved to env vars, not hardcoded

---

## Follow-up Actions

- [ ] Add healthcheck to Dockerfile (HEALTHCHECK instruction)
- [ ] Consider distroless base image for even smaller size
- [ ] Implement docker-compose for local dev with MongoDB
- [ ] Add .dockerignore to exclude unnecessary files

---

## References

- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [PR #40](https://github.com/sajankp/to-do/pull/40) - Implementation
- [Dockerfile](../../Dockerfile) - Current implementation
- [OWASP Docker Security](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
