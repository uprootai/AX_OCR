import { useEffect } from 'react';
import { ExternalLink } from 'lucide-react';

const DOCS_SITE_URL = '/docs/';

export default function Docs() {
  useEffect(() => {
    window.location.href = DOCS_SITE_URL;
  }, []);

  return (
    <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
      <div className="text-center space-y-4">
        <div className="animate-pulse text-muted-foreground text-lg">
          문서 사이트로 이동 중...
        </div>
        <a
          href={DOCS_SITE_URL}
          className="inline-flex items-center gap-2 text-primary hover:underline"
        >
          자동 이동이 안 되면 클릭하세요
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </div>
  );
}
