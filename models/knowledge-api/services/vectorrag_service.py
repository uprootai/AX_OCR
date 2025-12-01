"""
VectorRAG Service
FAISS 기반 벡터 유사도 검색

PPT 슬라이드 13 [WHAT-4] 도메인 지식 엔진 설계:
- 벡터 임베딩으로 자연어 유사도 검색
- OpenAI/Claude 임베딩 API 사용
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

# Optional imports
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("faiss not installed, using mock service")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class VectorRAGService:
    """VectorRAG 서비스 - FAISS 기반 벡터 검색"""

    def __init__(self):
        self.index = None
        self.metadata: List[Dict] = []
        self.dimension = 1536  # OpenAI text-embedding-3-small dimension
        self.index_path = Path("/app/indexes/faiss_index.bin")
        self.metadata_path = Path("/app/indexes/metadata.json")

        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

        logger.info("VectorRAG service initialized")

    async def load_index(self):
        """FAISS 인덱스 로드"""
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available, using mock mode")
            return

        try:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")

                if self.metadata_path.exists():
                    with open(self.metadata_path, 'r') as f:
                        self.metadata = json.load(f)
            else:
                # 빈 인덱스 생성
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine similarity)
                logger.info("Created new empty FAISS index")

        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            self.index = faiss.IndexFlatIP(self.dimension)

    async def save_index(self):
        """FAISS 인덱스 저장"""
        if not FAISS_AVAILABLE or not self.index:
            return

        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path))

            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    async def add_document(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        문서 추가 (임베딩 생성 후 인덱스에 추가)

        Args:
            text: 임베딩할 텍스트
            metadata: 문서 메타데이터 (part_id, name, dimensions 등)
        """
        if not FAISS_AVAILABLE:
            return False

        try:
            # 임베딩 생성
            embedding = await self._get_embedding(text)
            if embedding is None:
                return False

            # 정규화 (cosine similarity를 위해)
            embedding = embedding / np.linalg.norm(embedding)

            # 인덱스에 추가
            self.index.add(embedding.reshape(1, -1).astype('float32'))
            self.metadata.append(metadata)

            logger.info(f"Added document to index: {metadata.get('part_id', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False

    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색

        Args:
            query: 검색 쿼리 텍스트
            top_k: 반환할 결과 수
            threshold: 유사도 임계값

        Returns:
            유사도 높은 문서 리스트
        """
        if not FAISS_AVAILABLE or not self.index or self.index.ntotal == 0:
            return self._get_mock_results(query, top_k)

        try:
            # 쿼리 임베딩 생성
            query_embedding = await self._get_embedding(query)
            if query_embedding is None:
                return self._get_mock_results(query, top_k)

            # 정규화
            query_embedding = query_embedding / np.linalg.norm(query_embedding)

            # 검색
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1).astype('float32'),
                min(top_k, self.index.ntotal)
            )

            # 결과 포맷팅
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < 0 or dist < threshold:
                    continue

                metadata = self.metadata[idx] if idx < len(self.metadata) else {}
                results.append({
                    "id": metadata.get("part_id", f"doc-{idx}"),
                    "text": metadata.get("text", ""),
                    "similarity": float(dist),
                    "metadata": metadata
                })

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self._get_mock_results(query, top_k)

    async def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        텍스트 임베딩 생성 (OpenAI API)
        """
        if not self.openai_api_key or not HTTPX_AVAILABLE:
            # Mock embedding for testing
            return np.random.randn(self.dimension).astype('float32')

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "text-embedding-3-small",
                        "input": text
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    embedding = data["data"][0]["embedding"]
                    return np.array(embedding, dtype='float32')
                else:
                    logger.error(f"Embedding API error: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def _get_mock_results(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Mock 검색 결과 (FAISS 미설치 또는 빈 인덱스 시)"""
        mock_data = [
            {
                "id": "VEC-001",
                "text": "SUS304 Ø50 H7 선반가공 부품",
                "similarity": 0.92,
                "metadata": {
                    "part_id": "VEC-001",
                    "dimensions": ["50", "30"],
                    "tolerance": "H7",
                    "material": "SUS304"
                }
            },
            {
                "id": "VEC-002",
                "text": "AL6061 Ø45 밀링가공 브라켓",
                "similarity": 0.85,
                "metadata": {
                    "part_id": "VEC-002",
                    "dimensions": ["45", "25"],
                    "tolerance": "H8",
                    "material": "AL6061"
                }
            },
            {
                "id": "VEC-003",
                "text": "S45C Ø60 연삭가공 샤프트",
                "similarity": 0.78,
                "metadata": {
                    "part_id": "VEC-003",
                    "dimensions": ["60", "200"],
                    "tolerance": "g6",
                    "material": "S45C"
                }
            },
        ]
        return mock_data[:top_k]
