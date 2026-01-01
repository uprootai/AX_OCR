# 테스트 데이터 픽스처

> **목적**: E2E 테스트에 필요한 테스트 데이터 정의
> **구성**: 샘플 이미지, 기대 결과, 목 데이터

---

## 목차

1. [샘플 이미지](#1-샘플-이미지)
2. [기대 결과 데이터](#2-기대-결과-데이터)
3. [API 목 데이터](#3-api-목-데이터)
4. [테스트 계정](#4-테스트-계정)
5. [데이터베이스 시드](#5-데이터베이스-시드)

---

## 1. 샘플 이미지

### 1.1 이미지 목록

| 파일명 | 경로 | 용도 | 특성 |
|--------|------|------|------|
| `page_1.png` | `/apply-company/techloss/test_output/` | BWMS P&ID 기본 | ECU, FMU 포함, 30+ 심볼 |
| `bwms_pid_001.png` | `/samples/pid/` | BWMS P&ID 복잡 | 50+ 밸브, 20+ 장비 |
| `bwms_pid_002.png` | `/samples/pid/` | BWMS P&ID 단순 | 15개 심볼 |
| `mechanical_001.png` | `/samples/mechanical/` | 기계 부품도 | 치수 20+, GD&T 5+ |
| `mechanical_002.png` | `/samples/mechanical/` | 기계 조립도 | 부품 번호 30+ |
| `electrical_001.png` | `/samples/electrical/` | 전기 패널도 | 회로 심볼 40+ |
| `lowres_001.png` | `/samples/edge/` | 저해상도 | 320x240 |
| `highres_001.png` | `/samples/edge/` | 고해상도 | 8000x6000 |
| `noisy_001.png` | `/samples/edge/` | 노이즈 이미지 | 스캔 품질 낮음 |
| `rotated_001.png` | `/samples/edge/` | 회전 이미지 | 15도 기울어짐 |
| `multipage.pdf` | `/samples/edge/` | 다중 페이지 PDF | 10페이지 |

### 1.2 이미지 규격

#### BWMS P&ID 기본 (`page_1.png`)
```yaml
Metadata:
  size: 2000x1500
  format: PNG
  color: RGB
  dpi: 150

Expected Detections:
  total: 35
  by_class:
    valve: 12
    pump: 3
    tank: 4
    filter: 2
    heat_exchanger: 1
    instrument: 8
    ecu: 1
    fmu: 1
    label: 3

Expected OCR:
  dimension_count: 0  # P&ID는 치수 없음
  tag_count: 35       # 장비 태그

Expected Valves:
  - { id: "V-101", type: "Control", actuator: "pneumatic" }
  - { id: "V-102", type: "Isolation", actuator: "manual" }
  # ... (12개)

Expected Equipment:
  - { id: "ECU-001", type: "ECU", manufacturer: "TECHCROSS" }
  - { id: "P-101", type: "PUMP", manufacturer: "unknown" }
  # ... (8개)
```

#### 기계 부품도 (`mechanical_001.png`)
```yaml
Metadata:
  size: 3000x2000
  format: PNG
  color: RGB
  dpi: 300

Expected Detections:
  total: 45
  by_class:
    dimension: 25
    tolerance: 8
    gdt_symbol: 5
    datum: 3
    surface_finish: 4

Expected OCR:
  dimensions:
    - { value: "50.00", tolerance: "+0.05/-0.02", unit: "mm" }
    - { value: "25.00", tolerance: "±0.1", unit: "mm" }
    # ... (25개)

Expected GD&T:
  - { type: "flatness", value: "0.02", datum: null }
  - { type: "position", value: "0.1", datum: "A-B" }
  # ... (5개)
```

### 1.3 엣지 케이스 이미지

#### 저해상도 (`lowres_001.png`)
```yaml
Metadata:
  size: 320x240
  format: PNG

Expected Behavior:
  detection_count: 5-10  # 많은 누락 예상
  warning: "이미지 해상도가 낮아 검출 정확도가 떨어질 수 있습니다"

Recommended Action:
  upscale: true
  target_size: 1280x960
```

#### 노이즈 이미지 (`noisy_001.png`)
```yaml
Metadata:
  size: 1500x1000
  format: PNG
  noise_level: high

Expected Behavior:
  false_positive_rate: 10-20%
  ocr_accuracy: 60-70%

Recommended Settings:
  confidence: 0.4+  # 높은 threshold
  preprocessing: denoise
```

---

## 2. 기대 결과 데이터

### 2.1 검출 결과 픽스처

#### fixture_detection_bwms.json
```json
{
  "image_id": "page_1.png",
  "model_type": "pid_class_aware",
  "settings": {
    "confidence": 0.25,
    "iou_threshold": 0.45,
    "imgsz": 1024
  },
  "expected_results": {
    "total_count": 35,
    "by_class": {
      "valve": {
        "count": 12,
        "samples": [
          {
            "id": "det_001",
            "class": "valve",
            "confidence": 0.92,
            "bbox": [100, 200, 50, 50],
            "attributes": {
              "valve_id": "V-101",
              "type": "Control"
            }
          }
        ]
      },
      "pump": {
        "count": 3,
        "samples": [
          {
            "id": "det_002",
            "class": "pump",
            "confidence": 0.88,
            "bbox": [300, 400, 80, 60]
          }
        ]
      }
    }
  }
}
```

#### fixture_detection_mechanical.json
```json
{
  "image_id": "mechanical_001.png",
  "model_type": "engineering",
  "settings": {
    "confidence": 0.25,
    "iou_threshold": 0.45,
    "imgsz": 1280
  },
  "expected_results": {
    "total_count": 45,
    "by_class": {
      "dimension": {
        "count": 25,
        "tolerance": 2
      },
      "tolerance": {
        "count": 8,
        "tolerance": 1
      },
      "gdt_symbol": {
        "count": 5,
        "tolerance": 1
      }
    }
  }
}
```

### 2.2 OCR 결과 픽스처

#### fixture_ocr_dimensions.json
```json
{
  "image_id": "mechanical_001.png",
  "ocr_engine": "edocr2",
  "expected_dimensions": [
    {
      "id": "dim_001",
      "raw_text": "50.00 +0.05/-0.02",
      "parsed": {
        "value": 50.00,
        "tolerance_upper": 0.05,
        "tolerance_lower": -0.02,
        "unit": "mm"
      },
      "confidence": 0.95,
      "bbox": [150, 300, 100, 20]
    },
    {
      "id": "dim_002",
      "raw_text": "25.00 ±0.1",
      "parsed": {
        "value": 25.00,
        "tolerance_upper": 0.1,
        "tolerance_lower": -0.1,
        "unit": "mm"
      },
      "confidence": 0.92,
      "bbox": [200, 350, 80, 20]
    }
  ],
  "expected_gdt": [
    {
      "id": "gdt_001",
      "symbol": "flatness",
      "value": 0.02,
      "datum": null,
      "confidence": 0.88
    },
    {
      "id": "gdt_002",
      "symbol": "position",
      "value": 0.1,
      "datum": ["A", "B"],
      "confidence": 0.85
    }
  ]
}
```

### 2.3 TECHCROSS 결과 픽스처

#### fixture_valve_signal.json
```json
{
  "image_id": "page_1.png",
  "workflow": "TECHCROSS 1-2",
  "expected_valves": [
    {
      "id": "V-101",
      "type": "Control",
      "category": "control_valve",
      "actuator": "pneumatic",
      "size": "2\"",
      "confidence": 0.95,
      "position": { "x": 100, "y": 200 }
    },
    {
      "id": "V-102",
      "type": "Isolation",
      "category": "isolation_valve",
      "actuator": "manual",
      "size": "3\"",
      "confidence": 0.92,
      "position": { "x": 250, "y": 300 }
    },
    {
      "id": "SV-101",
      "type": "Safety",
      "category": "safety_valve",
      "actuator": "spring",
      "size": "1\"",
      "set_pressure": "10 bar",
      "confidence": 0.88,
      "position": { "x": 400, "y": 150 }
    }
  ],
  "summary": {
    "total": 12,
    "by_category": {
      "Control": 4,
      "Isolation": 5,
      "Safety": 2,
      "Check": 1
    }
  }
}
```

#### fixture_equipment_list.json
```json
{
  "image_id": "page_1.png",
  "workflow": "TECHCROSS 1-3",
  "expected_equipment": [
    {
      "id": "ECU-001",
      "type": "ECU",
      "description": "Electrochlorination Unit",
      "manufacturer": "TECHCROSS",
      "model": "ECS-200",
      "confidence": 0.94
    },
    {
      "id": "FMU-001",
      "type": "FMU",
      "description": "Filtration Module Unit",
      "manufacturer": "TECHCROSS",
      "confidence": 0.91
    },
    {
      "id": "P-101",
      "type": "PUMP",
      "description": "Ballast Pump",
      "manufacturer": "Unknown",
      "capacity": "1000 m³/h",
      "confidence": 0.89
    }
  ],
  "summary": {
    "total": 8,
    "by_type": {
      "ECU": 1,
      "FMU": 1,
      "PUMP": 2,
      "TANK": 3,
      "FILTER": 1
    }
  }
}
```

#### fixture_checklist.json
```json
{
  "image_id": "page_1.png",
  "workflow": "TECHCROSS 1-1",
  "rule_profile": "bwms",
  "expected_results": [
    {
      "item_id": "CLK-001",
      "rule_id": "bwms_ballast_tank_vent",
      "description": "밸러스트 탱크 벤트 연결 확인",
      "category": "BWMS Specific",
      "auto_status": "Pass",
      "final_status": null,
      "details": "Tank T-101 vent connected to treatment system"
    },
    {
      "item_id": "CLK-002",
      "rule_id": "bwms_treatment_system",
      "description": "처리 시스템 연결 확인",
      "category": "BWMS Specific",
      "auto_status": "Pass",
      "final_status": null
    },
    {
      "item_id": "CLK-003",
      "rule_id": "bwms_sampling_point",
      "description": "샘플링 포인트 위치 확인",
      "category": "BWMS Specific",
      "auto_status": "Fail",
      "final_status": null,
      "details": "Sampling point not found at outlet"
    }
  ],
  "summary": {
    "total": 60,
    "pass": 45,
    "fail": 10,
    "na": 3,
    "pending": 2,
    "compliance_rate": 81.8
  }
}
```

---

## 3. API 목 데이터

### 3.1 세션 목 데이터

#### mock_sessions.json
```json
{
  "sessions": [
    {
      "id": "session_001",
      "name": "BWMS P&ID Test Session",
      "status": "completed",
      "created_at": "2025-12-31T10:00:00Z",
      "updated_at": "2025-12-31T10:15:00Z",
      "image_count": 1,
      "detection_count": 35,
      "verified_count": 30,
      "settings": {
        "confidence": 0.25,
        "model_type": "pid_class_aware"
      }
    },
    {
      "id": "session_002",
      "name": "Mechanical Drawing Test",
      "status": "processing",
      "created_at": "2025-12-31T11:00:00Z",
      "updated_at": "2025-12-31T11:05:00Z",
      "image_count": 1,
      "detection_count": 0,
      "verified_count": 0
    },
    {
      "id": "session_003",
      "name": "Empty Session",
      "status": "created",
      "created_at": "2025-12-31T12:00:00Z",
      "updated_at": "2025-12-31T12:00:00Z",
      "image_count": 0,
      "detection_count": 0,
      "verified_count": 0
    }
  ]
}
```

### 3.2 BOM 목 데이터

#### mock_bom.json
```json
{
  "session_id": "session_001",
  "bom": {
    "id": "bom_001",
    "version": "1.0",
    "created_at": "2025-12-31T10:15:00Z",
    "items": [
      {
        "id": "bom_item_001",
        "detection_id": "det_001",
        "part_number": "V-101",
        "description": "Control Valve, 2\", Pneumatic",
        "quantity": 1,
        "unit": "EA",
        "category": "Valve",
        "status": "verified",
        "confidence": 0.95,
        "verified_by": "user_001",
        "verified_at": "2025-12-31T10:10:00Z"
      },
      {
        "id": "bom_item_002",
        "detection_id": "det_002",
        "part_number": "P-101",
        "description": "Centrifugal Pump, 1000 m³/h",
        "quantity": 1,
        "unit": "EA",
        "category": "Pump",
        "status": "pending",
        "confidence": 0.88
      }
    ],
    "summary": {
      "total_items": 35,
      "verified": 30,
      "pending": 4,
      "rejected": 1,
      "categories": {
        "Valve": 12,
        "Pump": 3,
        "Tank": 4,
        "Instrument": 8,
        "Other": 8
      }
    }
  }
}
```

### 3.3 에러 응답 목 데이터

#### mock_errors.json
```json
{
  "errors": {
    "400_bad_request": {
      "status_code": 400,
      "detail": "Invalid request body",
      "errors": [
        {
          "loc": ["body", "confidence"],
          "msg": "value is not a valid float",
          "type": "type_error.float"
        }
      ]
    },
    "404_not_found": {
      "status_code": 404,
      "detail": "Session not found",
      "resource_type": "session",
      "resource_id": "nonexistent_id"
    },
    "422_validation_error": {
      "status_code": 422,
      "detail": [
        {
          "loc": ["body", "iou_threshold"],
          "msg": "ensure this value is less than or equal to 0.95",
          "type": "value_error.number.not_le",
          "ctx": { "limit_value": 0.95 }
        }
      ]
    },
    "500_internal_error": {
      "status_code": 500,
      "detail": "Internal server error",
      "error_id": "ERR-20251231-001"
    }
  }
}
```

---

## 4. 테스트 계정

### 4.1 사용자 계정

| 계정 ID | 역할 | 용도 | 권한 |
|---------|------|------|------|
| `test_user_01` | 일반 사용자 | 기본 기능 테스트 | 읽기/쓰기/삭제 |
| `test_user_02` | 일반 사용자 | 동시성 테스트 | 읽기/쓰기 |
| `test_admin_01` | 관리자 | 관리 기능 테스트 | 모든 권한 |
| `test_readonly` | 읽기 전용 | 권한 테스트 | 읽기만 |

### 4.2 계정 픽스처

#### fixture_users.json
```json
{
  "users": [
    {
      "id": "test_user_01",
      "username": "testuser1",
      "email": "test1@example.com",
      "role": "user",
      "preferences": {
        "default_confidence": 0.25,
        "default_model_type": "pid_class_aware",
        "language": "ko"
      }
    },
    {
      "id": "test_admin_01",
      "username": "testadmin",
      "email": "admin@example.com",
      "role": "admin",
      "permissions": ["read", "write", "delete", "admin"]
    }
  ]
}
```

---

## 5. 데이터베이스 시드

### 5.1 시드 스크립트

#### seed_test_data.sql
```sql
-- 테스트 세션 생성
INSERT INTO sessions (id, name, status, created_at) VALUES
  ('session_001', 'BWMS P&ID Test', 'completed', '2025-12-31 10:00:00'),
  ('session_002', 'Mechanical Drawing', 'processing', '2025-12-31 11:00:00'),
  ('session_003', 'Empty Session', 'created', '2025-12-31 12:00:00');

-- 테스트 이미지 생성
INSERT INTO images (id, session_id, filename, path, width, height) VALUES
  ('img_001', 'session_001', 'page_1.png', '/uploads/page_1.png', 2000, 1500);

-- 테스트 검출 결과 생성
INSERT INTO detections (id, image_id, class, confidence, x, y, width, height) VALUES
  ('det_001', 'img_001', 'valve', 0.92, 100, 200, 50, 50),
  ('det_002', 'img_001', 'pump', 0.88, 300, 400, 80, 60);
```

### 5.2 시드 데이터 초기화

#### reset_test_data.sh
```bash
#!/bin/bash
# 테스트 데이터베이스 초기화 스크립트

# 데이터베이스 클리어
psql -d test_db -c "TRUNCATE sessions, images, detections, bom_items CASCADE;"

# 시드 데이터 로드
psql -d test_db -f seed_test_data.sql

# 테스트 이미지 복사
cp -r /samples/* /test_uploads/

echo "Test data reset complete"
```

---

## 6. 픽스처 사용 가이드

### 6.1 Playwright에서 사용

```typescript
// e2e/fixtures/index.ts
import detectionFixture from './fixture_detection_bwms.json';
import bomFixture from './fixture_bom.json';
import sessionFixture from './fixture_sessions.json';

export const fixtures = {
  detection: detectionFixture,
  bom: bomFixture,
  sessions: sessionFixture
};

// 테스트에서 사용
import { test, expect } from '@playwright/test';
import { fixtures } from './fixtures';

test('검출 결과 검증', async ({ page }) => {
  const expected = fixtures.detection.expected_results;

  // 검출 실행
  await page.click('[data-testid="run-detection"]');

  // 결과 검증
  const detections = await page.locator('[data-testid="detection-row"]').count();
  expect(detections).toBeGreaterThanOrEqual(expected.total_count - 5);
  expect(detections).toBeLessThanOrEqual(expected.total_count + 5);
});
```

### 6.2 API 목킹

```typescript
// e2e/mocks/api.ts
import { Page } from '@playwright/test';
import mockSessions from '../fixtures/mock_sessions.json';
import mockErrors from '../fixtures/mock_errors.json';

export async function mockSessionsAPI(page: Page) {
  await page.route('**/api/v1/sessions', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockSessions.sessions)
    });
  });
}

export async function mockErrorResponse(page: Page, errorType: string) {
  const error = mockErrors.errors[errorType];
  await page.route('**/api/v1/**', async route => {
    await route.fulfill({
      status: error.status_code,
      contentType: 'application/json',
      body: JSON.stringify({ detail: error.detail })
    });
  });
}
```

### 6.3 비주얼 비교

```typescript
// e2e/visual/comparison.ts
import { expect, Page } from '@playwright/test';

export async function compareDetectionOverlay(page: Page, expectedImagePath: string) {
  // 현재 페이지 스크린샷
  const screenshot = await page.screenshot({
    selector: '[data-testid="detection-canvas"]'
  });

  // 기대 이미지와 비교
  expect(screenshot).toMatchSnapshot(expectedImagePath, {
    threshold: 0.1  // 10% 허용 오차
  });
}
```

---

## 7. 관련 문서

- [08-test-matrix.md](./08-test-matrix.md) - 테스트 매트릭스
- [05-edge-cases.md](./05-edge-cases.md) - 엣지 케이스 테스트
- [06-integration.md](./06-integration.md) - 통합 테스트
