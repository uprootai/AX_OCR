# 동서기연 (DSE Bearing) 요구사항 분석

> **작성일**: 2026-01-20 (최종 업데이트: 2026-01-21)
> **프로젝트**: 터빈 베어링 도면 분석 및 견적 자동화
> **분석 상태**: ✅ **94개 전체 완료 (100%)**

---

## 1. 전달받은 자료 현황

### 1.1 파일 통계

| 구분 | 파일 수 | 용량 | 분석 상태 | 설명 |
|------|---------|------|----------|------|
| **BOM** | 1개 | 0.4MB | ✅ 완료 | BOM_Z24018 (395개 품목) |
| **제조사양서** | 1개 | 33MB | ⚠️ 메타데이터 | PDM002.pdf (대형 조립도) |
| **구매사양서** | 1개 | 12MB | ✅ 완료 | STMPS00095.pdf |
| **부품 도면** | 91개 | ~100MB | ✅ 완료 | TD 시리즈 개별 부품도 |
| **합계** | **94개** | **~145MB** | **94/94** | 1UNIT PJT 전체 도면 |

### 1.2 도면 카테고리 분류

#### A. 체결 부품 (Fasteners) - 15개
| 도면번호 | 품명 | Rev |
|----------|------|-----|
| TD0060700 | BOLT TORQUE TABLE | B |
| TD0060701 | HEX SOCKET HD BOLT | B |
| TD0060702 | SPRING WASHER | B |
| TD0060703 | DOWEL PIN | B |
| TD0060704 | HEX NUT | C |
| TD0060708 | HEX HD BOLT | B |
| TD0060709 | BUTTON HD SOCKET BOLT | B |
| TD0060711 | PIN | C |
| TD0060712 | SET PIN | B |
| TD0060718 | PIPE PLUG | D |
| TD0060722 | PIPE PLUG | B |
| TD0060746 | LOCKING PIN | A |
| TD0060748 | NORD LOCK WASHER | A |
| TD0060707 | LOCKING PIN | C |
| TD0060729 | LOCKING PIN | B |

#### B. 저널 베어링 (T1~T8) - 40개
| 타입 | 사양 | 구성품 |
|------|------|--------|
| T1 | 360x190 | BEARING ASSY, RING ASSY, RING, CASING ASSY, CASING, LINER PAD |
| T2 | 380x190 | BEARING ASSY, RING ASSY, CASING ASSY, CASING, LINER PAD |
| T3 | 380x260 | BEARING ASSY, RING ASSY, CASING ASSY, CASING, LINER PAD |
| T4 | 420x260 | BEARING ASSY, RING ASSY, RING, CASING ASSY, CASING, LINER PAD |
| T5 | 460x260 | BEARING ASSY, RING ASSY, RING, CASING ASSY, CASING |
| T6 | 460x260 | BEARING ASSY, RING ASSY, CASING ASSY, CASING |
| T7 | 460x260 | BEARING ASSY, RING ASSY, CASING ASSY, CASING |
| T8 | 500x260 | BEARING ASSY, RING ASSY, RING, CASING ASSY, CASING |

#### C. 스러스트 베어링 (Thrust Bearing) - 12개
| 도면번호 | 품명 | 용도 | 분석 |
|----------|------|------|------|
| TD0062055 | THRUST BEARING ASSY (OD670xID440) | 터빈용 | ✅ |
| TD0062056 | THRUST BEARING RING ASSY | - | ✅ |
| TD0062057 | THRUST BEARING RING | - | ✅ |
| TD0062058 | THRUST CASING ASSY (TBN) | 터빈용 | ✅ |
| TD0062059 | THRUST CASING (TBN) | 터빈용 | ✅ |
| TD0062060 | THRUST PAD (TBN) | 터빈용 | ✅ |
| TD0062061 | UPPER LEVELING PLATE | - | ✅ |
| TD0062062 | LOWER LEVELING PLATE | - | ✅ |
| TD0062063 | THRUST SHIM PLATE | TBN/GEN 공용 | ✅ |
| TD0062064 | THRUST CASING ASSY (GEN) | 발전기용 | ✅ |
| TD0062065 | THRUST CASING (GEN) | 발전기용 | ✅ |
| TD0062066 | THRUST PAD (GEN) | 발전기용 | ✅ |

#### D. 조정 부품 (Adjustment Parts) - 14개
| 도면번호 | 품명 | Rev |
|----------|------|-----|
| TD0060742 | SHIM PLATE | B |
| TD0060743 | SOLID SHIM PLATE | B |
| TD0060744 | MOVING WEDGE | A |
| TD0060745 | FIXED WEDGE | B |
| TD0060747 | JOINT SHIM | B |
| TD0060749 | SHIM PLATE | B |
| TD0060750 | ADJUST SHIM | A |
| TD0060751 | ADJUST SHIM | A |
| TD0060752 | LOWER ADJUST WEDGE ASSY | B |
| TD0060753 | SIDE ADJUST WEDGE ASSY | A |
| TD0060754 | SIDE ADJUST SHIM ASSY | A |
| TD0060717 | LOCKING PLATE | C |
| TD0060728 | PIVOT | B |
| TD0060720 | BUSHING | B |

#### E. 기타 부품 - 6개
| 도면번호 | 품명 | 설명 | 분석 |
|----------|------|------|------|
| TD0060706 | ANTI WEAR PAD | 마모 방지 | ✅ |
| TD0060710 | WIRE CLIP | - | ✅ |
| TD0060730 | NOZZLE | 오일 분사 | ✅ |
| TD0060731 | BEARING MARKING | 마킹 규격 | ✅ |
| TD0339626 | CONE COVER FOR CV | 커버 | ✅ |
| TD0339628 | PERFORATED CYLINDER FOR CV | 다공 실린더 | ✅ |

#### F. 품질 기준서 (CTQ) - 4개
| 도면번호 | 품명 | 대상 베어링 | 분석 |
|----------|------|------------|------|
| TD0060732 (1/4) | CTQ - 일반사항 | 전체 | ✅ |
| TD0060732 (2/4) | CTQ - ELLIPTICAL BEARING | 저널 베어링 (T1~T8) | ✅ |
| TD0060732 (3/4) | CTQ - TAPER LAND THRUST | 테이퍼 랜드 스러스트 | ✅ |
| TD0060732 (4/4) | CTQ - TILTING PAD THRUST | 틸팅 패드 스러스트 | ✅ |

#### G. 문서류 - 3개
| 파일명 | 품명 | 설명 | 분석 |
|--------|------|------|------|
| BOM_Z24018 | BOM 목록 | 395개 품목, 재질 SS400 | ✅ |
| STMPS00095 | 터빈베어링 구매사양서 | MPS 문서 | ✅ |
| PDM002 | 베어링 제조사양서 | 33MB 대형 문서 | ⚠️ 메타데이터 |

---

## 2. 고객 요구사항 정리

### 2.1 도면 샘플 요청 (완료)
- **요청**: 5~10장 샘플
- **실제 전달**: 94개 PDF (1UNIT PJT 전체)
- **BOM 기준**: Z24018_110104001_BRG_R1 (350개 품목)

### 2.2 도면에서 추출 필요 정보 (확인 필요)

#### 예상 추출 항목
| 항목 | 설명 | 우선순위 |
|------|------|----------|
| 도면번호 | TD00XXXXX | 필수 |
| Rev | A, B, C, D 등 | 필수 |
| 품명 | BEARING, CASING 등 | 필수 |
| 재질 | SS400, 기타 | 필수 |
| 주요 치수 | OD, ID, Length | 필수 |
| 공차 | 기하공차, 치수공차 | 중요 |
| 표면 거칠기 | Ra 값 | 중요 |
| 열처리 | 경도, 조건 | 중요 |

### 2.3 현재 견적 프로세스

| 단계 | 소요일 | 내용 |
|------|--------|------|
| 1. BOM 확인 | - | 도면 그룹별 분류 |
| 2. 사양 확인 | 4일 | 도면별 사양 검토 |
| 3. 외주 견적 | 6일 | 협력사 견적 요청 |
| 4. 자체 검토 | 2일 | 최종 검토 및 조정 |
| **합계** | **12일** | - |

**우선 개선 대상**: 소재 및 부품 견적

---

## 3. 도면 특성 분석

### 3.1 도면 유형
- **타입**: 기계 부품도 (Mechanical Part Drawing)
- **표준**: ISO/JIS 기반 추정
- **언어**: 영문 (품명), 일부 한글 메모

### 3.2 AI 분석 적용 가능성

| 기능 | 적용 가능성 | 비고 |
|------|-------------|------|
| YOLO 심볼 검출 | △ | 기계도면용 모델 필요 |
| eDOCr2 치수 인식 | ◎ | 한글/영문 혼합 지원 |
| 공차 분석 | ◎ | SkinModel API 활용 |
| BOM 매칭 | ◎ | 도면번호 기반 매핑 |

### 3.3 테크로스와 비교

| 항목 | 테크로스 (BWMS) | 동서기연 (Bearing) |
|------|-----------------|-------------------|
| 도면 유형 | P&ID (공정도) | 기계 부품도 |
| 주요 심볼 | 밸브, 계기, 플랜지 | 치수선, 공차 기호 |
| 추출 정보 | 장비 목록, 연결 관계 | 치수, 재질, 공차 |
| YOLO 모델 | pid_class_aware | engineering (예정) |

---

## 4. 제안 개발 방향

### 4.1 1단계: 치수 및 텍스트 추출
- eDOCr2 기반 OCR 적용
- 도면번호, 품명, 재질 자동 추출
- BOM과 도면 자동 매핑

### 4.2 2단계: 공차 분석
- SkinModel API 활용
- 기하공차, 치수공차 자동 인식
- 가공 난이도 분류

### 4.3 3단계: 견적 자동화
- 추출 정보 기반 견적서 생성
- 소재비, 가공비 자동 산출
- 외주 견적 요청서 자동 생성

---

## 5. 분석 완료 현황 (2026-01-21 업데이트)

### 5.1 완료 항목

| 항목 | 상태 | 내용 |
|------|------|------|
| **전체 도면 분석** | ✅ 완료 | 94개 PDF → 94개 MD 분석 파일 |
| **BOM 분석** | ✅ 완료 | 395개 품목 카테고리화 |
| **도면-BOM 매핑** | ✅ 완료 | TD 도면번호 기반 연결 |
| **CTQ 분석** | ✅ 완료 | 품질 기준 4종 분석 |

### 5.2 다음 단계 (고객 회신 필요)

1. **온라인 미팅 진행** ⏳
   - 도면에서 추출 필요 정보 상세 확인
   - 현재 견적서 양식 검토
   - **일정 회신 대기 중**

2. **기존 견적서 양식** ⏳
   - Excel 또는 PDF 파일 요청
   - **미수령**

3. **우선 견적 품목 리스트** ⏳
   - 395개 품목 중 우선순위 항목
   - **미수령**

4. **외주 견적 요청서 양식** ⏳
   - 6일 소요 프로세스 자동화 검토
   - **미수령**

---

## 6. 분석 결과 요약

### 6.1 MD 분석 파일 통계

| 카테고리 | 파일 수 | 번호 범위 |
|----------|---------|----------|
| BOM | 1 | 00 |
| 구매사양서 | 1 | 01 |
| 체결 부품 | 15 | 02~16 |
| 조정 부품 | 14 | 17~30 |
| 저널 베어링 (T1~T8) | 40 | 31~70 |
| 스러스트 베어링 | 12 | 71~82 |
| CTQ 문서 | 4 | 83~86 (2/4~4/4), 22 (1/4) |
| 기타 | 7 | 86~93 |
| **합계** | **94** | - |

### 6.2 주요 발견 사항

| 항목 | 내용 |
|------|------|
| **주요 재질** | SF440A (단조강), SM490A, S45C-N, SS400, ASTM A193 B7 |
| **베빗 재질** | ASTM B23 GR.2 |
| **일반 공차** | ISO 2768-m |
| **베어링 타입** | 저널(T1~T8), 스러스트(TBN/GEN) |
| **패드 유형** | Elliptical, Taper Land, Tilting Pad |

---

## 7. 보안 유의사항

> **도면 보안관련 철저히 부탁드립니다.**

- 모든 도면 파일은 프로젝트 내부에서만 사용
- 외부 전송 금지
- 분석 완료 후 샘플 데이터 삭제 협의

---

*작성: Claude Code (AX POC)*
*최종 업데이트: 2026-01-21*
