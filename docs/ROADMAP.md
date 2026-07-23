# Roadmap

## Phase 1: deterministic foundation

- [x] Repository skeleton
- [x] CLI entrypoint
- [x] API health endpoint
- [x] Policy decision endpoint wrapper
- [x] Evidence hashing
- [ ] Database schema and migrations
- [ ] Object-store integration
- [ ] Structured audit event log

## Phase 2: policy and isolation

- [ ] Engagement manifest loader
- [ ] Target and artifact registry
- [ ] Worker job queue
- [ ] Rootless static-analysis worker
- [ ] OPA policy test suite
- [ ] Human approval workflow

## Phase 3: reverse engineering pipeline

- [ ] Ghidra headless wrapper
- [ ] Rizin wrapper
- [ ] Function/string/import extraction
- [ ] Evidence-linked analysis summaries
- [ ] Disposable dynamic-analysis VM design

## Phase 4: agent orchestration

- [ ] LangGraph workflow graph
- [ ] Planner node
- [ ] Specialist executor node
- [ ] Verifier node
- [ ] Reporter node
- [ ] Cost and tool-call budgets

## Phase 5: assessment workflows

- [ ] Authorized target import
- [ ] Scope lock and network allowlisting
- [ ] Safe passive discovery
- [ ] Human-approved active checks
- [ ] Evidence-linked report generation
