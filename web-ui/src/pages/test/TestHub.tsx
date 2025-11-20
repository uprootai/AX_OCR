import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const tests = [
  { name: 'Gateway API', href: '/test/gateway', descKey: 'gatewayDesc', badge: '⭐ 추천', badgeColor: 'blue' },
  { name: 'YOLOv11 API', href: '/test/yolo', descKey: 'yoloDesc', badge: 'GPU', badgeColor: 'green' },
  { name: 'eDOCr2 API', href: '/test/edocr2', descKey: 'edocr2Desc', badge: 'GPU', badgeColor: 'green' },
  { name: 'PaddleOCR API', href: 'https://github.com/PaddlePaddle/PaddleOCR', descKey: 'paddleocrDesc', badge: 'GPU', badgeColor: 'green', external: true },
  { name: 'EDGNet API', href: '/test/edgnet', descKey: 'edgnetDesc', badge: 'GPU', badgeColor: 'green' },
  { name: 'Skin Model API', href: '/test/skinmodel', descKey: 'skinmodelDesc' },
  { name: 'VL API', href: 'https://docs.anthropic.com/claude/docs/vision', descKey: 'vlDesc', badge: 'Cloud', badgeColor: 'purple', external: true },
];

export default function TestHub() {
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t('testHub.title')}</h1>
      <p className="text-muted-foreground mb-8">
        {t('testHub.subtitle')}
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
                <p className="text-sm text-muted-foreground">{t(`testHub.${test.descKey}`)}</p>
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
              <p className="text-sm text-muted-foreground">{t(`testHub.${test.descKey}`)}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
