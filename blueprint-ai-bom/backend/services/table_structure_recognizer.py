"""Table Structure Recognizer Service - TableTransformer + EasyOCR 기반

테이블 구조 인식 및 셀 텍스트 추출 서비스
- Microsoft TableTransformer: 테이블 구조 (행/열) 인식
- EasyOCR: 셀 텍스트 추출 (한국어/영어 지원)
- DocLayout-YOLO와 연동하여 BOM 테이블 처리
- 자동 회전 감지 및 보정 (세로 텍스트 처리)

통합 일자: 2026-01-17
회전 보정 추가: 2026-01-17
검증 결과: idea-thinking/sub/003_table_transformer_ocr.md
GPU 메모리: 약 330MB (TableTransformer 140MB + EasyOCR 190MB)
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import torch
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# 환경변수 설정
TABLE_RECOGNIZER_ENABLED = os.environ.get("TABLE_RECOGNIZER_ENABLED", "true").lower() == "true"
TABLE_STRUCTURE_THRESHOLD = float(os.environ.get("TABLE_STRUCTURE_THRESHOLD", "0.5"))
TABLE_RECOGNIZER_DEVICE = os.environ.get("TABLE_RECOGNIZER_DEVICE", "cuda:0" if torch.cuda.is_available() else "cpu")
OCR_UPSCALE_FACTOR = int(os.environ.get("OCR_UPSCALE_FACTOR", "3"))
OCR_LANGUAGES = os.environ.get("OCR_LANGUAGES", "en,ko").split(",")


class TableElementType(str, Enum):
    """테이블 구조 요소 타입"""
    TABLE = "table"
    TABLE_ROW = "table row"
    TABLE_COLUMN = "table column"
    TABLE_SPANNING_CELL = "table spanning cell"
    TABLE_PROJECTED_ROW_HEADER = "table projected row header"
    TABLE_COLUMN_HEADER = "table column header"


@dataclass
class TableCell:
    """테이블 셀 데이터"""
    row: int
    col: int
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    text: str = ""
    confidence: float = 0.0


@dataclass
class TableStructure:
    """테이블 구조 데이터"""
    rows: int
    columns: int
    cells: List[TableCell] = field(default_factory=list)
    row_boxes: List[Tuple[float, float, float, float]] = field(default_factory=list)
    col_boxes: List[Tuple[float, float, float, float]] = field(default_factory=list)
    spanning_cells: List[Dict[str, Any]] = field(default_factory=list)
    source_bbox: Optional[Tuple[float, float, float, float]] = None


@dataclass
class TableRecognitionResult:
    """테이블 인식 결과"""
    structure: TableStructure
    raw_elements: List[Dict[str, Any]] = field(default_factory=list)
    ocr_performed: bool = False
    processing_time_ms: float = 0.0


class TableStructureRecognizer:
    """TableTransformer + EasyOCR 기반 테이블 구조 인식기"""

    def __init__(self):
        self.structure_model = None
        self.structure_processor = None
        self.ocr_reader = None
        self._initialized = False
        self._ocr_initialized = False
        self.device = TABLE_RECOGNIZER_DEVICE

        if TABLE_RECOGNIZER_ENABLED:
            self._initialize_structure_model()

    def _initialize_structure_model(self):
        """TableTransformer 구조 인식 모델 초기화"""
        if self._initialized:
            return

        try:
            from transformers import TableTransformerForObjectDetection, DetrImageProcessor

            logger.info("[TableStructureRecognizer] TableTransformer 모델 로드 중...")

            # Structure Recognition 모델 (Detection은 DocLayout-YOLO 사용)
            model_name = "microsoft/table-transformer-structure-recognition-v1.1-all"

            self.structure_processor = DetrImageProcessor.from_pretrained(
                model_name,
                size={"shortest_edge": 800, "longest_edge": 1333}
            )

            self.structure_model = TableTransformerForObjectDetection.from_pretrained(
                model_name
            ).to(self.device)
            self.structure_model.eval()

            # 파라미터 수 확인
            params = sum(p.numel() for p in self.structure_model.parameters())
            logger.info(f"[TableStructureRecognizer] 모델 로드 완료: {params / 1e6:.1f}M 파라미터")

            self._initialized = True

        except ImportError as e:
            logger.warning(f"[TableStructureRecognizer] transformers 미설치: {e}")
            logger.warning("[TableStructureRecognizer] 설치: pip install transformers timm")
            self._initialized = False

        except Exception as e:
            logger.error(f"[TableStructureRecognizer] 초기화 실패: {e}")
            self._initialized = False

    def _initialize_ocr(self):
        """EasyOCR 초기화 (지연 로딩)"""
        if self._ocr_initialized:
            return

        try:
            import easyocr

            logger.info(f"[TableStructureRecognizer] EasyOCR 초기화 중 (languages: {OCR_LANGUAGES})...")
            use_gpu = "cuda" in self.device
            self.ocr_reader = easyocr.Reader(OCR_LANGUAGES, gpu=use_gpu)
            self._ocr_initialized = True
            logger.info("[TableStructureRecognizer] EasyOCR 초기화 완료")

        except ImportError as e:
            logger.warning(f"[TableStructureRecognizer] easyocr 미설치: {e}")
            logger.warning("[TableStructureRecognizer] 설치: pip install easyocr")
            self._ocr_initialized = False

        except Exception as e:
            logger.error(f"[TableStructureRecognizer] EasyOCR 초기화 실패: {e}")
            self._ocr_initialized = False

    @property
    def is_available(self) -> bool:
        """구조 인식 모델 사용 가능 여부"""
        return self._initialized and self.structure_model is not None

    @property
    def is_ocr_available(self) -> bool:
        """OCR 사용 가능 여부"""
        if not self._ocr_initialized:
            self._initialize_ocr()
        return self._ocr_initialized and self.ocr_reader is not None

    def recognize_structure(
        self,
        table_image: Image.Image,
        threshold: float = None
    ) -> TableRecognitionResult:
        """
        테이블 이미지에서 구조 인식

        Args:
            table_image: 테이블 영역 이미지 (PIL Image)
            threshold: 검출 임계값 (기본값: TABLE_STRUCTURE_THRESHOLD)

        Returns:
            TableRecognitionResult: 구조 인식 결과
        """
        import time
        start_time = time.time()

        if not self.is_available:
            logger.warning("[TableStructureRecognizer] 모델 사용 불가")
            return TableRecognitionResult(
                structure=TableStructure(rows=0, columns=0),
                processing_time_ms=0.0
            )

        threshold = threshold or TABLE_STRUCTURE_THRESHOLD

        try:
            # 이미지 전처리
            inputs = self.structure_processor(
                images=table_image,
                return_tensors="pt"
            ).to(self.device)

            # 추론
            with torch.no_grad():
                outputs = self.structure_model(**inputs)

            # 후처리
            target_sizes = torch.tensor([table_image.size[::-1]]).to(self.device)
            results = self.structure_processor.post_process_object_detection(
                outputs,
                threshold=threshold,
                target_sizes=target_sizes
            )[0]

            # 구조 요소 파싱
            raw_elements = []
            rows_boxes = []
            cols_boxes = []
            spanning_cells = []

            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                label_name = self.structure_model.config.id2label[label.item()]
                bbox = tuple(box.tolist())
                confidence = score.item()

                element = {
                    "type": label_name,
                    "bbox": bbox,
                    "confidence": confidence
                }
                raw_elements.append(element)

                if label_name == "table row":
                    rows_boxes.append(bbox)
                elif label_name == "table column":
                    cols_boxes.append(bbox)
                elif label_name == "table spanning cell":
                    spanning_cells.append(element)

            # Y좌표로 행 정렬, X좌표로 열 정렬
            rows_boxes.sort(key=lambda b: b[1])  # y1 기준
            cols_boxes.sort(key=lambda b: b[0])  # x1 기준

            structure = TableStructure(
                rows=len(rows_boxes),
                columns=len(cols_boxes),
                row_boxes=rows_boxes,
                col_boxes=cols_boxes,
                spanning_cells=spanning_cells
            )

            processing_time = (time.time() - start_time) * 1000

            logger.info(f"[TableStructureRecognizer] 구조 인식 완료: {structure.rows}행 x {structure.columns}열")

            return TableRecognitionResult(
                structure=structure,
                raw_elements=raw_elements,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"[TableStructureRecognizer] 구조 인식 실패: {e}")
            return TableRecognitionResult(
                structure=TableStructure(rows=0, columns=0),
                processing_time_ms=(time.time() - start_time) * 1000
            )

    def _preprocess_for_ocr(
        self,
        image: Image.Image,
        upscale_factor: int,
        enhance_contrast: bool = True,
        sharpen: bool = True,
        grayscale: bool = True
    ) -> Image.Image:
        """
        OCR을 위한 이미지 전처리

        Args:
            image: 원본 이미지
            upscale_factor: 확대 배율
            enhance_contrast: 대비 향상 여부
            sharpen: 샤프닝 여부
            grayscale: 그레이스케일 변환 여부

        Returns:
            Image.Image: 전처리된 이미지
        """
        from PIL import ImageEnhance, ImageFilter

        w, h = image.size

        # 1. 업스케일
        processed = image.resize(
            (w * upscale_factor, h * upscale_factor),
            Image.LANCZOS
        )

        # 2. 대비 향상
        if enhance_contrast:
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(1.5)

        # 3. 샤프닝
        if sharpen:
            processed = processed.filter(ImageFilter.SHARPEN)

        # 4. 그레이스케일
        if grayscale:
            processed = processed.convert("L")

        return processed

    def _rotate_image(
        self,
        image: Image.Image,
        angle: int
    ) -> Image.Image:
        """
        이미지 회전

        Args:
            image: 원본 이미지
            angle: 회전 각도 (0, 90, 180, 270)

        Returns:
            Image.Image: 회전된 이미지
        """
        if angle == 0:
            return image
        elif angle == 90:
            return image.transpose(Image.ROTATE_90)
        elif angle == 180:
            return image.transpose(Image.ROTATE_180)
        elif angle == 270:
            return image.transpose(Image.ROTATE_270)
        else:
            # 임의의 각도 회전 (배경 흰색)
            return image.rotate(angle, expand=True, fillcolor=(255, 255, 255))

    def detect_text_rotation(
        self,
        image: Image.Image,
        angles: List[int] = None,
        sample_scale: int = 2
    ) -> Tuple[int, Dict[str, Any]]:
        """
        텍스트 방향 감지 (최적 회전 각도 찾기)

        여러 회전 각도에서 OCR을 수행하고 가장 좋은 결과를 반환합니다.
        평가 기준: 인식된 텍스트 수 × 평균 신뢰도

        Args:
            image: 테이블 이미지
            angles: 테스트할 각도 목록 (기본값: [0, 90, 180, 270])
            sample_scale: 샘플링용 축소 배율 (속도 향상, 기본값: 2)

        Returns:
            Tuple[int, Dict]: (최적 회전 각도, 각 각도별 점수 상세)
        """
        if not self.is_ocr_available:
            logger.warning("[TableStructureRecognizer] OCR 사용 불가 - 회전 감지 불가")
            return 0, {}

        if angles is None:
            angles = [0, 90, 180, 270]

        results = {}
        best_angle = 0
        best_score = -1

        # 속도를 위해 샘플 이미지 사용
        w, h = image.size
        sample_image = image.resize(
            (w // sample_scale, h // sample_scale),
            Image.LANCZOS
        )

        for angle in angles:
            try:
                # 이미지 회전
                rotated = self._rotate_image(sample_image, angle)

                # 전처리 (업스케일은 최소화)
                processed = self._preprocess_for_ocr(
                    rotated,
                    upscale_factor=2,  # 샘플용이므로 낮게
                    enhance_contrast=True,
                    sharpen=True,
                    grayscale=True
                )

                # OCR 실행
                ocr_results = self.ocr_reader.readtext(
                    np.array(processed),
                    detail=1,
                    paragraph=False
                )

                # 점수 계산
                if ocr_results:
                    num_texts = len(ocr_results)
                    avg_conf = sum(r[2] for r in ocr_results) / num_texts
                    # 텍스트 길이 보너스 (긴 텍스트는 더 신뢰성 있음)
                    total_chars = sum(len(r[1]) for r in ocr_results)
                    # 종합 점수: 텍스트 수 × 신뢰도 × log(총 문자수)
                    import math
                    score = num_texts * avg_conf * math.log(max(total_chars, 1) + 1)
                else:
                    num_texts = 0
                    avg_conf = 0
                    total_chars = 0
                    score = 0

                results[angle] = {
                    "num_texts": num_texts,
                    "avg_confidence": round(avg_conf, 3),
                    "total_chars": total_chars,
                    "score": round(score, 3)
                }

                if score > best_score:
                    best_score = score
                    best_angle = angle

                logger.debug(f"[Rotation {angle}°] texts={num_texts}, conf={avg_conf:.2f}, score={score:.1f}")

            except Exception as e:
                logger.warning(f"[TableStructureRecognizer] 회전 {angle}° 테스트 실패: {e}")
                results[angle] = {"error": str(e), "score": 0}

        logger.info(f"[TableStructureRecognizer] 최적 회전 각도: {best_angle}° (score={best_score:.1f})")

        return best_angle, results

    def extract_whole_table_text_with_rotation(
        self,
        table_image: Image.Image,
        upscale_factor: int = 5,
        confidence_threshold: float = 0.3,
        auto_rotate: bool = True,
        rotation_angles: List[int] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        전체 테이블 이미지에서 텍스트 추출 (자동 회전 보정 포함)

        Args:
            table_image: 테이블 영역 이미지
            upscale_factor: 이미지 확대 배율 (기본값: 5)
            confidence_threshold: 신뢰도 임계값 (기본값: 0.3)
            auto_rotate: 자동 회전 감지 여부 (기본값: True)
            rotation_angles: 테스트할 회전 각도 (기본값: [0, 90, 180, 270])

        Returns:
            Tuple[List[Dict], int]: (OCR 결과 목록, 적용된 회전 각도)
        """
        if not self.is_ocr_available:
            logger.warning("[TableStructureRecognizer] OCR 사용 불가")
            return [], 0

        applied_rotation = 0

        try:
            # 자동 회전 감지
            if auto_rotate:
                applied_rotation, rotation_results = self.detect_text_rotation(
                    table_image,
                    angles=rotation_angles
                )

                # 회전 적용
                if applied_rotation != 0:
                    logger.info(f"[TableStructureRecognizer] 이미지 {applied_rotation}° 회전 적용")
                    table_image = self._rotate_image(table_image, applied_rotation)

            # 이미지 전처리 (그레이스케일 포함)
            preprocessed = self._preprocess_for_ocr(
                table_image,
                upscale_factor,
                enhance_contrast=True,
                sharpen=True,
                grayscale=True
            )

            # OCR 실행
            ocr_results = self.ocr_reader.readtext(
                np.array(preprocessed),
                detail=1,
                paragraph=False
            )

            # 결과 필터링 및 변환
            results = []
            for bbox, text, conf in ocr_results:
                if conf >= confidence_threshold:
                    # bbox 좌표를 원본 스케일로 변환
                    scaled_bbox = [
                        [p[0] / upscale_factor, p[1] / upscale_factor]
                        for p in bbox
                    ]
                    results.append({
                        "text": text,
                        "confidence": round(conf, 3),
                        "bbox": scaled_bbox
                    })

            results.sort(key=lambda x: -x["confidence"])
            logger.info(f"[TableStructureRecognizer] 전체 OCR (회전 {applied_rotation}°): {len(results)}개 텍스트 검출")

            return results, applied_rotation

        except Exception as e:
            logger.error(f"[TableStructureRecognizer] 전체 OCR (회전 포함) 실패: {e}")
            return [], applied_rotation

    def extract_cell_texts(
        self,
        table_image: Image.Image,
        structure: TableStructure,
        upscale_factor: int = None,
        preprocess: bool = True
    ) -> TableStructure:
        """
        테이블 셀에서 텍스트 추출

        Args:
            table_image: 테이블 영역 이미지
            structure: 테이블 구조 정보
            upscale_factor: 이미지 확대 배율 (기본값: OCR_UPSCALE_FACTOR)
            preprocess: 이미지 전처리 적용 여부 (대비 향상, 샤프닝)

        Returns:
            TableStructure: 셀 텍스트가 추가된 구조
        """
        if not self.is_ocr_available:
            logger.warning("[TableStructureRecognizer] OCR 사용 불가")
            return structure

        if not structure.row_boxes or not structure.col_boxes:
            logger.warning("[TableStructureRecognizer] 행/열 정보 없음")
            return structure

        upscale_factor = upscale_factor or OCR_UPSCALE_FACTOR

        try:
            # 이미지 전처리 (OCR 정확도 향상)
            w, h = table_image.size
            if preprocess:
                upscaled = self._preprocess_for_ocr(
                    table_image,
                    upscale_factor,
                    enhance_contrast=True,
                    sharpen=True,
                    grayscale=False  # 셀별 OCR은 컬러 유지
                )
            else:
                upscaled = table_image.resize(
                    (w * upscale_factor, h * upscale_factor),
                    Image.LANCZOS
                )

            cells = []

            for row_idx, row_box in enumerate(structure.row_boxes):
                for col_idx, col_box in enumerate(structure.col_boxes):
                    # 셀 bbox 계산 (행과 열의 교차점)
                    x1 = max(col_box[0], row_box[0]) * upscale_factor
                    y1 = max(col_box[1], row_box[1]) * upscale_factor
                    x2 = min(col_box[2], row_box[2]) * upscale_factor
                    y2 = min(col_box[3], row_box[3]) * upscale_factor

                    # 유효한 셀인지 확인
                    if x2 <= x1 or y2 <= y1:
                        continue

                    # 셀 이미지 추출
                    cell_image = upscaled.crop((x1, y1, x2, y2))

                    # OCR 실행
                    try:
                        result = self.ocr_reader.readtext(
                            np.array(cell_image),
                            detail=1,
                            paragraph=False
                        )

                        if result:
                            # 모든 텍스트 결합
                            texts = [r[1] for r in result]
                            confidences = [r[2] for r in result]
                            text = " ".join(texts)
                            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                        else:
                            text = ""
                            avg_conf = 0.0

                    except Exception as ocr_err:
                        logger.debug(f"셀 OCR 실패 ({row_idx}, {col_idx}): {ocr_err}")
                        text = ""
                        avg_conf = 0.0

                    # 원본 스케일로 bbox 변환
                    original_bbox = (
                        x1 / upscale_factor,
                        y1 / upscale_factor,
                        x2 / upscale_factor,
                        y2 / upscale_factor
                    )

                    cells.append(TableCell(
                        row=row_idx,
                        col=col_idx,
                        bbox=original_bbox,
                        text=text.strip(),
                        confidence=avg_conf
                    ))

            structure.cells = cells
            recognized_count = sum(1 for c in cells if c.text)
            logger.info(f"[TableStructureRecognizer] 셀 OCR 완료: {recognized_count}/{len(cells)}개 인식")

            return structure

        except Exception as e:
            logger.error(f"[TableStructureRecognizer] 셀 텍스트 추출 실패: {e}")
            return structure

    def recognize_and_extract(
        self,
        table_image: Image.Image,
        structure_threshold: float = None,
        upscale_factor: int = None,
        skip_ocr: bool = False
    ) -> TableRecognitionResult:
        """
        테이블 구조 인식 및 셀 텍스트 추출 (통합 파이프라인)

        Args:
            table_image: 테이블 영역 이미지
            structure_threshold: 구조 검출 임계값
            upscale_factor: OCR용 이미지 확대 배율
            skip_ocr: OCR 스킵 여부 (구조만 필요한 경우)

        Returns:
            TableRecognitionResult: 구조 및 텍스트 인식 결과
        """
        # 1. 구조 인식
        result = self.recognize_structure(table_image, structure_threshold)

        if result.structure.rows == 0 or result.structure.columns == 0:
            logger.warning("[TableStructureRecognizer] 테이블 구조 인식 실패")
            return result

        # 2. 셀 텍스트 추출 (옵션)
        if not skip_ocr:
            result.structure = self.extract_cell_texts(
                table_image,
                result.structure,
                upscale_factor
            )
            result.ocr_performed = True

        return result

    def extract_whole_table_text(
        self,
        table_image: Image.Image,
        upscale_factor: int = 5,
        confidence_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        전체 테이블 이미지에서 텍스트 추출 (셀 분할 없이)

        셀별 OCR보다 정확도가 높을 수 있음.
        도면 Title Block 등 작은 텍스트가 많은 경우 권장.

        Args:
            table_image: 테이블 영역 이미지
            upscale_factor: 이미지 확대 배율 (기본값: 5)
            confidence_threshold: 신뢰도 임계값 (기본값: 0.3)

        Returns:
            List[Dict]: OCR 결과 목록 [{text, confidence, bbox}, ...]
        """
        if not self.is_ocr_available:
            logger.warning("[TableStructureRecognizer] OCR 사용 불가")
            return []

        try:
            # 이미지 전처리 (그레이스케일 포함)
            preprocessed = self._preprocess_for_ocr(
                table_image,
                upscale_factor,
                enhance_contrast=True,
                sharpen=True,
                grayscale=True
            )

            # OCR 실행
            ocr_results = self.ocr_reader.readtext(
                np.array(preprocessed),
                detail=1,
                paragraph=False
            )

            # 결과 필터링 및 변환
            results = []
            for bbox, text, conf in ocr_results:
                if conf >= confidence_threshold:
                    # bbox 좌표를 원본 스케일로 변환
                    scaled_bbox = [
                        [p[0] / upscale_factor, p[1] / upscale_factor]
                        for p in bbox
                    ]
                    results.append({
                        "text": text,
                        "confidence": round(conf, 3),
                        "bbox": scaled_bbox
                    })

            results.sort(key=lambda x: -x["confidence"])
            logger.info(f"[TableStructureRecognizer] 전체 OCR: {len(results)}개 텍스트 검출")

            return results

        except Exception as e:
            logger.error(f"[TableStructureRecognizer] 전체 OCR 실패: {e}")
            return []

    def get_table_as_dict(self, structure: TableStructure) -> Dict[str, Any]:
        """
        테이블 구조를 딕셔너리로 변환

        Returns:
            Dict: 테이블 데이터 (2D 배열 형태)
        """
        if not structure.cells:
            return {
                "rows": structure.rows,
                "columns": structure.columns,
                "data": []
            }

        # 2D 배열 생성
        data = [["" for _ in range(structure.columns)] for _ in range(structure.rows)]

        for cell in structure.cells:
            if 0 <= cell.row < structure.rows and 0 <= cell.col < structure.columns:
                data[cell.row][cell.col] = cell.text

        return {
            "rows": structure.rows,
            "columns": structure.columns,
            "data": data,
            "cells": [
                {
                    "row": c.row,
                    "col": c.col,
                    "text": c.text,
                    "confidence": round(c.confidence, 3),
                    "bbox": c.bbox
                }
                for c in structure.cells
            ]
        }

    def get_stats(self) -> Dict[str, Any]:
        """서비스 상태 통계"""
        gpu_memory = 0
        if torch.cuda.is_available() and self._initialized:
            gpu_memory = torch.cuda.memory_allocated(self.device) / 1024 / 1024

        return {
            "structure_model_available": self.is_available,
            "ocr_available": self._ocr_initialized,
            "device": self.device,
            "gpu_memory_mb": round(gpu_memory, 2),
            "ocr_languages": OCR_LANGUAGES,
            "upscale_factor": OCR_UPSCALE_FACTOR,
            "structure_threshold": TABLE_STRUCTURE_THRESHOLD
        }


# 싱글톤 인스턴스 (지연 초기화)
_table_recognizer: Optional[TableStructureRecognizer] = None


def get_table_structure_recognizer() -> TableStructureRecognizer:
    """테이블 구조 인식기 인스턴스 반환 (싱글톤)"""
    global _table_recognizer
    if _table_recognizer is None:
        _table_recognizer = TableStructureRecognizer()
    return _table_recognizer
