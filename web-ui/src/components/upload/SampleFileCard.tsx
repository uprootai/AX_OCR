import { memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { FileImage, FileText, Star } from 'lucide-react';

interface SampleFileCardProps {
  name: string;
  description: string;
  type: 'image' | 'pdf';
  recommended?: boolean;
  onSelect: () => void;
  disabled?: boolean;
}

export const SampleFileCard = memo(function SampleFileCard({
  name,
  description,
  type,
  recommended = false,
  onSelect,
  disabled = false
}: SampleFileCardProps) {
  const Icon = type === 'image' ? FileImage : FileText;

  return (
    <Card
      className={`
        relative transition-all duration-200 cursor-pointer
        hover:shadow-lg hover:scale-[1.02] hover:border-primary/50
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onClick={disabled ? undefined : onSelect}
    >
      {recommended && (
        <div className="absolute -top-2 -right-2 z-10">
          <Badge variant="default" className="gap-1 shadow-md">
            <Star className="h-3 w-3 fill-current" />
            권장
          </Badge>
        </div>
      )}

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className={`
            p-3 rounded-lg
            ${type === 'image' ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400' : 'bg-red-500/10 text-red-600 dark:text-red-400'}
          `}>
            <Icon className="h-6 w-6" />
          </div>
          <Badge variant="outline" className="text-xs">
            {type === 'image' ? 'IMAGE' : 'PDF'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div>
          <CardTitle className="text-sm font-semibold mb-1 line-clamp-2">
            {name}
          </CardTitle>
          <CardDescription className="text-xs line-clamp-2">
            {description}
          </CardDescription>
        </div>

        <Button
          size="sm"
          className="w-full"
          variant="outline"
          disabled={disabled}
          onClick={(e) => {
            e.stopPropagation();
            if (!disabled) onSelect();
          }}
        >
          선택
        </Button>
      </CardContent>
    </Card>
  );
});
