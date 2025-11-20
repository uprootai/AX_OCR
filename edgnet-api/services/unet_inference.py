"""
UNet 세그멘테이션 추론 서비스
도면 이미지에서 엣지/경계선 감지를 위한 픽셀 단위 세그멘테이션
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import base64

import torch
import torch.nn as nn
import numpy as np
import cv2
from fastapi import HTTPException

from utils.visualization import create_unet_visualization

# Configure logging
logger = logging.getLogger(__name__)


class UNet(nn.Module):
    """
    UNet 세그멘테이션 모델

    Encoder-Decoder 구조로 이미지에서 픽셀 단위 세그멘테이션 수행
    - Encoder: 이미지 특징 추출 (다운샘플링)
    - Decoder: 세그멘테이션 마스크 생성 (업샘플링)
    - Skip Connections: 고해상도 정보 보존
    """

    def __init__(self, in_channels=1, out_channels=1):
        super(UNet, self).__init__()

        # Encoder
        self.enc1 = self.conv_block(in_channels, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        self.enc4 = self.conv_block(256, 512)

        # Bottleneck
        self.bottleneck = self.conv_block(512, 1024)

        # Decoder
        self.upconv4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.dec4 = self.conv_block(1024, 512)

        self.upconv3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.dec3 = self.conv_block(512, 256)

        self.upconv2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec2 = self.conv_block(256, 128)

        self.upconv1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec1 = self.conv_block(128, 64)

        # Output
        self.out = nn.Conv2d(64, out_channels, kernel_size=1)
        self.sigmoid = nn.Sigmoid()

        # Pooling
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

    def conv_block(self, in_channels, out_channels):
        """3x3 Convolution + BatchNorm + ReLU 블록"""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        """Forward pass"""
        # Encoder
        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool(enc1))
        enc3 = self.enc3(self.pool(enc2))
        enc4 = self.enc4(self.pool(enc3))

        # Bottleneck
        bottleneck = self.bottleneck(self.pool(enc4))

        # Decoder with skip connections
        dec4 = self.upconv4(bottleneck)
        dec4 = torch.cat((dec4, enc4), dim=1)
        dec4 = self.dec4(dec4)

        dec3 = self.upconv3(dec4)
        dec3 = torch.cat((dec3, enc3), dim=1)
        dec3 = self.dec3(dec3)

        dec2 = self.upconv2(dec3)
        dec2 = torch.cat((dec2, enc2), dim=1)
        dec2 = self.dec2(dec2)

        dec1 = self.upconv1(dec2)
        dec1 = torch.cat((dec1, enc1), dim=1)
        dec1 = self.dec1(dec1)

        # Output
        out = self.out(dec1)
        return self.sigmoid(out)


class UNetInferenceService:
    """UNet 추론 서비스"""

    def __init__(self, model_path: str, device: str = 'cpu', image_size: int = 512):
        """
        UNet 추론 서비스 초기화

        Args:
            model_path: UNet 모델 파일 경로 (.pth)
            device: 사용할 디바이스 ('cpu' 또는 'cuda')
            image_size: 입력 이미지 크기 (학습 시 사용한 크기와 동일해야 함)
        """
        self.model_path = model_path
        self.device = device
        self.image_size = image_size
        self.model: Optional[UNet] = None

    def load_model(self):
        """UNet 모델 로드"""
        model_file = Path(self.model_path)
        if not model_file.exists():
            logger.error(f"Model not found: {self.model_path}")
            raise HTTPException(
                status_code=503,
                detail=f"UNet model not found at {self.model_path}"
            )

        logger.info(f"Loading UNet model from: {self.model_path}")
        logger.info(f"Using device: {self.device}")
        logger.info(f"Input image size: {self.image_size}x{self.image_size}")

        # Create model
        self.model = UNet(in_channels=1, out_channels=1)

        # Load weights
        try:
            checkpoint = torch.load(self.model_path, map_location=self.device)

            # Handle different checkpoint formats
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    # Training checkpoint format
                    state_dict = checkpoint['model_state_dict']
                    logger.info(f"Loaded training checkpoint (epoch {checkpoint.get('epoch', '?')})")
                else:
                    # Direct state dict
                    state_dict = checkpoint
            else:
                state_dict = checkpoint

            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            logger.info("UNet model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to load UNet model: {str(e)}"
            )

    def preprocess_image(self, image_path: Path) -> torch.Tensor:
        """
        이미지 전처리

        Args:
            image_path: 입력 이미지 경로

        Returns:
            전처리된 이미지 텐서 [1, 1, H, W]
        """
        # Load image
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Resize to model input size
        img = cv2.resize(img, (self.image_size, self.image_size))

        # Normalize to [0, 1]
        img = img.astype(np.float32) / 255.0

        # Convert to tensor [1, 1, H, W]
        img_tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0)

        return img_tensor

    def postprocess_mask(
        self,
        mask: torch.Tensor,
        original_size: tuple,
        threshold: float = 0.5
    ) -> np.ndarray:
        """
        세그멘테이션 마스크 후처리

        Args:
            mask: 모델 출력 [1, 1, H, W]
            original_size: 원본 이미지 크기 (height, width)
            threshold: 이진화 임계값

        Returns:
            후처리된 마스크 [H, W] (0 또는 255)
        """
        # Convert to numpy
        mask = mask.squeeze().cpu().numpy()

        # Apply threshold
        binary_mask = (mask > threshold).astype(np.uint8) * 255

        # Resize to original size
        if original_size != (self.image_size, self.image_size):
            binary_mask = cv2.resize(
                binary_mask,
                (original_size[1], original_size[0]),
                interpolation=cv2.INTER_NEAREST
            )

        return binary_mask

    def process_segmentation(
        self,
        file_path: Path,
        threshold: float = 0.5,
        visualize: bool = True,
        return_mask: bool = False
    ) -> Dict[str, Any]:
        """
        UNet 세그멘테이션 수행

        Args:
            file_path: 입력 이미지 경로
            threshold: 세그멘테이션 임계값 (0.0~1.0)
            visualize: 시각화 이미지 생성 여부
            return_mask: 세그멘테이션 마스크 반환 여부

        Returns:
            세그멘테이션 결과 딕셔너리
            {
                "mask_shape": [height, width],
                "edge_pixel_count": int,
                "edge_percentage": float,
                "threshold_used": float,
                "model_info": {
                    "architecture": "UNet",
                    "input_size": 512,
                    "parameters": 31042369
                },
                "visualized_image": str (base64, optional),
                "segmentation_mask": str (base64, optional)
            }
        """
        try:
            logger.info(f"Processing UNet segmentation: {file_path}")
            logger.info(f"Options: threshold={threshold}, visualize={visualize}")

            if self.model is None:
                self.load_model()

            # Load original image for size
            original_img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
            if original_img is None:
                raise ValueError(f"Failed to load image: {file_path}")

            original_size = original_img.shape  # (height, width)

            # Preprocess
            logger.info("Preprocessing image...")
            img_tensor = self.preprocess_image(file_path)
            img_tensor = img_tensor.to(self.device)

            # Inference
            logger.info("Running UNet inference...")
            with torch.no_grad():
                mask_pred = self.model(img_tensor)

            # Postprocess
            logger.info("Postprocessing mask...")
            binary_mask = self.postprocess_mask(mask_pred, original_size, threshold)

            # Calculate statistics
            edge_pixels = np.sum(binary_mask > 0)
            total_pixels = binary_mask.shape[0] * binary_mask.shape[1]
            edge_percentage = (edge_pixels / total_pixels) * 100

            result = {
                "mask_shape": list(binary_mask.shape),
                "edge_pixel_count": int(edge_pixels),
                "edge_percentage": round(edge_percentage, 2),
                "threshold_used": threshold,
                "model_info": {
                    "architecture": "UNet",
                    "input_size": self.image_size,
                    "parameters": 31042369,
                    "device": self.device
                }
            }

            # Generate visualization
            if visualize:
                logger.info("Generating visualization...")
                try:
                    visualized_image = create_unet_visualization(
                        str(file_path),
                        binary_mask
                    )
                    if visualized_image:
                        result["visualized_image"] = visualized_image
                        logger.info("✅ Visualization created")
                    else:
                        logger.warning("⚠️ Visualization generation failed")
                except Exception as e:
                    logger.warning(f"⚠️ Visualization error: {e}")

            # Return mask if requested
            if return_mask:
                logger.info("Encoding mask to base64...")
                _, mask_encoded = cv2.imencode('.png', binary_mask)
                mask_base64 = base64.b64encode(mask_encoded).decode('utf-8')
                result["segmentation_mask"] = mask_base64

            logger.info(f"UNet segmentation complete: {edge_pixels} edge pixels ({edge_percentage:.2f}%)")
            return result

        except Exception as e:
            logger.error(f"UNet segmentation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"UNet segmentation failed: {str(e)}"
            )


def check_unet_model_exists(model_path: str) -> bool:
    """UNet 모델 파일 존재 확인"""
    return Path(model_path).exists()
