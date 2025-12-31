# Export 가능한 납품 아키텍처 설계

> **작성일**: 2025-12-14
> **목적**: 빌더에서 생성한 템플릿 + BOM Verification을 고객 온프레미스로 export
> **상태**: 설계 단계

---

## 핵심 개념

```
┌─────────────────────────────────────────────────────────────────┐
│                    AX POC (개발/빌더 환경)                       │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ BlueprintFlow │  │  API 테스트   │  │  템플릿 관리  │       │
│  │ Builder       │  │  Dashboard    │  │               │       │
│  └───────┬───────┘  └───────────────┘  └───────┬───────┘       │
│          │                                      │               │
│          └──────────────┬───────────────────────┘               │
│                         ▼                                       │
│              ┌─────────────────────┐                           │
│              │   Export Package    │                           │
│              │   (템플릿 + 설정)   │                           │
│              └──────────┬──────────┘                           │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 고객 온프레미스 (런타임 환경)                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                  Standalone App                           │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │ 도면 업로드 │→ │ AI 분석     │→ │ BOM 검증    │       │ │
│  │  │             │  │ (템플릿)    │  │ & 출력      │       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  빌더 UI 없음 / 선택된 템플릿만 실행 / 경량화                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 아키텍처 설계

### 1. 프론트엔드 모듈 분리

```
web-ui/src/
├── modules/
│   ├── builder/                    # 빌더 전용 (납품에서 제외)
│   │   ├── BlueprintFlowBuilder.tsx
│   │   ├── NodePalette.tsx
│   │   ├── TemplateManager.tsx
│   │   └── index.ts
│   │
│   ├── runtime/                    # 런타임 (납품 포함)
│   │   ├── WorkflowRunner.tsx      # 템플릿 실행기
│   │   ├── TemplateSelector.tsx    # 템플릿 선택 UI
│   │   └── index.ts
│   │
│   ├── verification/               # BOM 검증 (납품 포함)
│   │   ├── VerificationPage.tsx
│   │   ├── BoundingBoxEditor.tsx
│   │   ├── DetectionList.tsx
│   │   ├── ApprovalWorkflow.tsx
│   │   └── index.ts
│   │
│   └── common/                     # 공통 컴포넌트 (납품 포함)
│       ├── ImageViewer.tsx
│       ├── FileUploader.tsx
│       ├── ExportButtons.tsx
│       └── index.ts
│
├── apps/
│   ├── full/                       # 전체 앱 (개발용)
│   │   ├── App.tsx
│   │   ├── routes.tsx
│   │   └── main.tsx
│   │
│   └── standalone/                 # 납품용 앱
│       ├── App.tsx                 # 경량화된 앱
│       ├── routes.tsx              # 최소 라우트
│       └── main.tsx
│
└── vite.config.ts                  # 멀티 빌드 설정
```

### 2. 멀티 빌드 설정

```typescript
// vite.config.ts

import { defineConfig } from 'vite';

export default defineConfig(({ mode }) => {
  const isStandalone = mode === 'standalone';

  return {
    build: {
      outDir: isStandalone ? 'dist/standalone' : 'dist/full',
      rollupOptions: {
        input: isStandalone
          ? './src/apps/standalone/main.tsx'
          : './src/apps/full/main.tsx',
      },
    },
    define: {
      __BUILD_MODE__: JSON.stringify(isStandalone ? 'standalone' : 'full'),
    },
  };
});
```

```bash
# 빌드 명령어
npm run build              # 전체 빌드 (개발용)
npm run build:standalone   # 납품용 빌드
```

---

### 3. 템플릿 Export 구조

```
exported_package/
├── config/
│   ├── template.json              # 워크플로우 템플릿
│   ├── api_config.json            # API 설정 (URL, 포트)
│   ├── class_definitions.json     # 검출 클래스 정의
│   └── pricing_data.json          # 가격 데이터 (옵션)
│
├── frontend/
│   └── dist/                      # 빌드된 standalone 앱
│       ├── index.html
│       ├── assets/
│       └── ...
│
├── backend/
│   ├── gateway/                   # 경량 Gateway
│   │   ├── api_server.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── api_specs/                 # 필요한 API 스펙만
│       ├── yolo.yaml
│       └── ...
│
├── models/                        # 필요한 모델만
│   ├── yolo/
│   │   └── best.pt
│   └── ...
│
├── docker/
│   ├── docker-compose.yml         # 최소 구성
│   ├── docker-compose.override.yml
│   └── .env.example
│
├── scripts/
│   ├── install.sh                 # 설치 스크립트
│   ├── start.sh                   # 시작 스크립트
│   ├── stop.sh                    # 중지 스크립트
│   └── backup.sh                  # 백업 스크립트
│
└── docs/
    ├── INSTALL.md                 # 설치 가이드
    ├── USER_MANUAL.md             # 사용자 매뉴얼
    └── ADMIN_GUIDE.md             # 관리자 가이드
```

---

### 4. 템플릿 JSON 구조

```json
// config/template.json
{
  "meta": {
    "id": "techcross-pid-analysis",
    "name": "P&ID 도면 분석",
    "version": "1.0.0",
    "created_at": "2025-12-14",
    "created_by": "AX POC Builder",
    "description": "P&ID 도면에서 심볼 검출 및 BOM 생성"
  },

  "workflow": {
    "nodes": [
      {
        "id": "input_1",
        "type": "ImageInput",
        "config": {
          "accepted_formats": ["pdf", "png", "jpg"],
          "max_size_mb": 50
        }
      },
      {
        "id": "yolo_1",
        "type": "YOLO",
        "config": {
          "model": "yolo/best.pt",
          "confidence": 0.7,
          "iou_threshold": 0.45,
          "classes": "all"
        }
      },
      {
        "id": "verification_1",
        "type": "Verification",
        "config": {
          "require_approval": true,
          "auto_approve_threshold": 0.95,
          "enable_manual_add": true
        }
      },
      {
        "id": "bom_1",
        "type": "BOMGenerator",
        "config": {
          "pricing_enabled": true,
          "export_formats": ["excel", "pdf"]
        }
      }
    ],

    "edges": [
      { "source": "input_1", "target": "yolo_1" },
      { "source": "yolo_1", "target": "verification_1" },
      { "source": "verification_1", "target": "bom_1" }
    ]
  },

  "required_apis": [
    {
      "id": "yolo",
      "port": 5005,
      "required": true
    }
  ],

  "class_definitions": {
    "source": "classes_info_with_pricing.json",
    "count": 27
  }
}
```

---

### 5. Export 워크플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                    AX POC Builder                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: 템플릿 설계                                              │
│ - BlueprintFlow에서 워크플로우 구성                              │
│ - 노드 연결 및 파라미터 설정                                     │
│ - 테스트 실행으로 검증                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Export 설정                                              │
│ - 고객사 정보 입력                                               │
│ - 포함할 API 선택                                                │
│ - 라이선스 설정 (옵션)                                           │
│ - 브랜딩 설정 (로고, 색상)                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Package 생성                                             │
│ - Frontend 빌드 (standalone 모드)                                │
│ - 필요한 API만 포함                                              │
│ - 모델 파일 복사                                                 │
│ - Docker 이미지 생성                                             │
│ - 설치 스크립트 생성                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: 배포 패키지                                              │
│                                                                  │
│  techcross-pid-v1.0.0.tar.gz                                    │
│  ├── docker-images/         # Docker 이미지 tar                  │
│  ├── config/                # 템플릿 + 설정                      │
│  ├── scripts/               # 설치/시작/백업 스크립트            │
│  └── docs/                  # 문서                               │
│                                                                  │
│  용량: ~2-5GB (모델 포함)                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### 6. Export Manager UI

```typescript
// web-ui/src/modules/builder/ExportManager.tsx

interface ExportConfig {
  customer: {
    name: string;
    logo?: string;
    primaryColor?: string;
  };
  template: {
    id: string;
    name: string;
    workflow: WorkflowDefinition;
  };
  apis: {
    id: string;
    include: boolean;
    port: number;
  }[];
  options: {
    includeModels: boolean;
    includePricing: boolean;
    generateDocs: boolean;
    dockerFormat: 'tar' | 'registry';
  };
}

const ExportManager: React.FC = () => {
  const [config, setConfig] = useState<ExportConfig>(defaultConfig);
  const [exportProgress, setExportProgress] = useState(0);

  const handleExport = async () => {
    // 1. Validate template
    const validation = await validateTemplate(config.template);
    if (!validation.valid) {
      showError(validation.errors);
      return;
    }

    // 2. Build frontend (standalone)
    setExportProgress(10);
    await buildFrontend('standalone', config.customer);

    // 3. Package APIs
    setExportProgress(30);
    await packageAPIs(config.apis.filter(a => a.include));

    // 4. Copy models
    setExportProgress(50);
    await copyModels(config.template.workflow);

    // 5. Generate configs
    setExportProgress(70);
    await generateConfigs(config);

    // 6. Create Docker images
    setExportProgress(85);
    await createDockerImages(config.options.dockerFormat);

    // 7. Generate docs
    setExportProgress(95);
    if (config.options.generateDocs) {
      await generateDocs(config);
    }

    // 8. Create final package
    setExportProgress(100);
    const packagePath = await createPackage(config);

    showSuccess(`패키지 생성 완료: ${packagePath}`);
  };

  return (
    <div className="export-manager">
      <h2>납품 패키지 생성</h2>

      {/* 고객 정보 */}
      <CustomerInfoSection config={config} onChange={setConfig} />

      {/* 템플릿 선택 */}
      <TemplateSection config={config} onChange={setConfig} />

      {/* API 선택 */}
      <APISelectionSection config={config} onChange={setConfig} />

      {/* 옵션 */}
      <OptionsSection config={config} onChange={setConfig} />

      {/* 미리보기 */}
      <PackagePreview config={config} />

      {/* Export 버튼 */}
      <Button onClick={handleExport} disabled={exportProgress > 0}>
        {exportProgress > 0 ? `생성 중... ${exportProgress}%` : '패키지 생성'}
      </Button>
    </div>
  );
};
```

---

### 7. 납품용 Standalone App 구조

```typescript
// web-ui/src/apps/standalone/App.tsx

const StandaloneApp: React.FC = () => {
  const [template, setTemplate] = useState<Template | null>(null);

  useEffect(() => {
    // 패키지에 포함된 템플릿 로드
    loadTemplate('/config/template.json').then(setTemplate);
  }, []);

  if (!template) return <Loading />;

  return (
    <StandaloneLayout>
      <Routes>
        {/* 빌더 없음 - 런타임만 */}
        <Route path="/" element={<WorkflowRunner template={template} />} />
        <Route path="/verification/:sessionId" element={<VerificationPage />} />
        <Route path="/results/:sessionId" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </StandaloneLayout>
  );
};

// 간소화된 워크플로우 러너
const WorkflowRunner: React.FC<{ template: Template }> = ({ template }) => {
  const [step, setStep] = useState<'upload' | 'processing' | 'verification'>('upload');
  const [sessionId, setSessionId] = useState<string | null>(null);

  const handleUpload = async (files: File[]) => {
    setStep('processing');

    // 템플릿에 정의된 워크플로우 자동 실행
    const result = await executeWorkflow(template.workflow, files);
    setSessionId(result.sessionId);

    // 검증이 필요하면 검증 페이지로
    if (template.workflow.requiresVerification) {
      setStep('verification');
    }
  };

  return (
    <div className="workflow-runner">
      {step === 'upload' && (
        <FileUploadZone
          title={template.name}
          description={template.description}
          onUpload={handleUpload}
        />
      )}

      {step === 'processing' && (
        <ProcessingStatus sessionId={sessionId} />
      )}

      {step === 'verification' && sessionId && (
        <Navigate to={`/verification/${sessionId}`} />
      )}
    </div>
  );
};
```

---

### 8. 납품용 Docker Compose

```yaml
# exported_package/docker/docker-compose.yml

version: '3.8'

services:
  # 프론트엔드 (Nginx)
  web:
    image: ${CUSTOMER_NAME:-customer}/web:${VERSION:-1.0.0}
    ports:
      - "${WEB_PORT:-80}:80"
    depends_on:
      - gateway
    restart: unless-stopped

  # API Gateway (경량화)
  gateway:
    image: ${CUSTOMER_NAME:-customer}/gateway:${VERSION:-1.0.0}
    ports:
      - "${GATEWAY_PORT:-8000}:8000"
    environment:
      - TEMPLATE_PATH=/config/template.json
      - API_CONFIG_PATH=/config/api_config.json
    volumes:
      - ./config:/config:ro
      - ./data:/data
    depends_on:
      - yolo-api
    restart: unless-stopped

  # YOLO API (필수)
  yolo-api:
    image: ${CUSTOMER_NAME:-customer}/yolo-api:${VERSION:-1.0.0}
    ports:
      - "${YOLO_PORT:-5005}:5005"
    volumes:
      - ./models/yolo:/models:ro
    environment:
      - MODEL_PATH=/models/best.pt
      - DEVICE=${DEVICE:-cuda}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  # BOM API (필수)
  bom-api:
    image: ${CUSTOMER_NAME:-customer}/bom-api:${VERSION:-1.0.0}
    ports:
      - "${BOM_PORT:-5020}:5020"
    volumes:
      - ./config:/config:ro
      - ./data:/data
    restart: unless-stopped

# 볼륨 (데이터 영속성)
volumes:
  data:
```

---

### 9. Export 스크립트

```python
# scripts/export_package.py

import argparse
import subprocess
import shutil
import json
from pathlib import Path

class PackageExporter:
    def __init__(self, config_path: str, output_dir: str):
        self.config = json.load(open(config_path))
        self.output_dir = Path(output_dir)

    def export(self):
        """전체 Export 프로세스"""
        print("🚀 납품 패키지 생성 시작...")

        # 1. 출력 디렉토리 생성
        self.setup_directories()

        # 2. Frontend 빌드
        print("📦 Frontend 빌드 중...")
        self.build_frontend()

        # 3. Backend 패키징
        print("📦 Backend 패키징 중...")
        self.package_backend()

        # 4. 모델 복사
        print("📦 모델 파일 복사 중...")
        self.copy_models()

        # 5. 설정 파일 생성
        print("⚙️ 설정 파일 생성 중...")
        self.generate_configs()

        # 6. Docker 이미지 빌드
        print("🐳 Docker 이미지 빌드 중...")
        self.build_docker_images()

        # 7. 문서 생성
        print("📚 문서 생성 중...")
        self.generate_docs()

        # 8. 최종 패키지 생성
        print("📦 최종 패키지 생성 중...")
        self.create_final_package()

        print(f"✅ 완료: {self.output_dir}")

    def setup_directories(self):
        dirs = ['config', 'frontend', 'backend', 'models', 'docker', 'scripts', 'docs']
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)

    def build_frontend(self):
        subprocess.run([
            'npm', 'run', 'build:standalone',
            '--', f'--outDir={self.output_dir}/frontend/dist'
        ], cwd='web-ui', check=True)

    def package_backend(self):
        # 필요한 API만 복사
        required_apis = self.config['required_apis']
        for api in required_apis:
            if api.get('include', True):
                src = Path(f"models/{api['id']}-api")
                dst = self.output_dir / 'backend' / f"{api['id']}-api"
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

    def copy_models(self):
        # 워크플로우에서 사용하는 모델만 복사
        for node in self.config['workflow']['nodes']:
            if 'model' in node.get('config', {}):
                model_path = node['config']['model']
                src = Path(f"models/{model_path}")
                dst = self.output_dir / 'models' / model_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    def generate_configs(self):
        # template.json
        template_config = {
            'meta': self.config['meta'],
            'workflow': self.config['workflow'],
            'required_apis': self.config['required_apis']
        }
        with open(self.output_dir / 'config' / 'template.json', 'w') as f:
            json.dump(template_config, f, indent=2, ensure_ascii=False)

        # api_config.json
        api_config = {
            api['id']: {'port': api['port'], 'url': f"http://{api['id']}-api:{api['port']}"}
            for api in self.config['required_apis']
        }
        with open(self.output_dir / 'config' / 'api_config.json', 'w') as f:
            json.dump(api_config, f, indent=2)

    def build_docker_images(self):
        # Docker Compose로 이미지 빌드
        subprocess.run([
            'docker', 'compose', 'build'
        ], cwd=self.output_dir / 'docker', check=True)

        # 이미지를 tar로 저장
        images_dir = self.output_dir / 'docker-images'
        images_dir.mkdir(exist_ok=True)

        for service in ['web', 'gateway', 'yolo-api', 'bom-api']:
            image_name = f"{self.config['meta']['id']}/{service}"
            subprocess.run([
                'docker', 'save', '-o',
                str(images_dir / f'{service}.tar'),
                image_name
            ], check=True)

    def generate_docs(self):
        # 설치 가이드 생성
        install_md = self.generate_install_guide()
        with open(self.output_dir / 'docs' / 'INSTALL.md', 'w') as f:
            f.write(install_md)

        # 사용자 매뉴얼 생성
        user_md = self.generate_user_manual()
        with open(self.output_dir / 'docs' / 'USER_MANUAL.md', 'w') as f:
            f.write(user_md)

    def create_final_package(self):
        package_name = f"{self.config['meta']['id']}-v{self.config['meta']['version']}"
        shutil.make_archive(
            str(self.output_dir.parent / package_name),
            'gztar',
            self.output_dir
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Export config JSON')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    exporter = PackageExporter(args.config, args.output)
    exporter.export()
```

---

## 요약: 빌더 vs 런타임 분리

| 구분 | AX POC (빌더) | 납품 패키지 (런타임) |
|------|---------------|---------------------|
| **용도** | 워크플로우 설계, 테스트 | 실제 업무 사용 |
| **UI** | BlueprintFlow + Dashboard | 간소화된 실행 UI |
| **API** | 19개 전체 | 필요한 것만 |
| **모델** | 모든 버전 | 선택된 것만 |
| **크기** | ~50GB+ | ~2-5GB |
| **설정** | 동적 변경 가능 | 템플릿 고정 |

---

## 구현 우선순위

| 단계 | 작업 | 기간 |
|------|------|------|
| 1 | 프론트엔드 모듈 분리 (builder/runtime/verification) | 2일 |
| 2 | Standalone 앱 구조 구현 | 2일 |
| 3 | 템플릿 JSON 스키마 정의 | 1일 |
| 4 | Export Manager UI | 3일 |
| 5 | Export 스크립트 | 2일 |
| 6 | 납품용 Docker 구성 | 1일 |
| **합계** | | **11일** |

---

## 관련 문서

- **통합 전략**: `2025-12-14_integration_strategy.md`
- **프로젝트 구조**: `2025-12-14_project_structure.md`
