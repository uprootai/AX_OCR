#!/usr/bin/env python3
"""
EDGNet 간단한 데이터 증강 스크립트

현재 데이터셋 구조에 맞춰 이미지와 그래프를 함께 증강합니다.
- 원본: 2개 도면
- 증강: 7가지 변형 (회전, 밝기, 노이즈)
- 결과: 14개 도면 (7배)
"""

import json
import cv2
import numpy as np
from pathlib import Path
import shutil
from typing import Dict, List, Tuple

class EDGNetAugmenter:
    def __init__(self):
        self.dataset_path = Path("/home/uproot/ax/poc/edgnet_dataset")
        self.output_path = Path("/home/uproot/ax/poc/edgnet_dataset_augmented")

        # 증강 타입
        self.augmentations = [
            "original",
            "rot90",
            "rot180",
            "rot270",
            "bright",
            "dark",
            "noise"
        ]

    def augment_image(self, image_path: Path) -> List[Tuple[str, np.ndarray]]:
        """이미지 증강"""
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        h, w = img.shape[:2]
        augmented = []

        # 1. Original
        augmented.append(("original", img.copy()))

        # 2-4. 회전
        for angle, name in [(90, "rot90"), (180, "rot180"), (270, "rot270")]:
            M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            augmented.append((name, rotated))

        # 5. 밝게
        bright = cv2.convertScaleAbs(img, alpha=1.2, beta=10)
        augmented.append(("bright", bright))

        # 6. 어둡게
        dark = cv2.convertScaleAbs(img, alpha=0.8, beta=-10)
        augmented.append(("dark", dark))

        # 7. 노이즈
        noise = np.random.normal(0, 10, img.shape).astype(np.uint8)
        noisy = cv2.add(img, noise)
        augmented.append(("noise", noisy))

        return augmented

    def transform_bbox(self, bbox: Dict, aug_type: str, img_width: int, img_height: int) -> Dict:
        """
        바운딩 박스 변환
        회전에 따라 bbox 좌표 조정
        """
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']

        if aug_type == "original" or aug_type in ["bright", "dark", "noise"]:
            return bbox.copy()

        elif aug_type == "rot90":
            # 90도 회전: (x,y) -> (y, img_width-x-w)
            return {
                'x': y,
                'y': img_width - x - w,
                'width': h,
                'height': w
            }

        elif aug_type == "rot180":
            # 180도 회전: (x,y) -> (img_width-x-w, img_height-y-h)
            return {
                'x': img_width - x - w,
                'y': img_height - y - h,
                'width': w,
                'height': h
            }

        elif aug_type == "rot270":
            # 270도 회전: (x,y) -> (img_height-y-h, x)
            return {
                'x': img_height - y - h,
                'y': x,
                'width': h,
                'height': w
            }

        return bbox.copy()

    def augment_graph(self, graph_data: Dict, aug_type: str, img_width: int, img_height: int) -> Dict:
        """그래프 데이터 증강"""
        augmented = graph_data.copy()

        # 노드 증강 (bbox 변환)
        if 'graph_nodes' in augmented:
            new_nodes = []
            for node in augmented['graph_nodes']:
                new_node = node.copy()
                if 'bbox' in new_node:
                    new_node['bbox'] = self.transform_bbox(
                        new_node['bbox'],
                        aug_type,
                        img_width,
                        img_height
                    )
                new_nodes.append(new_node)
            augmented['graph_nodes'] = new_nodes

        # 엣지는 그대로 유지 (노드 ID만 참조)

        return augmented

    def run(self):
        """증강 실행"""
        print("=" * 60)
        print("🎯 EDGNet 데이터 증강 (간단 버전)")
        print("=" * 60)

        # 출력 디렉토리 생성
        self.output_path.mkdir(exist_ok=True)
        (self.output_path / "drawings").mkdir(exist_ok=True)

        # JSON 파일 찾기
        json_files = [f for f in self.dataset_path.glob("*.json") if f.name != "metadata.json"]

        print(f"\n📁 발견된 그래프 파일: {len(json_files)}개")

        total_augmented = 0
        all_nodes = 0
        all_edges = 0

        for json_file in json_files:
            print(f"\n처리 중: {json_file.name}")

            # JSON 로드
            with open(json_file, 'r') as f:
                graph_data = json.load(f)

            # 이미지 파일 찾기
            base_name = json_file.stem
            # "A12-311197-9 Rev.2 Interm Shaft-Acc_y_1" -> "A12-311197-9 Rev.2 Interm Shaft-Acc_y"
            if base_name.endswith("_1"):
                img_base = base_name[:-2]
            else:
                img_base = base_name

            img_path = self.dataset_path / "drawings" / f"{img_base}.jpg"

            if not img_path.exists():
                print(f"  ⚠️  이미지 파일 없음: {img_path.name}")
                continue

            # 이미지 로드
            img = cv2.imread(str(img_path))
            img_height, img_width = img.shape[:2]

            print(f"  이미지: {img_width}x{img_height}")
            print(f"  노드: {len(graph_data.get('graph_nodes', []))}")
            print(f"  엣지: {len(graph_data.get('graph_edges', []))}")

            # 증강 수행
            augmented_images = self.augment_image(img_path)

            for aug_type, aug_img in augmented_images:
                # 증강된 이미지 저장
                out_img_name = f"{base_name}_{aug_type}.jpg"
                out_img_path = self.output_path / "drawings" / out_img_name
                cv2.imwrite(str(out_img_path), aug_img)

                # 증강된 그래프 생성
                aug_graph = self.augment_graph(graph_data, aug_type, img_width, img_height)
                aug_graph['filename'] = out_img_name

                # JSON 저장
                out_json_name = f"{base_name}_{aug_type}.json"
                out_json_path = self.output_path / out_json_name
                with open(out_json_path, 'w') as f:
                    json.dump(aug_graph, f, indent=2)

                total_augmented += 1
                all_nodes += len(aug_graph.get('graph_nodes', []))
                all_edges += len(aug_graph.get('graph_edges', []))

                print(f"    ✅ {aug_type}")

        # 메타데이터 생성
        metadata = {
            "num_drawings": total_augmented,
            "total_nodes": all_nodes,
            "total_edges": all_edges,
            "original_drawings": len(json_files),
            "augmentation_factor": 7,
            "augmentations": self.augmentations
        }

        with open(self.output_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        print("\n" + "=" * 60)
        print("✅ 증강 완료!")
        print("=" * 60)
        print(f"원본 도면:   {len(json_files)}개")
        print(f"증강 도면:   {total_augmented}개 (7배)")
        print(f"총 노드:     {all_nodes}개")
        print(f"총 엣지:     {all_edges}개")
        print(f"출력 경로:   {self.output_path}")
        print("=" * 60)

        return total_augmented


if __name__ == "__main__":
    augmenter = EDGNetAugmenter()
    result = augmenter.run()

    if result > 0:
        print("\n🎉 성공! 다음 단계:")
        print("   python3 scripts/retrain_edgnet_gpu.py")
    else:
        print("\n❌ 증강 실패")
        exit(1)
