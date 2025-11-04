import { Link } from 'react-router-dom';

const tests = [
  { name: 'YOLOv11 API', href: '/test/yolo', description: '공학 도면 객체 검출 (mAP50: 80.4%, 권장)', badge: '⭐ 권장', badgeColor: 'blue' },
  { name: 'eDOCr v1/v2 API', href: '/test/edocr2', description: 'OCR 테스트 (v1 GPU 가속, v2 고급 기능)', badge: 'GPU', badgeColor: 'green' },
  { name: 'EDGNet API', href: '/test/edgnet', description: '세그멘테이션 테스트' },
  { name: 'Skin Model API', href: '/test/skinmodel', description: '공차 예측 테스트' },
  { name: 'Gateway API', href: '/test/gateway', description: '통합 테스트' },
];

export default function TestHub() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">API Tests</h1>
      <p className="text-muted-foreground mb-8">
        각 API를 개별적으로 테스트할 수 있습니다.
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        {tests.map((test) => (
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
                    : 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                }`}>
                  {test.badge}
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{test.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
