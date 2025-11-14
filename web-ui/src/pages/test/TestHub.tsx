import { Link } from 'react-router-dom';

const tests = [
  { name: 'Gateway API', href: '/test/gateway', description: '통합 파이프라인 테스트 (추천)', badge: '⭐ 추천', badgeColor: 'blue' },
  { name: 'YOLOv11 API', href: '/test/yolo', description: '공학 도면 객체 검출 (mAP50: 80.4%)', badge: 'GPU', badgeColor: 'green' },
  { name: 'eDOCr2 API', href: '/test/edocr2', description: '한글 OCR (GPU 가속)', badge: 'GPU', badgeColor: 'green' },
  { name: 'PaddleOCR API', href: 'https://github.com/PaddlePaddle/PaddleOCR', description: '다국어 OCR (GPU 가속)', badge: 'GPU', badgeColor: 'green', external: true },
  { name: 'EDGNet API', href: '/test/edgnet', description: '도면 세그멘테이션', badge: 'GPU', badgeColor: 'green' },
  { name: 'Skin Model API', href: '/test/skinmodel', description: '공차 예측 및 제조 가능성 분석' },
  { name: 'VL API', href: 'https://docs.anthropic.com/claude/docs/vision', description: '비전-언어 멀티모달 분석', badge: 'Cloud', badgeColor: 'purple', external: true },
];

export default function TestHub() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">API Tests</h1>
      <p className="text-muted-foreground mb-8">
        각 API를 개별적으로 테스트할 수 있습니다.
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        {tests.map((test) => {
          if (test.external) {
            return (
              <a
                key={test.name}
                href={test.href}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-6 bg-card border rounded-lg hover:border-primary transition-colors"
              >
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-xl font-semibold">{test.name}</h3>
                  {test.badge && (
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded ${
                      test.badgeColor === 'blue'
                        ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                        : test.badgeColor === 'green'
                        ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                        : 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300'
                    }`}>
                      {test.badge}
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">{test.description}</p>
              </a>
            );
          }

          return (
            <Link
              key={test.name}
              to={test.href}
              className="block p-6 bg-card border rounded-lg hover:border-primary transition-colors"
            >
              <div className="flex items-center gap-2 mb-2">
                <h3 className="text-xl font-semibold">{test.name}</h3>
                {test.badge && (
                  <span className={`px-2 py-0.5 text-xs font-semibold rounded ${
                    test.badgeColor === 'blue'
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                      : test.badgeColor === 'green'
                      ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                      : 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300'
                  }`}>
                    {test.badge}
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground">{test.description}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
