#!/usr/bin/env python3
"""
시스템 성능 벤치마크 스크립트

전체 시스템의 성능을 측정하고 개선 전후를 비교합니다.
"""

import asyncio
import time
import httpx
import statistics
from pathlib import Path
from typing import List, Dict
import json

# 테스트 설정
TEST_ITERATIONS = 5
TIMEOUT = 120.0


class BenchmarkResult:
    """벤치마크 결과를 저장하는 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.times: List[float] = []
        self.successes = 0
        self.failures = 0
        self.errors: List[str] = []
    
    def add_success(self, duration: float):
        self.times.append(duration)
        self.successes += 1
    
    def add_failure(self, error: str):
        self.failures += 1
        self.errors.append(error)
    
    def get_stats(self) -> Dict:
        if not self.times:
            return {
                "name": self.name,
                "status": "failed",
                "successes": 0,
                "failures": self.failures,
                "errors": self.errors[:3]  # First 3 errors
            }
        
        return {
            "name": self.name,
            "status": "success",
            "successes": self.successes,
            "failures": self.failures,
            "avg_time": statistics.mean(self.times),
            "min_time": min(self.times),
            "max_time": max(self.times),
            "median_time": statistics.median(self.times),
            "stdev_time": statistics.stdev(self.times) if len(self.times) > 1 else 0
        }
    
    def print_stats(self):
        stats = self.get_stats()
        print(f"\n{'='*60}")
        print(f"📊 {stats['name']}")
        print(f"{'='*60}")
        
        if stats['status'] == 'failed':
            print(f"❌ 모든 테스트 실패 ({stats['failures']}회)")
            print(f"에러: {stats.get('errors', [])}")
            return
        
        print(f"✅ 성공: {stats['successes']}회")
        print(f"❌ 실패: {stats['failures']}회")
        print(f"\n⏱️  처리 시간:")
        print(f"  평균: {stats['avg_time']:.2f}초")
        print(f"  최소: {stats['min_time']:.2f}초")
        print(f"  최대: {stats['max_time']:.2f}초")
        print(f"  중앙값: {stats['median_time']:.2f}초")
        if stats['stdev_time'] > 0:
            print(f"  표준편차: {stats['stdev_time']:.2f}초")


async def benchmark_health_check(url: str, name: str) -> BenchmarkResult:
    """Health check 엔드포인트 벤치마크"""
    result = BenchmarkResult(f"Health Check - {name}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(TEST_ITERATIONS):
            try:
                start = time.time()
                response = await client.get(url)
                duration = time.time() - start
                
                if response.status_code == 200:
                    result.add_success(duration)
                else:
                    result.add_failure(f"HTTP {response.status_code}")
            except Exception as e:
                result.add_failure(str(e))
    
    return result


async def benchmark_ocr_basic(test_file: Path) -> BenchmarkResult:
    """기본 OCR 벤치마크"""
    result = BenchmarkResult("eDOCr2 v1 - Basic OCR")
    
    if not test_file.exists():
        result.add_failure("Test file not found")
        return result
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for i in range(TEST_ITERATIONS):
            try:
                with open(test_file, 'rb') as f:
                    start = time.time()
                    response = await client.post(
                        "http://localhost:5001/api/v1/ocr",
                        files={"file": f},
                        data={"extract_dimensions": "true"}
                    )
                    duration = time.time() - start
                    
                    if response.status_code == 200:
                        data = response.json()
                        dimensions_count = len(data.get("dimensions", []))
                        print(f"  Iteration {i+1}: {duration:.2f}s ({dimensions_count} dimensions)")
                        result.add_success(duration)
                    else:
                        result.add_failure(f"HTTP {response.status_code}")
            except Exception as e:
                result.add_failure(str(e)[:100])
    
    return result


async def benchmark_edgnet(test_file: Path) -> BenchmarkResult:
    """EDGNet 세그멘테이션 벤치마크"""
    result = BenchmarkResult("EDGNet - Segmentation")

    if not test_file.exists():
        result.add_failure("Test file not found")
        return result

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for i in range(TEST_ITERATIONS):
            try:
                with open(test_file, 'rb') as f:
                    start = time.time()
                    response = await client.post(
                        "http://localhost:5012/api/v1/segment",
                        files={"file": f},
                        data={"visualize": "false"}
                    )
                    duration = time.time() - start
                    
                    if response.status_code == 200:
                        data = response.json()
                        components_count = len(data.get("components", []))
                        print(f"  Iteration {i+1}: {duration:.2f}s ({components_count} components)")
                        result.add_success(duration)
                    else:
                        result.add_failure(f"HTTP {response.status_code}")
            except Exception as e:
                result.add_failure(str(e)[:100])
    
    return result


async def benchmark_concurrent_requests(test_file: Path, num_concurrent: int = 5) -> BenchmarkResult:
    """동시 요청 처리 벤치마크"""
    result = BenchmarkResult(f"Concurrent OCR ({num_concurrent} requests)")
    
    if not test_file.exists():
        result.add_failure("Test file not found")
        return result
    
    async def single_request():
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            with open(test_file, 'rb') as f:
                start = time.time()
                response = await client.post(
                    "http://localhost:5001/api/v1/ocr",
                    files={"file": f},
                    data={"extract_dimensions": "true"}
                )
                duration = time.time() - start
                return response.status_code == 200, duration
    
    try:
        start_all = time.time()
        tasks = [single_request() for _ in range(num_concurrent)]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_all
        
        successes = sum(1 for r in results_list if isinstance(r, tuple) and r[0])
        print(f"  {successes}/{num_concurrent} succeeded in {total_duration:.2f}s")
        
        result.add_success(total_duration)
    except Exception as e:
        result.add_failure(str(e))
    
    return result


async def main():
    """메인 벤치마크 실행"""
    print("="*60)
    print("  AX 도면 분석 시스템 - 성능 벤치마크")
    print("="*60)
    print(f"\n테스트 반복 횟수: {TEST_ITERATIONS}회")
    print(f"타임아웃: {TIMEOUT}초")
    
    # 테스트 파일 찾기
    test_file = None
    possible_paths = [
        Path("/home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"),
        Path("/home/uproot/ax/poc/test_data/sample.pdf"),
        Path("/home/uproot/ax/poc/test_data/sample.jpg"),
    ]
    
    for path in possible_paths:
        if path.exists():
            test_file = path
            break
    
    if test_file:
        print(f"테스트 파일: {test_file.name}")
    else:
        print("⚠️  테스트 파일을 찾을 수 없습니다. Health check만 실행합니다.")
    
    # 벤치마크 실행
    results = []
    
    print("\n\n" + "="*60)
    print("1️⃣  Health Check 테스트")
    print("="*60)
    
    health_tests = [
        ("http://localhost:8000/api/v1/health", "Gateway"),
        ("http://localhost:5001/api/v1/health", "eDOCr2 v1"),
        ("http://localhost:5012/api/v1/health", "EDGNet"),
        ("http://localhost:5003/api/v1/health", "Skin Model"),
    ]
    
    for url, name in health_tests:
        result = await benchmark_health_check(url, name)
        result.print_stats()
        results.append(result)
    
    if test_file:
        print("\n\n" + "="*60)
        print("2️⃣  OCR 처리 성능 테스트")
        print("="*60)
        
        ocr_result = await benchmark_ocr_basic(test_file)
        ocr_result.print_stats()
        results.append(ocr_result)
        
        print("\n\n" + "="*60)
        print("3️⃣  EDGNet 세그멘테이션 테스트")
        print("="*60)
        
        edgnet_result = await benchmark_edgnet(test_file)
        edgnet_result.print_stats()
        results.append(edgnet_result)
        
        print("\n\n" + "="*60)
        print("4️⃣  동시 요청 처리 테스트")
        print("="*60)
        
        concurrent_result = await benchmark_concurrent_requests(test_file, num_concurrent=3)
        concurrent_result.print_stats()
        results.append(concurrent_result)
    
    # 최종 요약
    print("\n\n" + "="*60)
    print("📊 전체 벤치마크 요약")
    print("="*60)
    
    all_stats = [r.get_stats() for r in results]
    
    # JSON 저장
    output_file = Path("/home/uproot/ax/poc/benchmark_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "iterations": TEST_ITERATIONS,
            "results": all_stats
        }, f, indent=2)
    
    print(f"\n✅ 결과 저장: {output_file}")
    
    # 간단한 표
    print(f"\n{'서비스':<30} {'평균 시간':<15} {'상태'}")
    print("-" * 60)
    for stat in all_stats:
        if stat['status'] == 'success':
            avg_time = f"{stat['avg_time']:.2f}s"
            status = f"✅ {stat['successes']}/{stat['successes']+stat['failures']}"
        else:
            avg_time = "N/A"
            status = f"❌ {stat['failures']} failed"
        print(f"{stat['name']:<30} {avg_time:<15} {status}")
    
    print("\n" + "="*60)
    print("벤치마크 완료!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
