# TECHCROSS Phase 1: 즉시 개발 가능한 작업

> 예상 소요 시간: 1일
> 난이도: ⭐⭐ (중하)
> 의존성: 없음 (바로 시작 가능)

---

## 작업 1: BWMS 장비 태그 패턴 인식

### 목표
OCR로 읽은 텍스트에서 BWMS 전용 장비 태그(ECU-001, HGU-002 등)를 자동 인식

### 구현 위치
`models/pid-analyzer-api/api_server.py`에 함수 추가

### 상세 구현

```python
import re
from typing import List, Dict

# BWMS 장비 코드 및 설명
BWMS_EQUIPMENT = {
    'ECU': {
        'pattern': r'ECU[-_]?\d{3}',
        'name_ko': '전기분해 유닛',
        'name_en': 'Electrolyzer Cell Unit',
        'description': '해수를 전기분해하여 차아염소산나트륨(NaOCl) 생성'
    },
    'HGU': {
        'pattern': r'HGU[-_]?\d{3}',
        'name_ko': '수소가스 유닛',
        'name_en': 'Hydrogen Gas Unit',
        'description': '전기분해 과정에서 발생하는 수소가스 처리'
    },
    'FMU': {
        'pattern': r'FMU[-_]?\d{3}',
        'name_ko': '필터 모듈',
        'name_en': 'Filter Module Unit',
        'description': '해수 내 부유물질 제거'
    },
    'ANU': {
        'pattern': r'ANU[-_]?\d{3}',
        'name_ko': '중화 유닛',
        'name_en': 'Active Neutralization Unit',
        'description': '처리수 중화 처리'
    },
    'NIU': {
        'pattern': r'NIU[-_]?\d{3}',
        'name_ko': '중화 주입 유닛',
        'name_en': 'Neutralization Injection Unit',
        'description': '중화제 주입'
    },
    'TSU': {
        'pattern': r'TSU[-_]?\d{3}',
        'name_ko': '잔류 용액 유닛',
        'name_en': 'Total residual Solution Unit',
        'description': 'TRO(잔류산화제) 측정'
    },
    'DTS': {
        'pattern': r'DTS[-_]?\d{3}',
        'name_ko': 'TRO 투여 스테이션',
        'name_en': 'Dosing TRO Station',
        'description': 'TRO 투여량 조절'
    },
    'GDS': {
        'pattern': r'GDS[-_]?\d{3}',
        'name_ko': '가스 희석 시스템',
        'name_en': 'Gas Dilution System',
        'description': '수소가스 안전 희석'
    },
    'EWU': {
        'pattern': r'EWU[-_]?\d{3}',
        'name_ko': '전해질 세척 유닛',
        'name_en': 'Electrolyte Washing Unit',
        'description': '전극 세척'
    },
    'APU': {
        'pattern': r'APU[-_]?\d{3}',
        'name_ko': '자동 퍼지 유닛',
        'name_en': 'Automatic Purge Unit',
        'description': '시스템 자동 퍼지'
    },
    'DMU': {
        'pattern': r'DMU[-_]?\d{3}',
        'name_ko': '직접 혼합 유닛',
        'name_en': 'Direct Mix Unit',
        'description': '처리수 직접 혼합'
    },
    'CPC': {
        'pattern': r'CPC[-_]?\d{3}',
        'name_ko': '제어 패널',
        'name_en': 'Control Panel Cabinet',
        'description': '시스템 제어 패널'
    },
}


def detect_bwms_equipment(ocr_results: List[Dict]) -> List[Dict]:
    """
    OCR 결과에서 BWMS 장비 태그를 검출합니다.

    Args:
        ocr_results: OCR 결과 리스트 [{'text': 'ECU-001', 'bbox': [...], ...}, ...]

    Returns:
        검출된 BWMS 장비 리스트
        [
            {
                'tag': 'ECU-001',
                'type': 'ECU',
                'name_ko': '전기분해 유닛',
                'name_en': 'Electrolyzer Cell Unit',
                'description': '...',
                'bbox': [...],
                'confidence': 0.95,
                'maker_supply': False  # '*' 마크 여부
            },
            ...
        ]
    """
    equipment_list = []
    seen_tags = set()  # 중복 방지

    for ocr_item in ocr_results:
        text = ocr_item.get('text', '').strip().upper()

        for equip_type, info in BWMS_EQUIPMENT.items():
            if re.match(info['pattern'], text, re.IGNORECASE):
                if text not in seen_tags:
                    seen_tags.add(text)

                    # '*' 마크 확인 (MAKER SUPPLY)
                    maker_supply = '*' in ocr_item.get('text', '')

                    equipment_list.append({
                        'tag': text,
                        'type': equip_type,
                        'name_ko': info['name_ko'],
                        'name_en': info['name_en'],
                        'description': info['description'],
                        'bbox': ocr_item.get('bbox'),
                        'confidence': ocr_item.get('confidence', 0.0),
                        'maker_supply': maker_supply
                    })
                break

    # 태그 번호순 정렬
    equipment_list.sort(key=lambda x: x['tag'])
    return equipment_list


def get_bwms_equipment_summary(equipment_list: List[Dict]) -> Dict:
    """장비 요약 통계 생성"""
    summary = {
        'total_count': len(equipment_list),
        'by_type': {},
        'maker_supply_count': 0
    }

    for equip in equipment_list:
        equip_type = equip['type']
        summary['by_type'][equip_type] = summary['by_type'].get(equip_type, 0) + 1
        if equip.get('maker_supply'):
            summary['maker_supply_count'] += 1

    return summary
```

### API 엔드포인트 추가

```python
@app.post("/api/v1/detect-bwms-equipment")
async def detect_bwms_equipment_endpoint(
    file: UploadFile = File(...),
):
    """BWMS 장비 태그 검출 API"""
    # 1. 이미지 로드
    image = load_image(file)

    # 2. OCR 수행 (기존 OCR Ensemble 활용)
    ocr_results = await call_ocr_ensemble(image)

    # 3. BWMS 장비 검출
    equipment = detect_bwms_equipment(ocr_results)
    summary = get_bwms_equipment_summary(equipment)

    return {
        'success': True,
        'data': {
            'equipment': equipment,
            'summary': summary
        }
    }
```

### 테스트 케이스

```python
def test_detect_bwms_equipment():
    # 테스트 OCR 결과
    ocr_results = [
        {'text': 'ECU-001', 'confidence': 0.95},
        {'text': 'FMU-001*', 'confidence': 0.92},  # MAKER SUPPLY
        {'text': 'HGU-002', 'confidence': 0.88},
        {'text': 'PUMP-001', 'confidence': 0.90},  # 일반 장비 (제외됨)
    ]

    equipment = detect_bwms_equipment(ocr_results)

    assert len(equipment) == 3  # BWMS 장비만
    assert equipment[0]['tag'] == 'ECU-001'
    assert equipment[1]['maker_supply'] == True  # FMU-001*
```

---

## 작업 2: Equipment List Excel 출력

### 목표
검출된 장비 목록을 Excel 파일로 출력

### 구현

```python
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from datetime import datetime


def generate_equipment_list_excel(
    equipment_list: List[Dict],
    project_info: Dict,
    output_path: str
) -> str:
    """
    Equipment List Excel 파일 생성

    Args:
        equipment_list: 장비 목록
        project_info: 프로젝트 정보 {'name': '...', 'drawing_no': '...', ...}
        output_path: 출력 파일 경로

    Returns:
        생성된 파일 경로
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Equipment List"

    # 스타일 정의
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font_white = Font(bold=True, size=11, color="FFFFFF")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # 프로젝트 정보 헤더
    ws['A1'] = "TECHCROSS BWMS Equipment List"
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:F1')

    ws['A2'] = f"Project: {project_info.get('name', 'N/A')}"
    ws['A3'] = f"Drawing No: {project_info.get('drawing_no', 'N/A')}"
    ws['A4'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # 데이터 테이블 헤더 (6행부터)
    headers = ['No', 'Tag', 'Type', 'Name (Korean)', 'Name (English)', 'Maker Supply']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col, value=header)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = border

    # 데이터 입력
    for i, equip in enumerate(equipment_list, 1):
        row = 6 + i
        ws.cell(row=row, column=1, value=i).border = border
        ws.cell(row=row, column=2, value=equip['tag']).border = border
        ws.cell(row=row, column=3, value=equip['type']).border = border
        ws.cell(row=row, column=4, value=equip['name_ko']).border = border
        ws.cell(row=row, column=5, value=equip['name_en']).border = border
        ws.cell(row=row, column=6, value='*' if equip.get('maker_supply') else '').border = border

    # 열 너비 조정
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 8
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 25
    ws.column_dimensions['F'].width = 12

    # 요약 정보
    summary_row = 6 + len(equipment_list) + 2
    ws.cell(row=summary_row, column=1, value="Summary:").font = Font(bold=True)
    ws.cell(row=summary_row + 1, column=1, value=f"Total Equipment: {len(equipment_list)}")
    ws.cell(row=summary_row + 2, column=1,
            value=f"Maker Supply: {sum(1 for e in equipment_list if e.get('maker_supply'))}")

    wb.save(output_path)
    return output_path
```

### API 엔드포인트

```python
@app.post("/api/v1/generate-equipment-list")
async def generate_equipment_list_endpoint(
    file: UploadFile = File(...),
    project_name: str = Form(default="Unknown"),
    drawing_no: str = Form(default="N/A"),
):
    """Equipment List Excel 생성 API"""
    # 1. BWMS 장비 검출
    equipment = await detect_bwms_equipment_from_image(file)

    # 2. Excel 생성
    output_path = f"/tmp/equipment_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    generate_equipment_list_excel(
        equipment,
        {'name': project_name, 'drawing_no': drawing_no},
        output_path
    )

    # 3. 파일 반환
    return FileResponse(
        output_path,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=f"Equipment_List_{drawing_no}.xlsx"
    )
```

---

## 체크리스트

- [ ] BWMS 장비 패턴 인식 함수 구현
- [ ] PID Analyzer API에 엔드포인트 추가
- [ ] Equipment List Excel 생성 함수 구현
- [ ] 단위 테스트 작성
- [ ] 샘플 P&ID로 테스트
- [ ] 프론트엔드 연동 (선택)

---

## 예상 결과물

1. **API 엔드포인트**:
   - `POST /api/v1/detect-bwms-equipment`
   - `POST /api/v1/generate-equipment-list`

2. **Excel 파일**:
   ```
   Equipment_List_YZJ2023-1584.xlsx
   ├── Sheet: Equipment List
   │   ├── 프로젝트 정보
   │   ├── 장비 테이블 (No, Tag, Type, Name, Maker Supply)
   │   └── 요약 (Total, Maker Supply 수)
   ```

---

## 다음 단계

Phase 1 완료 후 → Phase 2: Valve Signal List 자동 생성
