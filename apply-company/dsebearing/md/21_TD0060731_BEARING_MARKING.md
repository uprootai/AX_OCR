# TD0060731 - BEARING MARKING (베어링 마킹)

## 도면 정보

| 항목 | 값 |
|------|-----|
| **도면 번호** | TD0060731 |
| **Rev** | C |
| **제목** | BEARING MARKING |
| **크기** | A1 (594×841mm) |
| **단위** | mm |
| **Scale** | N/S |
| **Sheet** | 1/1 |
| **발행처** | DOOSAN Enerbility |
| **날짜** | 2024.03.29 (Rev C) |

---

## 리비전 이력

| REV | 날짜 | 설명 |
|-----|------|------|
| B | - | 전면개정 |
| C | 2024.03.29 | 최신 |

---

## 적용 베어링 유형

| 베어링 유형 | 마킹 위치 참조 |
|------------|--------------|
| **TILTING PAD JOURNAL BEARING** | NOTES "4" |
| **SHORTEND ELLIPTICAL BEARING** | NOTES "4" |
| **STANDARD ELLIPTICAL BEARING** | NOTES "4" |
| **THRUST BEARING (1COLLAR TYPE)** | NOTES "5" |
| **THRUST BEARING (2COLLAR TYPE)** | NOTES "5" |
| **THRUST SHIM PLATE** | NOTES "5" |

---

## 저널 베어링 마킹 (JOURNAL BEARING)

### TILTING PAD JOURNAL BEARING

```
                MARKING POSITION
                마킹내용은 NOTES "4" 볼것
                      ↓
    ┌─────────────────────────────────────┐
    │          12시 방향 기준              │
    │              ↓                      │
    │         ┌─────────┐                 │
    │         │ STAMPING│                 │
    │         │ AS SHOWN│                 │
    │     ┌───┼─────────┼───┐             │
    │     │   │         │   │             │
    │  C ─┤   │ LINER   │   ├─ C          │
    │     │   │  PAD    │   │             │
    │     └───┼─────────┼───┘             │
    │         └─────────┘                 │
    │                                     │
    │  PAD PLATE와 RING에 베어링 번호와     │
    │  위치를 표기할 것 (NOTE6 참조)        │
    └─────────────────────────────────────┘

    [EXAMPLE]
    DONGTAN#1
    T1.LOWER
    TD000609.REV.B
    GEN SIDE
    @RTON
```

### SHORTEND ELLIPTICAL BEARING

```
    ┌─────────────────────────────────────┐
    │      MARKING POSITION               │
    │      마킹내용은 NOTES "4" 볼것       │
    │              ↓                      │
    │         ┌─────────┐                 │
    │         │ JOINT   │                 │
    │         │ SHIM    │                 │
    │     ┌───┴─────────┴───┐             │
    │     │                 │             │
    │     │    Elliptical   │             │
    │     │    Bearing      │             │
    │     └─────────────────┘             │
    │                                     │
    │  PAD PLATE와 RING에 베어링 번호와     │
    │  위치를 표기할 것 (NOTE6 참조)        │
    └─────────────────────────────────────┘
```

### STANDARD ELLIPTICAL BEARING

```
    ┌─────────────────────────────────────┐
    │      MARKING POSITION               │
    │      마킹내용은 NOTES "4" 볼것       │
    │              ↓                      │
    │         ┌─────────┐                 │
    │         │         │                 │
    │     ┌───┴─────────┴───┐             │
    │     │                 │             │
    │     │   Standard      │             │
    │     │   Elliptical    │             │
    │     └─────────────────┘             │
    │                                     │
    │  JOINT SHIM과 RING에 베어링 번호와    │
    │  상유위치를 표기할 것 (EX. 1L, 1R)    │
    └─────────────────────────────────────┘
```

---

## 스러스트 베어링 마킹 (THRUST BEARING)

### THRUST BEARING (1COLLAR TYPE / 2COLLAR TYPE)

```
    ┌─────────────────────────────────────┐
    │      MARKING POSITION               │
    │      마킹내용은 NOTES "5" 볼것       │
    │                                     │
    │  모든 THRUST SHIM은:                 │
    │  - TBN SIDE인지                      │
    │  - GEN SIDE인지                      │
    │  MARKING을 갖출 것                   │
    │  물자관리도 SHIM을 이치할것           │
    │                                     │
    │         DETAIL F-6                  │
    │         ┌───────┐                   │
    │    F-6 →│       │                   │
    │         │ SHIM  │                   │
    │         │ PLATE │                   │
    │         └───────┘                   │
    └─────────────────────────────────────┘
```

---

## 마킹 규격

### 문자 크기

| 항목 | 규격 |
|------|------|
| **문자 크기** | 8 ~ 12 mm |
| **적용 면** | 회전방향 표기면에만 |

### 마킹 방법

| 방법 | 허용 여부 |
|------|---------|
| **STAMPING** | ✅ 허용 |
| **전동펜** | ✅ 허용 |
| **SHARP EDGE PUNCH** | ❌ 금지 |

---

## 저널 베어링 마킹 내용 (NOTES 4)

### 필수 마킹 항목

| 순번 | 항목 | 예시 |
|-----|------|------|
| 1 | **PROJECT NAME** | HANAM, M01 |
| 2 | **BEARING NO.** | T1 LOWER, T2 UPPER |
| 3 | **DWG NO.** | TD0060709.REV.B |
| 4 | **SIDE** | TBN SIDE / GEN SIDE (또는 HP SIDE / LP SIDE) |
| 5 | **BEARING WEIGHT** | 소수점 2자리 (TON 단위) |

### 마킹 예시

```
┌─────────────────────────────┐
│  DONGTAN#1                  │  ← PROJECT NAME
│  T1.LOWER                   │  ← BEARING NO.
│  TD000609.REV.B             │  ← DWG NO.
│  GEN SIDE                   │  ← SIDE
│  1.25TON                    │  ← WEIGHT
└─────────────────────────────┘
```

---

## 스러스트 베어링 마킹 내용 (NOTES 5)

### 필수 마킹 항목

| 순번 | 항목 | 예시 |
|-----|------|------|
| 1 | **PROJECT NAME** | HANAM, M01 |
| 2 | **BEARING NO.** | HP THRUST LOWER, LP THRUST UPPER |
| 3 | **DWG NO.** | TD0062xxx |
| 4 | **SIDE** | TBN SIDE / GEN SIDE (또는 HP SIDE / LP SIDE) |
| 5 | **BEARING WEIGHT** | 소수점 2자리 (TON 단위) |

---

## PAD 번호 체계 (NOTES 6)

### 번호 부여 규칙

```
         12시 방향
            ↑
            │
    ┌───────┼───────┐
    │   2   │   1   │ ← 9시 방향 PAD = 1번
    │       │       │
 9시├───────┼───────┤3시
    │   3   │   4   │
    │       │       │
    └───────┼───────┘
            │
         6시 방향

    PAD 번호: 9시 방향부터 시계방향으로 1, 2, 3, 4...
```

### 번호 표기 예시

| PAD 위치 | 번호 표기 |
|---------|---------|
| 9시 방향 (좌측) | **1 L** |
| 12시 방향 | **2** |
| 3시 방향 (우측) | **3** |
| 6시 방향 | **4** |

---

## NOTES (주의사항)

### 한국어
1. **마킹 SIZE**는 회전방향을 표기한 면에만 실시하며 글자 크기는 **8~12MM**로 해도 인감에서 작성
2. **CASING&RING**의 UPPER면과 LOWER에 각각 회전방향과 **"ROTATION"**로 표기할 것
3. **마킹 위치**는 가공부 (HOLE, ETC.)를 피할 것
4. **저널 베어링 마킹 내용**은 상기 항목 따를 것
5. **스러스트 베어링 마킹 내용**은 상기 항목 따를 것
6. **모든 베어링 번호와 PAD**에 호로 구분하여 **9시 방향에 있는 PAD가 1번**임 (EX. 1L, 1, 2, 3, 4 등)
7. **SHARP EDGE PUNCH**는 사용하지 말것

### English
1. MARKING SHOULD BE DONE ONLY FOR THE SURFACE MARKING **ROTATION DIRECTION** AND **CHARACTER DIMENSION IS 8~12MM** (EXCEPT SPECIAL COMMENT)
2. MARKING WILL BE MARKED ON WITH **"ROTATION"** AT UPPER AND LOWER OF CASING&RING
3. MARKING POSITION SHOULD **AVOID MACHINING AREA** (HOLE, ETC.)
4. MARKING CONTENTS FOR **JOURNAL BEARING** ARE AS ABOVE
5. MARKING CONTENTS FOR **THRUST BEARING** ARE AS ABOVE
6. PUNCH BEARING NUMBER AND PAD NUMBER. **9 O'CLOCK PAD PLATE IS NUMBER 1** (EX. 1L, 1, 2, 3, 4)
7. **DO NOT USE PUNCH WITH SHARP EDGE**

---

## 마킹 위치 요약

### 저널 베어링

| 부품 | 마킹 위치 |
|------|---------|
| **CASING** | UPPER/LOWER 회전방향 |
| **RING** | UPPER/LOWER 회전방향 |
| **PAD PLATE** | 베어링 번호, PAD 번호 |
| **LINER PAD** | PAD 번호 |
| **JOINT SHIM** | 베어링 번호, 위치 (1L, 1R) |

### 스러스트 베어링

| 부품 | 마킹 위치 |
|------|---------|
| **THRUST COLLAR** | 베어링 번호, SIDE |
| **THRUST SHIM** | TBN/GEN SIDE |
| **SHIM PLATE** | 베어링 번호, SIDE |

---

## BOM 참조

### 마킹 대상 베어링

| 베어링 | 도면 번호 | 마킹 참조 |
|-------|----------|---------|
| T1 Journal | TD0062015~TD0062020 | NOTES 4 |
| T2 Journal | TD0062021~TD0062025 | NOTES 4 |
| T3 Journal | TD0062026~TD0062030 | NOTES 4 |
| T4~T8 Journal | TD0062031~TD0062066 | NOTES 4 |
| HP Thrust | - | NOTES 5 |
| LP Thrust | - | NOTES 5 |

---

*분석일: 2026-01-20*
*분석 도구: Claude Code (Multimodal LLM)*
