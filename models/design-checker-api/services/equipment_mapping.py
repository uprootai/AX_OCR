"""
Equipment Mapping - 규칙 장비명 ↔ OCR 태그 매핑
TECHCROSS BWMS 체크리스트 규칙의 equipment 필드를 OCR 태그와 연결

예시:
- 규칙: "Check Valve" → OCR 태그: ["BWV", "CV"]
- 규칙: "Flow Control Valve" → OCR 태그: ["FCV"]
- 규칙: "Ballast Pump" → OCR 태그: ["BP", "BALLAST PUMP"]
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EquipmentMatch:
    """장비 매칭 결과"""
    rule_equipment: str  # 규칙의 equipment 값
    matched_tags: list[str]  # 매칭된 OCR 태그들
    match_type: str  # direct, alias, pattern
    confidence: float  # 매칭 신뢰도


# ============================================================
# 장비명 → OCR 태그 매핑 테이블
# ============================================================
EQUIPMENT_TO_TAGS = {
    # ============================================================
    # Valve 타입
    # ============================================================
    "Check Valve": {
        "tags": ["BWV", "CV", "CHK"],
        "patterns": [r"\bBWV[-_]?\d+\b", r"\bCV[-_]?\d+\b", r"\bCHK[-_]?\d+\b"],
        "description": "역류방지밸브",
    },
    "Flow Control Valve": {
        "tags": ["FCV"],
        "patterns": [r"\bFCV[-_]?\d+\b"],
        "description": "유량조절밸브",
    },
    "Butterfly Valve": {
        "tags": ["BFV", "BV"],
        "patterns": [r"\bBFV[-_]?\d+\b", r"\bBV[-_]?\d+\b"],
        "description": "버터플라이밸브",
    },
    "Ball Valve": {
        "tags": ["BLV", "BALL"],
        "patterns": [r"\bBLV[-_]?\d+\b", r"\bBALL[-_]?\d+\b"],
        "description": "볼밸브",
    },
    "Gate Valve": {
        "tags": ["GV", "GATE"],
        "patterns": [r"\bGV[-_]?\d+\b", r"\bGATE[-_]?\d+\b"],
        "description": "게이트밸브",
    },
    "Globe Valve": {
        "tags": ["GLV"],
        "patterns": [r"\bGLV[-_]?\d+\b"],
        "description": "글로브밸브",
    },
    "Relief Valve": {
        "tags": ["RV", "PRV", "SRV"],
        "patterns": [r"\bRV[-_]?\d+\b", r"\bPRV[-_]?\d+\b", r"\bSRV[-_]?\d+\b"],
        "description": "릴리프밸브",
    },
    "Solenoid Valve": {
        "tags": ["SOV", "SV"],
        "patterns": [r"\bSOV[-_]?\d+\b", r"\bSV[-_]?\d+\b"],
        "description": "솔레노이드밸브",
    },
    "Valve": {
        "tags": ["BWV", "FCV", "BFV", "GV", "GLV", "RV", "SOV", "CV"],
        "patterns": [r"\b[A-Z]{2,3}V[-_]?\d+\b"],
        "description": "일반 밸브 (모든 밸브 유형)",
    },

    # ============================================================
    # TECHCROSS BWMS 주요 장비
    # ============================================================
    "ECU": {
        "tags": ["ECU"],
        "patterns": [r"\bECU[-_\s]?\d*[A-Z]?\b", r"\bECU\s*\d+B\b"],
        "description": "Electrolysis Chamber Unit (ECS 전용)",
        "product_type": "ECS",
    },
    "HGU": {
        "tags": ["HGU"],
        "patterns": [r"\bHGU[-_]?\d*\b"],
        "description": "Hypochlorite Generation Unit (HYCHLOR 전용)",
        "product_type": "HYCHLOR",
    },
    "PRU": {
        "tags": ["PRU"],
        "patterns": [r"\bPRU[-_\s]?\d*[A-Z]?\b"],
        "description": "Power Rectifier Unit (ECS 전용)",
        "product_type": "ECS",
    },
    "FMU": {
        "tags": ["FMU"],
        "patterns": [r"\bFMU[-_\s]?\d*[A-Z]?\b"],
        "description": "Flow Meter Unit",
    },
    "ANU": {
        "tags": ["ANU"],
        "patterns": [r"\bANU[-_]?\d*[A-Z]?\b"],
        "description": "Automatic Neutralization Unit",
    },
    "TSU": {
        "tags": ["TSU"],
        "patterns": [r"\bTSU[-_]?[A-Z0-9]*\b"],
        "description": "TRO Sensing Unit",
    },
    "APU": {
        "tags": ["APU"],
        "patterns": [r"\bAPU[-_\s]?\d*\b", r"NO\.\d+\s*APU"],
        "description": "Auto Pump Unit",
    },
    "GDS": {
        "tags": ["GDS"],
        "patterns": [r"\bGDS[-_]?\d*\b"],
        "description": "Gas Detection System",
    },
    "DMU": {
        "tags": ["DMU"],
        "patterns": [r"\bDMU[-_]?\d*\b"],
        "description": "Dosing & Mixing Unit (HYCHLOR 전용)",
        "product_type": "HYCHLOR",
    },
    "NIU": {
        "tags": ["NIU"],
        "patterns": [r"\bNIU[-_]?\d*\b"],
        "description": "Neutralization Injection Unit (HYCHLOR 전용)",
        "product_type": "HYCHLOR",
    },
    "CPC": {
        "tags": ["CPC"],
        "patterns": [r"\bCPC[-_]?\d*\b"],
        "description": "Control PC",
    },
    "EWU": {
        "tags": ["EWU"],
        "patterns": [r"\bEWU[-_]?\d*\b"],
        "description": "Emergency Wash Unit",
    },
    "FTS": {
        "tags": ["FTS"],
        "patterns": [r"\bFTS[-_]?\d*\b"],
        "description": "Flow Transmitter System",
    },
    "CSU": {
        "tags": ["CSU"],
        "patterns": [r"\bCSU[-_]?\d*\b"],
        "description": "Control Signal Unit",
    },
    "PCU": {
        "tags": ["PCU"],
        "patterns": [r"\bPCU[-_]?\d*\b"],
        "description": "Pump Control Unit",
    },
    "PDE": {
        "tags": ["PDE"],
        "patterns": [r"\bPDE[-_]?\d*[A-Z]?\b"],
        "description": "Power Distribution Equipment",
    },

    # ============================================================
    # Pump 타입
    # ============================================================
    "Ballast Pump": {
        "tags": ["BP", "BALLAST PUMP", "B.PUMP"],
        "patterns": [r"\bBP[-_]?\d*\b", r"\bBALLAST\s*PUMP\b", r"\bB\.?PUMP\b"],
        "description": "밸러스트 펌프",
    },
    "Stripping Pump": {
        "tags": ["SP", "STRIP PUMP", "STRIPPING PUMP"],
        "patterns": [r"\bSP[-_]?\d*\b", r"\bSTRIP(?:PING)?\s*PUMP\b"],
        "description": "스트리핑 펌프",
    },
    "Mixing S.W.Pump": {
        "tags": ["MIXING"],
        "patterns": [r"\bMIXING\s*S\.?W\.?\s*PUMP\b"],
        "description": "Mixing Seawater Pump (ECS 전용)",
        "product_type": "ECS",
    },
    "Seawater Pump": {
        "tags": ["SWP", "S.W.PUMP"],
        "patterns": [r"\bSWP[-_]?\d*\b", r"\bS\.?W\.?\s*PUMP\b"],
        "description": "해수 펌프",
    },

    # ============================================================
    # Sensor/Transmitter 타입
    # ============================================================
    "Pressure Transmitter": {
        "tags": ["PT"],
        "patterns": [r"\bPT[-_]?\d+\b"],
        "description": "압력 트랜스미터",
    },
    "Flow Transmitter": {
        "tags": ["FT"],
        "patterns": [r"\bFT[-_]?\d+\b"],
        "description": "유량 트랜스미터",
    },
    "Temperature Transmitter": {
        "tags": ["TT"],
        "patterns": [r"\bTT[-_]?\d+\b"],
        "description": "온도 트랜스미터",
    },
    "Level Transmitter": {
        "tags": ["LT"],
        "patterns": [r"\bLT[-_]?\d+\b"],
        "description": "레벨 트랜스미터",
    },
    "Flow Switch": {
        "tags": ["FS"],
        "patterns": [r"\bFS[-_]?\d+\b"],
        "description": "유량 스위치",
    },
    "Pressure Switch": {
        "tags": ["PS"],
        "patterns": [r"\bPS[-_]?\d+\b"],
        "description": "압력 스위치",
    },

    # ============================================================
    # Tank 타입 (확장)
    # ============================================================
    "T.S.TK": {
        "tags": ["TSTK", "T.S.TK", "TOP SIDE TK", "TOPSIDE TK"],
        "patterns": [r"\bT\.?S\.?\s*TK\b", r"\bTOP\s*SIDE\s*T(?:AN)?K\b", r"\bTOPSIDE\s*T(?:AN)?K\b"],
        "description": "Top Side Tank",
    },
    "W.B.TK": {
        "tags": ["WBTK", "W.B.TK", "WATER BALLAST TK", "WBT", "BALLAST TK"],
        "patterns": [
            r"\bW\.?B\.?\s*TK\b", r"\bWBT[-_]?\d*\b",
            r"\bWATER\s*BALLAST\s*T(?:AN)?K\b", r"\bBALLAST\s*T(?:AN)?K\b",
            r"\bNO\.?\s*\d+\s*W\.?B\.?\s*TK\b",  # NO.1 W.B.TK
        ],
        "description": "Water Ballast Tank",
    },
    "Slop TK": {
        "tags": ["SLOP TK", "SLOP TANK", "SLOP"],
        "patterns": [r"\bSLOP\s*T(?:AN)?K\b", r"\bSLOP\b"],
        "description": "슬롭 탱크",
    },
    "Grey water TK": {
        "tags": ["GREY WATER TK", "GREY TK", "GRAY WATER TK"],
        "patterns": [r"\bGR[EA]Y\s*(?:WATER\s*)?T(?:AN)?K\b"],
        "description": "그레이워터 탱크",
    },
    "Fore Peak TK": {
        "tags": ["FORE PEAK TK", "F.P.TK", "FPT"],
        "patterns": [r"\bFORE\s*PEAK\s*T(?:AN)?K\b", r"\bF\.?P\.?\s*TK\b", r"\bFPT\b"],
        "description": "선수 피크 탱크",
    },
    "Aft Peak TK": {
        "tags": ["AFT PEAK TK", "A.P.TK", "APT"],
        "patterns": [r"\bAFT\s*PEAK\s*T(?:AN)?K\b", r"\bA\.?P\.?\s*TK\b", r"\bAPT\b"],
        "description": "선미 피크 탱크",
    },
    "F.O.TK": {
        "tags": ["F.O.TK", "FUEL OIL TK", "FOT"],
        "patterns": [r"\bF\.?O\.?\s*TK\b", r"\bFUEL\s*OIL\s*T(?:AN)?K\b", r"\bFOT[-_]?\d*\b"],
        "description": "연료유 탱크",
    },
    "D.O.TK": {
        "tags": ["D.O.TK", "DIESEL OIL TK", "DOT"],
        "patterns": [r"\bD\.?O\.?\s*TK\b", r"\bDIESEL\s*(?:OIL\s*)?T(?:AN)?K\b", r"\bDOT[-_]?\d*\b"],
        "description": "디젤유 탱크",
    },
    "F.W.TK": {
        "tags": ["F.W.TK", "FRESH WATER TK", "FWT"],
        "patterns": [r"\bF\.?W\.?\s*TK\b", r"\bFRESH\s*WATER\s*T(?:AN)?K\b", r"\bFWT[-_]?\d*\b"],
        "description": "청수 탱크",
    },
    "D.B.TK": {
        "tags": ["D.B.TK", "DOUBLE BOTTOM TK", "DBT"],
        "patterns": [r"\bD\.?B\.?\s*TK\b", r"\bDOUBLE\s*BOTTOM\s*T(?:AN)?K\b", r"\bDBT[-_]?\d*\b"],
        "description": "이중저 탱크",
    },
    "Cargo TK": {
        "tags": ["CARGO TK", "C.O.TK", "COT"],
        "patterns": [r"\bCARGO\s*T(?:AN)?K\b", r"\bC\.?O\.?\s*TK\b", r"\bCOT[-_]?\d*\b"],
        "description": "화물 탱크",
    },
    "Settling TK": {
        "tags": ["SETTLING TK", "SETT TK"],
        "patterns": [r"\bSETTL(?:ING)?\s*T(?:AN)?K\b"],
        "description": "침전 탱크",
    },
    "Service TK": {
        "tags": ["SERVICE TK", "SERV TK"],
        "patterns": [r"\bSERV(?:ICE)?\s*T(?:AN)?K\b"],
        "description": "서비스 탱크",
    },
    "Storage TK": {
        "tags": ["STORAGE TK", "STOR TK"],
        "patterns": [r"\bSTOR(?:AGE)?\s*T(?:AN)?K\b"],
        "description": "저장 탱크",
    },
    "Holding TK": {
        "tags": ["HOLDING TK", "HOLD TK"],
        "patterns": [r"\bHOLD(?:ING)?\s*T(?:AN)?K\b"],
        "description": "홀딩 탱크",
    },
    "Expansion TK": {
        "tags": ["EXPANSION TK", "EXP TK"],
        "patterns": [r"\bEXP(?:ANSION)?\s*T(?:AN)?K\b"],
        "description": "팽창 탱크",
    },
    "Cofferdam": {
        "tags": ["COFFERDAM", "C/D"],
        "patterns": [r"\bCOFFERDAM\b", r"\bC/?D\b"],
        "description": "코퍼댐",
    },
    "Void Space": {
        "tags": ["VOID", "VOID SPACE"],
        "patterns": [r"\bVOID\s*(?:SPACE)?\b"],
        "description": "보이드 스페이스",
    },

    # ============================================================
    # Line/Pipe 타입 (확장)
    # ============================================================
    "BWMS Inlet": {
        "tags": ["BWMS INLET", "INLET", "BWTS INLET"],
        "patterns": [r"\bBW[MT]S\s*INLET\b", r"\bINLET\b", r"\bTO\s*BWMS\b"],
        "description": "BWMS 입구",
    },
    "BWMS Outlet": {
        "tags": ["BWMS OUTLET", "OUTLET", "BWTS OUTLET"],
        "patterns": [r"\bBW[MT]S\s*OUTLET\b", r"\bOUTLET\b", r"\bFROM\s*BWMS\b"],
        "description": "BWMS 출구",
    },
    "Overflow Line": {
        "tags": ["OVERFLOW", "O/F LINE", "O/F", "OVFL"],
        "patterns": [r"\bOVER\s*FLOW\b", r"\bO/?F\s*(?:LINE)?\b", r"\bOVFL\b"],
        "description": "오버플로우 라인",
    },
    "Air Line": {
        "tags": ["AIR LINE", "AIR PIPE", "AIR"],
        "patterns": [r"\bAIR\s*(?:LINE|PIPE)\b", r"\bAIR\s*VENT\b"],
        "description": "에어 라인",
    },
    "FW Line": {
        "tags": ["FW LINE", "FRESH WATER LINE", "F.W.LINE"],
        "patterns": [r"\bF\.?W\.?\s*LINE\b", r"\bFRESH\s*WATER\s*(?:LINE)?\b"],
        "description": "청수 라인",
    },
    "SW Line": {
        "tags": ["SW LINE", "SEA WATER LINE", "S.W.LINE"],
        "patterns": [r"\bS\.?W\.?\s*LINE\b", r"\bSEA\s*WATER\s*(?:LINE)?\b"],
        "description": "해수 라인",
    },
    "BW Line": {
        "tags": ["BW LINE", "BALLAST WATER LINE", "B.W.LINE"],
        "patterns": [r"\bB\.?W\.?\s*LINE\b", r"\bBALLAST\s*(?:WATER\s*)?LINE\b"],
        "description": "밸러스트 라인",
    },
    "Vent Line": {
        "tags": ["VENT LINE", "VENT", "V/L"],
        "patterns": [r"\bVENT\s*(?:LINE|PIPE)?\b", r"\bV/?L\b"],
        "description": "벤트 라인",
    },
    "Drain Line": {
        "tags": ["DRAIN LINE", "DRAIN", "D/L"],
        "patterns": [r"\bDRAIN\s*(?:LINE|PIPE)?\b", r"\bD/?L\b"],
        "description": "드레인 라인",
    },
    "Suction Line": {
        "tags": ["SUCTION LINE", "SUCTION", "S/L"],
        "patterns": [r"\bSUCT(?:ION)?\s*(?:LINE|PIPE)?\b", r"\bS/?L\b"],
        "description": "흡입 라인",
    },
    "Discharge Line": {
        "tags": ["DISCHARGE LINE", "DISCHARGE", "D/C LINE"],
        "patterns": [r"\bDISCH(?:ARGE)?\s*(?:LINE|PIPE)?\b", r"\bD/?C\s*LINE\b"],
        "description": "토출 라인",
    },
    "Return Line": {
        "tags": ["RETURN LINE", "RETURN", "R/L"],
        "patterns": [r"\bRETURN\s*(?:LINE|PIPE)?\b", r"\bR/?L\b"],
        "description": "리턴 라인",
    },
    "Supply Line": {
        "tags": ["SUPPLY LINE", "SUPPLY", "SUP LINE"],
        "patterns": [r"\bSUPPLY\s*(?:LINE|PIPE)?\b"],
        "description": "공급 라인",
    },
    "Sampling Line": {
        "tags": ["SAMPLING LINE", "SAMPLING", "SAMPLE LINE"],
        "patterns": [r"\bSAMPL(?:ING|E)?\s*(?:LINE|PIPE)?\b"],
        "description": "샘플링 라인",
    },
    "By-pass Line": {
        "tags": ["BY-PASS", "BYPASS", "B/P LINE"],
        "patterns": [r"\bBY[-\s]?PASS\s*(?:LINE|PIPE)?\b", r"\bB/?P\s*LINE\b"],
        "description": "바이패스 라인",
    },
    "Cross Connection": {
        "tags": ["CROSS CONNECTION", "X-CONN", "CROSS CONN"],
        "patterns": [r"\bCROSS\s*CONN(?:ECTION)?\b", r"\bX[-\s]?CONN\b"],
        "description": "크로스 커넥션",
    },
    "Branch Pipe": {
        "tags": ["BRANCH", "BRANCH PIPE", "BR.PIPE"],
        "patterns": [r"\bBRANCH\s*(?:PIPE|LINE)?\b", r"\bBR\.?\s*PIPE\b"],
        "description": "지관",
    },
    "Manifold": {
        "tags": ["MANIFOLD", "M/F"],
        "patterns": [r"\bMANIFOLD\b", r"\bM/?F\b"],
        "description": "매니폴드",
    },
    "Header": {
        "tags": ["HEADER", "HDR"],
        "patterns": [r"\bHEADER\b", r"\bHDR\b"],
        "description": "헤더",
    },
    "Sounding Pipe": {
        "tags": ["SOUNDING PIPE", "S/P", "SOUND PIPE"],
        "patterns": [r"\bSOUND(?:ING)?\s*PIPE\b", r"\bS/?P\b"],
        "description": "사운딩 파이프",
    },
    "Filling Pipe": {
        "tags": ["FILLING PIPE", "FILL PIPE"],
        "patterns": [r"\bFILL(?:ING)?\s*PIPE\b"],
        "description": "충전 파이프",
    },

    # ============================================================
    # 기타 장비
    # ============================================================
    "Stripping Eductor": {
        "tags": ["EDUCTOR", "STRIPPING EDUCTOR"],
        "patterns": [r"\bEDUCTOR\b", r"\bSTRIP(?:PING)?\s*EDUCTOR\b"],
        "description": "스트리핑 이덕터",
    },
    "Filter": {
        "tags": ["FLT", "FILTER", "FTU"],
        "patterns": [r"\bFLT[-_]?\d*\b", r"\bFILTER\b", r"\bFTU[-_]?\d*\b"],
        "description": "필터",
    },
    "Heat Exchanger": {
        "tags": ["HEU", "HX", "HEAT EXCHANGER"],
        "patterns": [r"\bHEU[-_]?\d*\b", r"\bHX[-_]?\d*\b", r"\bHEAT\s*EXCHANGER\b"],
        "description": "열교환기",
    },

    # ============================================================
    # Strainer 타입 (P1 추가)
    # ============================================================
    "T-STRAINER": {
        "tags": ["T-STRAINER", "T STRAINER", "TSTRAINER"],
        "patterns": [r"\bT[-\s]?STRAINER\b", r"\b[I!|]?T[-\s]?STRAINER[I!|]?\b"],
        "description": "T형 스트레이너",
    },
    "Y-STRAINER": {
        "tags": ["Y-STRAINER", "Y STRAINER", "YSTRAINER"],
        "patterns": [r"\bY[-\s]?STRAINER\b"],
        "description": "Y형 스트레이너",
    },
    "Strainer": {
        "tags": ["STRAINER", "STR"],
        "patterns": [r"\bSTRAINER\b", r"\bSTR[-_]?\d*\b"],
        "description": "스트레이너 (일반)",
    },

    # ============================================================
    # Flushing/Cleaning Line (P1 추가)
    # ============================================================
    "Flushing Line": {
        "tags": ["FLUSHING", "FLUSHING LINE", "LINE FLUSHING", "FLUSH LINE"],
        "patterns": [
            r"\bFLUSH(?:ING)?\s*(?:LINE|PIPE)?\b",
            r"\bLINE\s*FLUSH(?:ING)?\b",
            r"\bFLUSH(?:ING)?\s*AND\s*DRAIN\b",
        ],
        "description": "플러싱 라인",
    },
    "Cleaning Line": {
        "tags": ["CLEANING", "CLEANING LINE", "CIP"],
        "patterns": [r"\bCLEAN(?:ING)?\s*(?:LINE|PIPE)?\b", r"\bCIP\b"],
        "description": "세정 라인",
    },

    # ============================================================
    # Sensor 타입 (P1 추가)
    # ============================================================
    "Temperature Sensor": {
        "tags": ["TEMP SENSOR", "TEMPERATURE SENSOR", "TS", "TI"],
        "patterns": [
            r"\bTEMP(?:ERATURE)?\s*SENSOR\b",
            r"\bTS[-_]?\d+\b",
            r"\bTI[-_]?\d+\b",
            r"\bTEMP(?:ERATURE)?\s*(?:INDICATOR|SWITCH)\b",
        ],
        "description": "온도 센서",
    },
    "Conductivity Sensor": {
        "tags": ["CONDUCTIVITY SENSOR", "COND SENSOR", "CSU"],
        "patterns": [
            r"\bCOND(?:UCTIVITY)?\s*SENSOR\b",
            r"\bCSU[-_]?\d*\b",
            r"\bCOND(?:UCTIVITY)?\s*(?:UNIT|SENSOR)\b",
        ],
        "description": "전도도 센서",
    },
    "Salinity Sensor": {
        "tags": ["SALINITY SENSOR", "SAL SENSOR"],
        "patterns": [r"\bSALIN(?:ITY)?\s*SENSOR\b"],
        "description": "염도 센서",
    },
    "TRO Sensor": {
        "tags": ["TRO SENSOR", "TRO"],
        "patterns": [r"\bTRO\s*(?:SENSOR)?\b", r"\bTRO[-_]?\d*\b"],
        "description": "TRO 센서 (잔류염소)",
    },
    "Sensor": {
        "tags": ["SENSOR"],
        "patterns": [r"\bSENSOR\b"],
        "description": "센서 (일반)",
    },

    # ============================================================
    # Signal/Control Valve (P1 추가)
    # ============================================================
    "Signal Valve": {
        "tags": ["SIGNAL VALVE", "SIG VALVE", "SIGNAL"],
        "patterns": [r"\bSIGNAL\s*(?:VALVE)?\b", r"\bSIG\s*VALVE\b"],
        "description": "신호 밸브",
    },
    "Manual Valve": {
        "tags": ["MANUAL VALVE", "MV", "HAND VALVE"],
        "patterns": [r"\bMANUAL\s*VALVE\b", r"\bMV[-_]?\d*\b", r"\bHAND\s*VALVE\b"],
        "description": "수동 밸브",
    },
    "Remote Valve": {
        "tags": ["REMOTE VALVE", "RV", "REMOTE"],
        "patterns": [r"\bREMOTE\s*(?:VALVE|BUTTERFLY)?\b"],
        "description": "원격 밸브",
    },
    "3-Way Valve": {
        "tags": ["3-WAY VALVE", "3WAY", "THREE WAY"],
        "patterns": [r"\b3[-\s]?WAY\s*(?:VALVE|COCK)?\b", r"\bTHREE\s*WAY\b"],
        "description": "3방 밸브",
    },

    # ============================================================
    # ECS 전용 장비 (P1 추가)
    # ============================================================
    "HEU": {
        "tags": ["HEU", "HEATING UNIT", "HEAT EXCHANGE UNIT"],
        "patterns": [r"\bHEU[-_]?\d*\b", r"\bHEAT(?:ING)?\s*(?:EXCHANGE\s*)?UNIT\b"],
        "description": "Heating/Heat Exchange Unit (ECS)",
        "product_type": "ECS",
    },
    "DTS": {
        "tags": ["DTS", "DIFF TEMP SENSOR", "DIFFERENTIAL TEMP"],
        "patterns": [r"\bDTS[-_]?\d*\b", r"\bDIFF(?:ERENTIAL)?\s*TEMP\b"],
        "description": "Differential Temperature Sensor (ECS)",
        "product_type": "ECS",
    },
    "VLS": {
        "tags": ["VLS", "VALVE SIGNAL", "VALVE LIMIT SWITCH"],
        "patterns": [r"\bVLS[-_]?\d*\b", r"\bVALVE\s*(?:SIGNAL|LIMIT)\b"],
        "description": "Valve Limit Switch (ECS)",
        "product_type": "ECS",
    },
    "VCU": {
        "tags": ["VCU", "VALVE CONTROL UNIT"],
        "patterns": [r"\bVCU[-_]?\d*\b", r"\bVALVE\s*CONTROL\s*UNIT\b"],
        "description": "Valve Control Unit (ECS)",
        "product_type": "ECS",
    },
    "IS-Barrier": {
        "tags": ["IS BARRIER", "IS-BARRIER", "INTRINSIC SAFETY", "IS BARR"],
        "patterns": [r"\bIS[-\s]?BARR(?:IER)?\b", r"\bINTRINSIC\s*SAFETY\b"],
        "description": "Intrinsic Safety Barrier (ECS)",
        "product_type": "ECS",
    },
    "Ex-DTS": {
        "tags": ["EX-DTS", "EXDTS", "EX DTS"],
        "patterns": [r"\bEX[-\s]?DTS[-_]?\d*\b"],
        "description": "Explosion-proof DTS (ECS)",
        "product_type": "ECS",
    },
}

# ============================================================
# OCR 태그 → 장비명 역매핑 (자동 생성)
# ============================================================
TAG_TO_EQUIPMENT: dict[str, list[str]] = {}
for equip_name, config in EQUIPMENT_TO_TAGS.items():
    for tag in config["tags"]:
        tag_upper = tag.upper()
        if tag_upper not in TAG_TO_EQUIPMENT:
            TAG_TO_EQUIPMENT[tag_upper] = []
        if equip_name not in TAG_TO_EQUIPMENT[tag_upper]:
            TAG_TO_EQUIPMENT[tag_upper].append(equip_name)


class EquipmentMapper:
    """장비명 ↔ OCR 태그 매퍼"""

    def __init__(self):
        self.equipment_to_tags = EQUIPMENT_TO_TAGS
        self.tag_to_equipment = TAG_TO_EQUIPMENT
        self._compile_patterns()

    def _compile_patterns(self):
        """정규식 패턴 컴파일"""
        self._compiled_patterns = {}
        for equip_name, config in self.equipment_to_tags.items():
            patterns = config.get("patterns", [])
            self._compiled_patterns[equip_name] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def find_tags_for_equipment(
        self,
        equipment_name: str,
        ocr_texts: list[str]
    ) -> EquipmentMatch:
        """
        규칙의 equipment 이름으로 OCR 텍스트에서 매칭되는 태그 찾기

        Args:
            equipment_name: 규칙의 equipment 필드 값
            ocr_texts: OCR 결과 텍스트 리스트

        Returns:
            EquipmentMatch: 매칭 결과
        """
        matched_tags = []
        match_type = "none"

        # 1. 직접 매핑 확인
        equip_upper = equipment_name.upper().strip()
        if equip_upper in self.equipment_to_tags:
            config = self.equipment_to_tags[equip_upper]
            patterns = self._compiled_patterns.get(equip_upper, [])

            for text in ocr_texts:
                text_upper = text.upper()
                # 태그 직접 매칭
                for tag in config["tags"]:
                    if tag.upper() in text_upper:
                        matched_tags.append(text)
                        match_type = "direct"

                # 패턴 매칭
                for pattern in patterns:
                    if pattern.search(text):
                        if text not in matched_tags:
                            matched_tags.append(text)
                            match_type = "pattern"

        # 2. 부분 매칭 (equipment 이름에 여러 항목이 있는 경우)
        if not matched_tags and "," in equipment_name:
            for part in equipment_name.split(","):
                part = part.strip()
                sub_match = self.find_tags_for_equipment(part, ocr_texts)
                matched_tags.extend(sub_match.matched_tags)
                if sub_match.match_type != "none":
                    match_type = "alias"

        # 3. 유사어 매칭 (Valve, Pump 등 일반 용어)
        if not matched_tags:
            for equip_key, config in self.equipment_to_tags.items():
                # equipment_name이 equip_key에 포함되거나 그 반대
                if (equip_upper in equip_key.upper() or
                    equip_key.upper() in equip_upper):
                    patterns = self._compiled_patterns.get(equip_key, [])
                    for text in ocr_texts:
                        for pattern in patterns:
                            if pattern.search(text):
                                if text not in matched_tags:
                                    matched_tags.append(text)
                                    match_type = "alias"

        # 신뢰도 계산
        confidence = 1.0 if match_type == "direct" else (
            0.8 if match_type == "pattern" else (
                0.6 if match_type == "alias" else 0.0
            )
        )

        return EquipmentMatch(
            rule_equipment=equipment_name,
            matched_tags=list(set(matched_tags)),  # 중복 제거
            match_type=match_type,
            confidence=confidence
        )

    def find_equipment_for_tag(
        self,
        tag: str
    ) -> list[str]:
        """
        OCR 태그로 가능한 장비명 찾기

        Args:
            tag: OCR 태그 (예: "BWV1", "ECU", "FCV01")

        Returns:
            매칭되는 장비명 리스트
        """
        tag_upper = tag.upper().strip()

        # 1. 직접 매핑 확인
        if tag_upper in self.tag_to_equipment:
            return self.tag_to_equipment[tag_upper]

        # 2. 태그에서 타입 추출 (숫자 제거)
        tag_type = re.sub(r"[-_\s]?\d+[A-Z]?$", "", tag_upper)
        if tag_type in self.tag_to_equipment:
            return self.tag_to_equipment[tag_type]

        # 3. 패턴 매칭으로 검색
        matches = []
        for equip_name, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.match(tag):
                    if equip_name not in matches:
                        matches.append(equip_name)

        return matches

    def validate_equipment_in_ocr(
        self,
        equipment_name: str,
        ocr_results: list[dict]
    ) -> dict:
        """
        규칙의 equipment가 OCR 결과에 존재하는지 검증

        Args:
            equipment_name: 규칙의 equipment 필드
            ocr_results: OCR 결과 리스트 [{text, confidence, ...}, ...]

        Returns:
            {
                "exists": bool,
                "matched_tags": [...],
                "match_type": str,
                "confidence": float,
                "locations": [...]  # 검출 위치
            }
        """
        texts = [r.get("text", "") for r in ocr_results]
        match = self.find_tags_for_equipment(equipment_name, texts)

        # 위치 정보 추출
        locations = []
        for ocr in ocr_results:
            text = ocr.get("text", "")
            if text in match.matched_tags:
                locations.append({
                    "text": text,
                    "x": ocr.get("x", 0),
                    "y": ocr.get("y", 0),
                    "confidence": ocr.get("confidence", 0)
                })

        return {
            "exists": len(match.matched_tags) > 0,
            "matched_tags": match.matched_tags,
            "match_type": match.match_type,
            "confidence": match.confidence,
            "locations": locations
        }

    def get_all_mappings(self) -> dict:
        """전체 매핑 테이블 반환"""
        return {
            "equipment_to_tags": {
                k: {"tags": v["tags"], "description": v.get("description", "")}
                for k, v in self.equipment_to_tags.items()
            },
            "tag_to_equipment": self.tag_to_equipment,
            "total_equipment": len(self.equipment_to_tags),
            "total_tags": len(self.tag_to_equipment)
        }


# 싱글톤 인스턴스
equipment_mapper = EquipmentMapper()
