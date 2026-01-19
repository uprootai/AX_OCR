import requests
import json

# Test workflow: imageinput -> yolo -> blueprint-ai-bom
workflow_request = {
    "workflow": {
        "id": "test-workflow",
        "name": "Test Workflow Order",
        "nodes": [
            {"id": "node_0", "type": "imageinput", "position": {"x": 100, "y": 100}, "parameters": {}},
            {"id": "node_1", "type": "blueprint-ai-bom", "position": {"x": 500, "y": 100}, "parameters": {}},
            {"id": "node_2", "type": "yolo", "position": {"x": 300, "y": 100}, "parameters": {"confidence": 0.4}}
        ],
        "edges": [
            {"id": "e1", "source": "node_0", "target": "node_2"},  # imageinput -> yolo
            {"id": "e2", "source": "node_2", "target": "node_1"}   # yolo -> blueprint-ai-bom
        ]
    },
    "inputs": {"image": "test"},
    "config": {"execution_mode": "sequential"}
}

print("Sending workflow request:")
print(f"Nodes: {[(n['id'], n['type']) for n in workflow_request['workflow']['nodes']]}")
print(f"Edges: {[(e['source'], '->', e['target']) for e in workflow_request['workflow']['edges']]}")

# Just validate, don't actually execute
response = requests.post(
    "http://localhost:8000/api/v1/workflow/validate",
    json=workflow_request['workflow']
)
print(f"\nValidation response: {response.json()}")
