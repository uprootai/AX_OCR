#!/usr/bin/env python3
"""Test script to verify model registry default model selection"""

import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_ai_app import ModelRegistry

def test_model_registry():
    """Test the model registry to see which model is marked as default"""
    try:
        # Initialize the model registry
        model_registry = ModelRegistry()

        print("📁 Model Registry Contents:")
        print(f"Registry loaded from: {model_registry.registry_path}")
        print(f"Total models: {len(model_registry.registry.get('models', {}))}")
        print()

        # List all models with their status
        print("📋 All models in registry:")
        for model_id, model_info in model_registry.registry.get('models', {}).items():
            default_status = "✅ DEFAULT" if model_info.get('default', False) else "❌ not default"
            active_status = "✅ ACTIVE" if model_info.get('active', False) else "❌ inactive"
            print(f"  {model_id}: {model_info.get('name', 'Unknown')} - {default_status}, {active_status}")
            print(f"    Path: {model_info.get('path', 'No path')}")
            print()

        # Test get_default_model method
        print("🎯 Testing get_default_model() method:")
        default_result = model_registry.get_default_model()

        if default_result:
            model_id, model_info = default_result
            print(f"✅ Default model found: {model_id}")
            print(f"   Name: {model_info.get('name', 'Unknown')}")
            print(f"   Path: {model_info.get('path', 'No path')}")
            print(f"   Description: {model_info.get('description', 'No description')}")
        else:
            print("❌ No default model found!")

        # Test get_available_models method
        print("\n🔍 Testing get_available_models() method:")
        available_models = model_registry.get_available_models()
        print(f"Available models: {list(available_models.keys())}")

        return default_result

    except Exception as e:
        print(f"❌ Error testing model registry: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 Testing Model Registry Default Selection")
    print("=" * 50)
    result = test_model_registry()

    if result:
        model_id, model_info = result
        print(f"\n🎉 SUCCESS: Default model is '{model_id}' (should be 'yolo_v11n')")
        if model_id == 'yolo_v11n':
            print("✅ Correct! YOLOv11n is set as default")
        else:
            print(f"❌ Incorrect! Expected 'yolo_v11n' but got '{model_id}'")
    else:
        print("\n❌ FAILED: No default model found")