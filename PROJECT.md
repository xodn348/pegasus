# Pegasus — PROJECT.md (v3)

## 1. Purpose

**클라우드 네이티브 자율 프로젝트 리더.** 사용자가 폰에서 멀티위크 프로젝트를 시작 → Anthropic 클라우드로 핸드오프 → **노트북 끔** → 프로젝트가 스스로 완료. 사용자는 (a) 정말 본인이 결정해야 할 때 또는 (b) 완료 시에만 호출됨.

기반: Anthropic Managed Agents (Outcomes, Multiagent Orchestration, Memory, Scheduled Routines).

### 성공 기준
- `/pegasus start` → 터미널 상태까지, 빌드 윈도우 중 ≥4h 노트북 off
- 모든 milestone satisfied → 루틴 self-disable
- 완료 5분 이내 모바일 알림
- 중간 질문 → `/pegasus tell` → 다음 tick이 반영

### Non-goals
- 커스텀 UI (Claude Console로 충분) · 셀프호스트 러너 · PR 게이트 (auto-merge) · sub-hour cadence · 멀티 프로젝트 루틴 · 인터뷰/플래닝 스킬 재발명

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
L0  Mobile      /pegasus start | tell | status | stop
     ↓
L1  Leader      딥 인터뷰 → spec/plan → repo 부트스트랩 → memory_store 생성 → cron 등록 → 핸드오프
     ↓  creates  [<project>] driver  (hourly)
L2  Driver      매 tick: state 로드 → Outcome 선언 → multiagent 위임 → 통합 → state 갱신
     ↓  delegates
L3  Workers     C-suite specialists (CEO · CTO · CFO · CMO · COO · GC), ralph 루프
     ↓  read/write
L4  GitHub      xodn348/<project> — spec, plan, events.ndjson, state.json
```

**Cross-cutting (v1 필수):**
- **Memory store** workspace-scoped (cross-agent). Leader 생성 → Driver 매 tick `/mnt/memory/` 마운트. `state.json`이 진실
- **Prompt caching** `cache_control` 1h TTL → 시스템 프롬프트 캐시 hit 90% 할인. Hourly cron과 정확히 정합
- **Model tiering** Haiku = 워커 / Sonnet = Driver coordinator / Opus = 어려운 결정만 → 4–6× 비용 절감
- **Worker별 MCP** CFO+Stripe, COO+Linear, CMO+Notion, CTO+GitHub, GC+web_search (v1엔 1–2개만, 나머지 v1.5)
- **Anthropic prebuilt skills** xlsx / pdf / pptx / docx 기본 활용

---

## 4. Anthropic primitives

Beta header `managed-agents-2026-04-01`. Verified vs official cookbooks.

| Primitive | Pegasus 사용 |
|---|---|
| **Outcomes** | tick당 1개. rubric = spec 파일. `max_iterations = 5` (하드 캡 20). 터미널: satisfied / failed / max_iterations_reached / interrupted |
| **Multiagent Orchestration** | `multiagent={"type":"coordinator","agents":[...]}` 선언 + 런타임 `agent_toolset_20260401` 호출. depth 1, ≤20 unique, ≤25 concurrent |
| **Memory store** | workspace-scoped, `/mnt/memory/`. CAS via `content_sha256`. 30일 버전 보관. ≤8 stores/session, 100KB/memory cap |
| **Scheduled Routines** | header `experimental-cc-routine-2026-04-01`. tick마다 **새 세션** — memory_store + GitHub만 연속 |
| **Webhooks** | `session.outcome_evaluation_ended` 등. 모바일 푸시는 native 없음 → 직접 relay 필요 |
| **Dreaming** | v1 skip. 스모크 후 재평가 |

---

## 5. Outcomes — tick 단위 수렴

- 1 Outcome = 1 세션 = 1 tick (세션 간 이월 없음)
- `max_iterations` = grader 평가 횟수 (cap 20, Driver 기본 5)
- "프로젝트 완료"는 **Outcomes가 아니라 우리 `state.json` 상태머신**이 결정. 모든 milestone done → 루틴 self-disable

tick 동작:
1. Driver wake (새 세션) → state 로드 → 현재 milestone ready task 선택
2. `user.define_outcome` 발사 — description + rubric path + max_iterations=5
3. multiagent 위임 → 워커 작업 → grader 평가
4. `satisfied` → state 갱신 → 다음 cron tick 대기
5. `max_iterations_reached` → milestone 진행중 유지, 다음 tick 재시도
6. `failed` → 차단 표시 → 사용자 escalation

---

## 6. Decision boundaries

| Driver 자율 | 사용자 확인 |
|---|---|
| next task pick · rubric 인용 · ≤3 워커 · fast-forward 머지 · 1회 revert · push to main · 루틴 disable | 3-way 충돌 머지 · milestone 추가 · spec/current.md 수정 · force push · grader 없이 done 표시 · 2회째 revert |

경계 밖 → `questions/pending.md` + `phase = "awaiting_user"` + 모바일 푸시.

---

## 7. State + bus

**`workflow/state.json`** — name, phase (planning / executing / awaiting_user / done), current_milestone_id, milestones[…], tick_count, completion_pct, routine_id, managed_agent_id.

**`events.ndjson`** kinds — project_init, user_tell, question_raised / resolved, tick_started / satisfied / failed / max_iterations / interrupted, specialist_invoked / returned, integration_failed, milestone_advanced, escalation, pegasus_done, pegasus_stopped. Anthropic 세션 이벤트도 미러링.

**두 bus 병행:** Mac `pegasus-os/claude/bus/events.ndjson` (사용자 cross-session 관찰) + 프로젝트 `xodn348/<project>/events.ndjson` (프로젝트 lifecycle). 스키마 공유, 데이터 분리.

---

## 8. Reuse from pegasus-os

- **VERBATIM**: `bus/SCHEMA.md`, base principles (Think / Simplicity / Surgical / Goal-Driven), `reflectors/{violation,friction}-rules.md`
- **ADAPT**: SOPs (parallel-subagents, spec-seed, worktree-parallel), `skills/pegasus-init` (Leader 인터뷰 80%)
- **SKIP**: daily-self-improve, oss-contributor, weekly-retro, kernel hooks — pegasus-os 전용

---

## 9. v1 milestones

| # | Task |
|---|---|
| 1 | `skills/pegasus/SKILL.md` — 4-verb (start/tell/status/stop) + 인터뷰 체인 + memory_store 생성 + cron 등록 |
| 2 | `claude/routines/leader-driver.md` — tick 프롬프트: state 로드 → Outcome 선언 → multiagent 위임 → 통합 → state 갱신 |
| 3 | `workers.json` — C-suite 워커 매핑 (CEO / CTO / CFO / CMO / COO / GC) |
| 4 | v1 필수 5개 박기 — memory_store · prompt caching · model tiering · worker별 MCP · prebuilt skills |
| 5 | pegasus-os reuse — bus/SCHEMA.md, base principles, reflectors 추출 |
| 6 | Smoke — Ebsilon GTM 1-pager (또는 markdown-toc), ≥4h laptop-off 검증 |

---

## 10. Open questions — resolved 2026-05-20

| Q | A |
|---|---|
| Routine prompt size limit | 미공개. 6KB 이하 권장. **테스트 필요** |
| Tick 세션 lifecycle | **새 세션**. memory_store + GitHub만 연속성 보장 |
| 모바일 푸시 | Anthropic native **없음**. webhook `session.outcome_evaluation_ended` → 직접 relay (Pushover / APNs) |
| Multiagent 선언적 roster | **있음** — `multiagent={"type":"coordinator","agents":[...]}`. 런타임 위임은 `agent_toolset_20260401` |
| Memory 스코프 | **workspace-scoped** (per-agent 아님). Leader + Driver가 같은 workspace 공유 → 진실 공유 가능 |

남은 미확정: 루틴 프롬프트 body 한계 (실험으로 확인).

---

## 11. Anti-patterns

- Polling — 세션 이벤트 스트림이 푸시 채널
- 하나의 Outcome으로 전체 프로젝트 평가 (per-tick임)
- Driver가 `spec/current.md` 직접 수정 (addendum-only)
- `max_iterations_reached`를 "완료"로 해석
- Force-push / 히스토리 rewrite

---

## 12. Footer

Project owner: Junhyuk Lee (xodn348@tamu.edu).  
Spec **v3.0** — 2026-05-20, post Anthropic API verification + 4-agent upgrade research integration. Supersedes v2.  
README = public intro. 본 문서 = 엔지니어링 진실.
