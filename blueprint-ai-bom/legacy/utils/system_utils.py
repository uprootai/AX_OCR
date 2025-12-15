"""
System Utilities
시스템 관련 유틸리티 함수들
"""
import subprocess
import streamlit as st
from typing import Dict, Any

def get_gpu_status() -> Dict[str, Any]:
    """GPU 상태 확인"""
    try:
        result = subprocess.run([
            'nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            gpu_info = result.stdout.strip().split(', ')
            memory_used = int(gpu_info[0])
            memory_total = int(gpu_info[1])
            gpu_util = int(gpu_info[2])
            return {
                "memory_used": memory_used,
                "memory_total": memory_total,
                "memory_percent": (memory_used / memory_total) * 100,
                "gpu_util": gpu_util,
                "available": True
            }
    except:
        pass
    return {"available": False}

def clear_model_cache():
    """모델 캐시 정리"""
    # 세션 상태에서 모델 캐시 정리
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('model_') or key.startswith('yolo_model_cache_') or key.startswith('fallback_model_'):
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del st.session_state[key]

def clear_all_cache():
    """모든 캐시 및 세션 상태 정리"""
    # Streamlit 캐시 정리
    st.cache_data.clear()
    st.cache_resource.clear()

    # 세션 상태 정리 (보존해야 할 항목 제외)
    preserved_keys = ['current_image', 'original_image']
    keys_to_remove = [key for key in st.session_state.keys() if key not in preserved_keys]

    for key in keys_to_remove:
        del st.session_state[key]

    # 수동 가비지 컬렉션
    import gc
    gc.collect()

    # GPU 메모리 정리 (가능한 경우)
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass