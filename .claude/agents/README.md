# Claude Agents

AX 저장소의 agent 문서는 특정 command를 보조하는 읽기 전용 역할 위주로 유지합니다.

| Agent | 주 용도 | 주로 함께 쓰는 Command |
|-------|---------|------------------------|
| `code-reviewer` | 읽기 전용 코드 리뷰 | `/review` |
| `test-runner` | 변경 범위 기반 테스트 실행 | `/verify`, `/qa-only` |
| `docker-deployer` | 컨테이너 핫 디플로이/재기동 | `/rebuild-service` |

현재 방침:
- S03에서는 새 agent를 늘리기보다 command 절차를 정리하고, 기존 agent를 보조 역할로 유지한다.
- command가 주도하고 agent는 읽기 전용 분업 또는 격리 실행 용도로만 사용한다.
- 장기적으로 `/cso`, `/benchmark`, `/canary`가 들어오면 agent 확장을 검토한다.
