# TECHLOSS (TECHCROSS) 디렉토리 구조

> **최종 업데이트**: 2026-01-17
> **총 파일 수**: ~240개 (정리 후)
> **총 용량**: ~49MB

---

## 프로젝트 개요

**TECHCROSS BWMS (Ballast Water Management System)** AI 도면 검토 시스템

| 항목 | 내용 |
|------|------|
| **제품 라인** | ECS (Electrolysis Chlorination System), HYCHLOR 2.0 |
| **목적** | P&ID 도면 자동 검토, Equipment List/Valve Signal List/Deviation List 생성 |
| **워크플로우** | `도면 입력 → AI 검토 → 체크리스트 자동 작성 → 승인` |

---

## 디렉토리 트리

```
techloss/
├── *.md (11개)                    # 프로젝트 문서 (본 문서 포함)
├── Equipment List 표준 파일/       # 표준 템플릿 (2개)
├── STANDARD/                       # 표준 P&ID 도면
│   └── ECS 비방폭 1세트/          # 25+ 용량별 도면
├── ocr_test/                       # OCR 테스트 데이터 (32개)
├── output/                         # 시각화 출력 결과 (11개)
├── test_output/                    # 테스트 출력 (22+개)
│   └── symbols/                   # 심볼 추출 결과
├── ECS 예시/                       # ECS 실제 프로젝트 예시 (8개)
├── about-email-details/            # 이메일 상세 내용 (7개)
└── 2차 기술 미팅 자료 모음/        # 미팅 자료
    ├── 하이클로 예시/             # HYCHLOR 문서 (11개)
    └── 와이어프레임/              # UI 와이어프레임 (4개)
```

---

## 1. 프로젝트 문서 (루트 마크다운 파일)

| 파일명 | 용량 | 설명 |
|--------|------|------|
| `TECHLOSS_자료현황_2026-01-05.md` | 16KB | **핵심** - 프로젝트 요구사항 및 현황 |
| `TECHLOSS_서비스통합_계획.md` | 97KB | 서비스 통합 상세 계획 |
| `TECHLOSS_UI_계획.md` | 67KB | UI/UX 설계 계획 |
| `TECHLOSS_회의_프로세스.md` | 52KB | 회의 프로세스 및 기록 |
| `TECHLOSS_시각적_설명.md` | 24KB | 시스템 시각적 설명 |
| `TECHLOSS_AX_POC_개발계획.md` | 17KB | AX POC 개발 계획 |
| `TECHLOSS_자료_정리.md` | 13KB | 자료 정리 문서 |
| `TECHLOSS_미구현기능_평가.md` | 11KB | 미구현 기능 평가 |
| `ECS_vs_HYCHLOR_체크리스트_비교분석.md` | 11KB | ECS vs HYCHLOR 비교 분석 |
| `TECHCROSS_POC_개발_우선순위.md` | 3KB | 개발 우선순위 |

**총 문서 용량**: ~311KB

---

## 2. Equipment List 표준 파일

| 파일명 | 용량 |
|--------|------|
| `(Ver.25.00) TP_ECS Equipment list (2025.02.14).xlsx` | - |
| `(Ver.25.00) TP_Equipment list_HYCHLOR 2.0 (2025.03.13).xlsx` | - |

---

## 3. STANDARD - 표준 P&ID 도면

### ECS 비방폭 1세트 (25+ 파일)

| 용량 | PDF 파일 |
|------|----------|
| 150B | `ECS-150B1.1 X 1.pdf` |
| 300B | `ECS-300B2.2 X 1.pdf`, `ECS-300B1.1 X 2.pdf` |
| 500B | `ECS-500B2.2 X 1.pdf`, `ECS-500B1.1 X 2.pdf` |
| 600B | `ECS-600B2.2 X 1.pdf`, `ECS-600B1.1 X 2.pdf` |
| 750B | `ECS-750B2.2 X 1.pdf`, `ECS-750B1.1 X 2.pdf` |
| 1000B | `ECS-1000B2.2 X 1.pdf`, `ECS-1000B1.1 X 2.pdf` |
| 1500B | `ECS-1500B2.2 X 1.pdf` |
| 2000B | `ECS-2000B2.2 X 1.pdf` |
| 2500B | `ECS-2500B2.2 X 1.pdf` |
| 3000B | `ECS-3000B2.2 X 1.pdf` |
| 4000B | `ECS-4000B2.2 X 1.pdf` |

**DWG 파일**: 1개 (ECS-150B 원본)

---

## 4. ocr_test - OCR 테스트 데이터 (32개)

### 이미지 파일 (16개)
```
ecs_pnid_page_1.png ~ ecs_pnid_page_16.png
```

### OCR 결과 JSON (6개)
| 파일명 | 설명 |
|--------|------|
| `all_16pages_ocr.json` | 전체 16페이지 OCR 결과 |
| `full_ocr_result.json` | 전체 OCR 결과 |
| `page1_ocr.json` | 1페이지 개별 결과 |
| `validation_result.json` | 검증 결과 v1 |
| `validation_result_v2.json` | 검증 결과 v2 |
| `validation_result_v3.json` | 검증 결과 v3 |

### 테스트 문서 (2개)
| 파일명 | 설명 |
|--------|------|
| `BWMS_Validation_Test.xlsx` | 검증 테스트 |
| `BWMS_Checklist_Test.xlsx` | 체크리스트 테스트 |

---

## 5. output - 시각화 출력 결과 (11개)

| 파일명 | 용량 | 설명 |
|--------|------|------|
| `hychlor_page5_visualization.html` | 1.3MB | HYCHLOR 5페이지 시각화 |
| `pid_connectivity_vis.png` | 1.0MB | P&ID 연결성 시각화 |
| `hychlor_page4_visualization.html` | 879KB | HYCHLOR 4페이지 시각화 |
| `hychlor_connectivity.html` | 868KB | HYCHLOR 연결성 시각화 |
| `hychlor_yolo_ocr_combined.html` | 859KB | HYCHLOR YOLO+OCR 결합 |
| `yolo_visualization.html` | 730KB | YOLO 시각화 |
| `ecs_yolo_ocr_combined.html` | 714KB | ECS YOLO+OCR 결합 |
| `techcross_pid.png` | 522KB | TECHCROSS P&ID 이미지 |
| `yolo_preview.png` | 298KB | YOLO 미리보기 |
| `yolo_detections.svg` | 23KB | YOLO 검출 SVG |

---

## 6. test_output - 테스트 출력 (22+개)

### 페이지 이미지 (16개)
```
page_1.png ~ page_16.png (각 400~900KB)
page_5_resized.png (리사이즈 버전)
```

### 기타 출력
| 파일명 | 용량 | 설명 |
|--------|------|------|
| `line_detector_result.png` | 454KB | 라인 검출 결과 |
| `BWMS_Equipment_List.xlsx` | 6KB | 생성된 Equipment List |

### symbols/ 하위 디렉토리
| 디렉토리 | 설명 |
|----------|------|
| `final/` | 최종 심볼 |
| `full_rows/` | 전체 행 |
| `individual/` | 개별 심볼 |
| `rows/` | 행 단위 |
| `scan/` | 스캔 결과 |

**추출된 심볼**: 44개 (symbol_r00_c0.png ~ symbol_r21_c1.png)

---

## 7. ECS 예시 (실제 프로젝트)

| 파일명 | 용량 | 설명 |
|--------|------|------|
| `[PNID] REV.0 YZJ2023-1584_1585_NK_ECS1000Bx1_MIX.dwg` | 1.5MB | P&ID 원본 DWG |
| `[PNID] REV.0 YZJ2023-1584_1585_NK_ECS1000Bx1_MIX.pdf` | 702KB | P&ID PDF |
| `(Ver.25.01) Check list_P&ID_ECS-B.xlsm` | 379KB | 체크리스트 |
| `48K LPGC - General requirements of TA.doc` | 360KB | 일반 요구사항 |
| `9. Ballast Water Treatment Plaant.docx` | 48KB | BWMS 사양 |
| `BWMS Valve signal & Operation mode.xlsx` | 31KB | Valve Signal List |
| `(DEVIATION LIST) YZJ2023-1584_1585.xlsx` | 15KB | Deviation List |
| `TP_ECS Equipment list_YZJ2023-1584_1585.xlsx` | 14KB | Equipment List |

---

## 8. about-email-details - 이메일 상세 내용 (7개)

| 파일명 | 용량 | 설명 |
|--------|------|------|
| `00_공통.txt` | 18KB | 공통 사항 |
| `01_P&ID_인식_체크리스트.txt` | 14KB | P&ID 체크리스트 관련 |
| `02_Valve_Signal_List.txt` | 25KB | Valve Signal List 관련 |
| `03_Equipment_List.txt` | 18KB | Equipment List 관련 |
| `04_Deviation_List.txt` | 25KB | Deviation List 관련 |
| `05_기타.txt` | 15KB | 기타 사항 |
| `TECHCROSS_질문목록_이메일용.txt` | 5KB | 이메일용 질문 목록 |

---

## 9. 2차 기술 미팅 자료 모음

### 9.1 하이클로 예시 (11개)

| 파일명 | 용량 | 설명 |
|--------|------|------|
| `[PNID] Rev.0 H1993A...HYCHLOR 2.0-3000 2SETS_LR.dwg` | 4.7MB | P&ID 원본 DWG |
| `H1993A-98A Order specification...R02.pdf` | 1.0MB | 주문 사양서 |
| `H1993A-98A hull and electrical...R2.pdf` | 833KB | 기술 요구사항 |
| `1. 9000540K-Ballast water treatment...RevA.pdf` | 669KB | BWMS 사양 |
| `[PNID] Rev.0 H1993A...HYCHLOR 2.0-3000 2SETS_LR.pdf` | 396KB | P&ID PDF |
| `(Ver.25.01) Check list_P&ID_HYCHLOR 2.0.xlsm` | 95KB | 체크리스트 |
| `4. Deviation list of Ballast water...doc` | 84KB | Deviation List |
| `(Ver.25.01) BWMS Valve signal_H1993A...xlsx` | 24KB | Valve Signal List |
| `TP_Equipment list_H1993A...HYCHLOR 2.0.xlsx` | 20KB | Equipment List |
| `Counter flange List_H1993A...xlsx` | 14KB | Counter Flange List |

### 9.2 와이어프레임 (4개)

| 파일명 | 용량 | 설명 |
|--------|------|------|
| `기본설계팀 AI 에이전트 와이어프레임.pdf` | 890KB | 와이어프레임 PDF |
| `[PNID] (Rev.A) NACKS_NE504.pdf` | 791KB | 샘플 P&ID |
| `기본설계팀 AI 에이전트 와이어프레임.pptx` | 288KB | 와이어프레임 원본 |
| `(Ver.25.01) Check list_P&ID_ECS-B_김수민.xlsm` | 76KB | 체크리스트 샘플 |

---

## 파일 유형별 요약

| 유형 | 확장자 | 개수 | 용도 |
|------|--------|------|------|
| **P&ID 도면** | `.dwg` | 3개 | CAD 원본 |
| **P&ID 도면** | `.pdf` | 30+개 | 도면 PDF |
| **체크리스트** | `.xlsm` | 5개 | 매크로 포함 체크리스트 |
| **데이터** | `.xlsx` | 15+개 | Equipment/Valve Signal/Deviation List |
| **문서** | `.md` | 10개 | 프로젝트 문서 |
| **문서** | `.doc/.docx` | 4개 | 요구사항 문서 |
| **이미지** | `.png` | 35+개 | OCR 테스트/시각화 결과 |
| **시각화** | `.html` | 6개 | 인터랙티브 시각화 |
| **OCR 결과** | `.json` | 6개 | OCR/검증 결과 |
| **SVG** | `.svg` | 1개 | YOLO 검출 결과 |

---

## E2E 테스트 의존성

`web-ui/e2e/` 테스트에서 이 디렉토리 파일 참조:
- `ocr_test/ecs_pnid_page_*.png` - OCR 테스트용 이미지
- `STANDARD/` - 표준 P&ID 도면 테스트

---

## 정리 완료 내역

| 항목 | 상태 | 결과 |
|------|------|------|
| `Zone.Identifier` 파일들 | ✅ 삭제됨 | 57개 제거 |
| 중복 ECS 예시 | ✅ 정리됨 | 2차 미팅 폴더에서 제거 (~3MB 절감) |
| `about-email-details/` | ✅ 유지 | 이메일 상세 내용 7개 파일 (~120KB) |

---

**작성자**: Claude Code (Opus 4.5)
**버전**: v1.1 (정리 반영)
