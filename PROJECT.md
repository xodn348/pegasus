# Pegasus — PROJECT.md (v4)

## 1. Purpose

**클라우드 네이티브 자율 프로젝트 리더 (Claude Code 세션 기반).** 사용자가 폰에서 멀티위크 프로젝트를 시작 → Claude Code 루틴이 핸드오프 → **노트북 끔** → 프로젝트가 스스로 완료. 사용자는 (a) 정말 본인이 결정해야 할 때 또는 (b) 완료 시에만 호출됨.

기반: **Claude Code (세션 인증)** — `CronCreate`, `Agent` (subagent fanout), `PushNotification`, GitHub. **Anthropic API key / Managed Agents API 안 씀.**

### 성공 기준
- `/pegasus start` → 터미널 상태까지, 빌드 윈도우 중 ≥4h 노트북 off
- 모든 milestone satisfied → 루틴 self-disable (`CronDelete`)
- 완료 5분 이내 모바일 푸시 (`PushNotification`)
- 중간 질문 → `/pegasus tell` → 다음 tick이 반영

### Non-goals
- Anthropic API · Managed Agents 베타 · 커스텀 UI · 셀프호스트 러너 · PR 게이트 (auto-merge) · sub-hour cadence · 멀티 프로젝트 루틴 · 인터뷰/플래닝 스킬 재발명

---

## 2. Workflow (normative, 2026-05-17)

1. 사용자 클로드 세션에서 프로젝트 시작
2. 리더가 딥 인터뷰 (20–30분)
3. 리더가 아키텍처/플랜 → spec
4. 리더가 워커 병렬 호출, 각자 spec 전달
5. 워커는 ralph 루프로 완료
6. 리더가 통합 + 사용자 호출 최소화
7. 완료 시 알림

불변: 컴퓨터 off OK · 1 프로젝트 = 1 리포 = 1 루틴 · 완료 시 루틴 자동 비활성 · 모바일 푸시

---

## 3. Architecture

```
L0  Mobile      Claude Code mobile — /pegasus start | tell | status | stop
     ↓
L1  Leader      Claude Code 세션 — 딥 인터뷰 → spec/plan → repo 부트스트랩 → CronCreate → 핸드오프
     ↓  creates  cron "[<project>] driver"  (hourly)
L2  Driver      Claude Code 루틴 세션 (매 tick 새 세션) — state 로드 → Agent fanout → grader subagent → state 갱신
     ↓  Agent tool delegates
L3  Workers     workers/*.md (CEO · CTO · CFO · CMO · COO · GC) — subagent system prompts
     ↓  read/write
L4  GitHub      xodn348/<project> — spec, plan, events.ndjson, state.json
```

> **🟢 Source of truth = GitHub spec.** `xodn348/<project>/spec/` is canonical for everything Pegasus knows about the project. Driver, every worker, and the grader read `spec/current.md` + `spec/milestones/<M>.md` + `spec/addenda.md` directly from the cloned cwd. If a Driver-passed task description disagrees with the spec, **the spec wins.** No in-memory shortcut, no Driver-paraphrased "context" replaces a Read of the spec file.

**Cross-cutting:**
- **State = GitHub.** `state.json` + `spec/*` only cross-tick 진실. 별도 memory store API 없음.
- **Worker = system prompt + repo access.** `workers/*.md` 본문을 `Agent` tool의 `prompt`에 주입 + 워커는 cwd의 `spec/*`를 직접 Read.
- **Workers can fanout.** 모든 워커가 `Agent` tool 보유 — 자체 subagent (Explore, general-purpose) 또는 peer officer (다른 워커 .md 본문 주입) 병렬 호출 가능. cap 3 per call. Driver는 워커 1명당 1개 통합된 답을 기대.
- **Grader = subagent.** tick 끝에 별도 grader `Agent` 호출 (rubric 파일 경로 + diff 보여줌, satisfied/needs_more_work/failed 판정).
- **Mobile push = `PushNotification` tool.** Claude Code 네이티브, relay 안 필요.
- **비용 = Claude Code 구독.** per-token API billing 없음.

---

## 4. Claude Code primitives we use

| Tool / mechanism | Pegasus 사용 |
|---|---|
| **`CronCreate`** | Driver 루틴 등록 — hourly cron, prompt body = `claude/routines/leader-driver.md` |
| **`CronDelete`** | 프로젝트 done 또는 사용자 `/pegasus stop` |
| **`Agent`** | Driver가 매 tick 워커 + grader subagent 병렬 호출. `model`, `subagent_type` 지정 가능. 1 메시지 내 여러 호출 → 병렬 |
| **`PushNotification`** | 사용자 escalation, 완료 알림 |
| **`TaskCreate / Update`** | tick 내 task 추적 |
| **`Bash / Read / Write / Edit`** | repo clone, 파일 작업, commit, push |
| **`WebFetch / WebSearch`** | 워커가 외부 자료 가져올 때 |

Managed Agents 베타, Outcomes API, multiagent coordinator API, `user.define_outcome` 이벤트 — **안 씀**.

---

## 5. Tick semantics

- 1 tick = 1 Claude Code 세션 (cron fires fresh, GitHub만 연속성)
- 프로젝트 완료 = `state.json`의 모든 milestone done. Driver가 `CronDelete` 호출, `phase = done`

### Grader (자체 구현)

Anthropic Outcomes API 없으니 Driver가 매 tick 끝에:
1. 워커 결과물 모음 (diff, 파일 변경, 테스트 결과)
2. `spec/milestones/{M}.md` rubric 첨부
3. `Agent` 호출 — `model=claude-sonnet-4-6`, prompt = "이 작업 결과가 rubric 충족하는가? `satisfied` / `needs_more_work` / `failed` + 2문장 사유"
4. 반환 verdict를 `events.ndjson`에 기록 + state.json 갱신

---

## 6. Decision boundaries

| Driver 자율 | 사용자 확인 |
|---|---|
| next task pick · rubric 인용 · ≤3 워커 · fast-forward 머지 · 1회 revert · push to main · `CronDelete` self-disable | 3-way 충돌 머지 · milestone 추가 · `spec/current.md` 수정 · force push · grader 없이 done 표시 · 2회째 revert |

경계 밖 → `questions/pending.md` + `phase = "awaiting_user"` + `PushNotification`.

---

## 7. State + bus

**`workflow/state.json`** — name, phase (planning / executing / awaiting_user / done / stopped), current_milestone_id, milestones[…], tick_count, last_tick_utc, completion_pct, routine_id.

**`events.ndjson`** kinds — project_init, user_tell, question_raised / resolved, tick_started / satisfied / needs_more_work / failed / skipped, specialist_invoked / returned, integration_failed, milestone_advanced, escalation, pegasus_done, pegasus_stopped.

**두 bus 병행:** Mac `pegasus-os/claude/bus/events.ndjson` (사용자 cross-session 관찰) + 프로젝트 `xodn348/<project>/events.ndjson` (프로젝트 lifecycle). 스키마 공유, 데이터 분리.

---

## 8. Reuse from pegasus-os

pegasus-os도 Claude Code 루틴으로 동작 — 동일 런타임이라 재사용 직접적.

- **VERBATIM**: `bus/SCHEMA.md`, base principles (Think / Simplicity / Surgical / Goal-Driven), `reflectors/{violation,friction}-rules.md`
- **ADAPT**: SOPs (parallel-subagents, spec-seed, worktree-parallel), `skills/pegasus-init` (Leader 인터뷰 80%)
- **SKIP**: daily-self-improve, oss-contributor, weekly-retro, kernel hooks — pegasus-os 전용

---

## 9. v1 milestones

| # | Task |
|---|---|
| 1 | `skills/pegasus/SKILL.md` — 4-verb + 인터뷰 + repo 부트스트랩 + `CronCreate` |
| 2 | `claude/routines/leader-driver.md` — tick 프롬프트: state 로드 → Agent fanout → grader → state 갱신 |
| 3 | `workers.json` — C-suite 워커 매핑 (system_prompt_path + model + tools) |
| 4 | pegasus-os reuse — bus/SCHEMA.md, base principles, reflectors 추출 |
| 5 | Smoke — Ebsilon GTM 1-pager (또는 markdown-toc), ≥4h laptop-off 검증 |

---

## 10. Open questions — resolved 2026-05-20

| Q | A |
|---|---|
| Cron routine prompt 크기 한계 | Claude Code 측 제한. 6KB 이하 권장. 테스트 필요 |
| Tick 세션 lifecycle | **새 세션 매번**. GitHub만 연속성 |
| 모바일 푸시 | **`PushNotification` tool 네이티브** — relay 안 필요 |
| 워커 병렬 호출 | `Agent` tool 1 메시지 내 여러 호출 → 병렬 실행 |
| 비용 | **Claude Code 구독 흡수**, API per-token 빌링 없음 |

---

## 11. Anti-patterns

- Anthropic API / Managed Agents 베타 호출
- 한 tick 안에 너무 많은 task (워커 컨텍스트 폭발)
- Driver가 `spec/current.md` 직접 수정 (addendum-only)
- Force-push / 히스토리 rewrite
- Grader 없이 task done 표시

---

## 12. Footer

Project owner: Junhyuk Lee (xodn348@tamu.edu).  
Spec **v4.0** — 2026-05-20, **session-key (Claude Code) architecture**. Supersedes v3 (which used Anthropic Managed Agents API).  
README = public intro. 본 문서 = 엔지니어링 진실.
