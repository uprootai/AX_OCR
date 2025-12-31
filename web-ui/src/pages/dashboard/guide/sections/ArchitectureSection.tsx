import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/Card';
import Mermaid from '../../../../components/ui/Mermaid';
import ImageZoom from '../../../../components/ui/ImageZoom';
import { Layers } from 'lucide-react';

interface ArchitectureSectionProps {
  sectionRef: (el: HTMLElement | null) => void;
}

export function ArchitectureSection({ sectionRef }: ArchitectureSectionProps) {
  const { t } = useTranslation();

  const architectureChart = `flowchart TB
    subgraph Frontend["Frontend :5173"]
        UI[Web UI + BlueprintFlow]
    end

    subgraph Gateway["Gateway :8000"]
        GW[Orchestrator]
    end

    subgraph Detection["Detection"]
        YOLO[YOLO :5005]
    end

    subgraph OCR["OCR"]
        direction LR
        ED[eDOCr2 :5002]
        PD[PaddleOCR :5006]
        TE[Tesseract :5008]
        TR[TrOCR :5009]
        EN[Ensemble :5011]
    end

    subgraph Segmentation["Segmentation"]
        EG[EDGNet :5012]
        LD[LineDetector :5016]
    end

    subgraph Preprocessing["Preprocessing"]
        ES[ESRGAN :5010]
    end

    subgraph Analysis["Analysis"]
        SK[SkinModel :5003]
        PA[PID-Analyzer :5018]
        DC[DesignChecker :5019]
    end

    subgraph AI["AI"]
        VL[VL :5004]
    end

    subgraph Knowledge["Knowledge"]
        KN[Knowledge :5007]
    end

    UI --> GW
    GW --> Detection
    GW --> OCR
    GW --> Segmentation
    GW --> Preprocessing
    GW --> Analysis
    GW --> AI
    GW --> Knowledge

    style Frontend fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Gateway fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Detection fill:#dbeafe,stroke:#3b82f6,stroke-width:2px
    style OCR fill:#dcfce7,stroke:#22c55e,stroke-width:2px
    style Segmentation fill:#fae8ff,stroke:#d946ef,stroke-width:2px
    style Preprocessing fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    style Analysis fill:#ffe4e6,stroke:#f43f5e,stroke-width:2px
    style AI fill:#e0e7ff,stroke:#6366f1,stroke-width:2px
    style Knowledge fill:#f3e8ff,stroke:#a855f7,stroke-width:2px`;

  return (
    <section
      id="architecture"
      ref={sectionRef}
      className="mb-12 scroll-mt-20"
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Layers className="w-5 h-5 mr-2" />
            {t('guide.systemArchitecture')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">
                {t('guide.systemStructure')}
              </h3>
              <ImageZoom>
                <Mermaid chart={architectureChart} />
              </ImageZoom>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
