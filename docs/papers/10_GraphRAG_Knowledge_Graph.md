# GraphRAG: From Local to Global Knowledge Graph RAG

## 논문 정보
- **제목**: From Local to Global: A Graph RAG Approach to Query-Focused Summarization
- **저자**: Darren Edge, et al. (Microsoft Research)
- **게재일**: 2024년 4월 24일
- **arXiv**: [2404.16130](https://arxiv.org/abs/2404.16130)
- **GitHub**: https://github.com/microsoft/graphrag

## 연구 배경
기존 RAG(Retrieval-Augmented Generation)는 개별 문서 검색에는 효과적이지만, "데이터셋의 주요 테마는 무엇인가?"와 같은 전역적 질문에는 한계가 있습니다.

## 핵심 방법론

### 2단계 그래프 인덱싱
1. **엔티티 지식 그래프 생성**
   - LLM을 사용하여 소스 문서에서 엔티티 추출
   - 엔티티 간 관계 파악

2. **커뮤니티 요약 사전 생성**
   - 밀접하게 관련된 엔티티 그룹화
   - 각 커뮤니티에 대한 요약 생성

### 질의 응답 프로세스
1. 각 커뮤니티 요약으로 부분 응답 생성
2. 모든 부분 응답을 최종 응답으로 요약

## 핵심 장점
- **전역적 질문 처리**: 전체 데이터셋에 대한 종합적 질문 가능
- **확장성**: 100만 토큰 범위의 데이터셋 처리
- **포괄성**: 기존 RAG 대비 더 포괄적이고 다양한 답변

## 성능
- 전역적 sensemaking 질문에서 기존 RAG 대비 우수
- 답변의 포괄성(comprehensiveness)과 다양성(diversity) 향상

## 관련 연구
- [Graph RAG Survey](https://arxiv.org/abs/2408.08921) - GraphRAG 서베이 논문
- [Retrieval-Augmented Generation with Graphs](https://arxiv.org/abs/2501.00309)

## AX 시스템 적용
- **사용 API**: Knowledge API (Port 5007)
- **용도**: 도면 지식 그래프 구축, 관계 분석
- **데이터베이스**: Neo4j 그래프 데이터베이스
- **장점**: 도면 컴포넌트 간 관계 추론, 전역적 질의 지원

## 참고 자료
- GitHub: https://github.com/microsoft/graphrag
- 공식 문서: https://microsoft.github.io/graphrag/
- Microsoft Research: https://www.microsoft.com/en-us/research/project/graphrag/
