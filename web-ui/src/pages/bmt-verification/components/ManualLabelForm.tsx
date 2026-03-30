import { useState } from 'react';
import { Plus, ChevronDown, ChevronRight, CheckCircle } from 'lucide-react';

interface ManualLabelFormProps {
  onSubmit: (tagCode: string, partName: string) => void;
}

export default function ManualLabelForm({ onSubmit }: ManualLabelFormProps) {
  const [open, setOpen] = useState(false);
  const [tagCode, setTagCode] = useState('');
  const [partName, setPartName] = useState('');
  const [toast, setToast] = useState(false);

  const handleSubmit = () => {
    if (!tagCode.trim() || !partName.trim()) return;
    onSubmit(tagCode.trim(), partName.trim());
    setTagCode('');
    setPartName('');
    setToast(true);
    setTimeout(() => setToast(false), 2000);
  };

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
      >
        {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <Plus size={16} className="text-green-600 dark:text-green-400" />
        <span>수작업 TAG 추가</span>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100 dark:border-gray-700 pt-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">TAG 코드</label>
            <input
              value={tagCode}
              onChange={(e) => setTagCode(e.target.value)}
              placeholder="V15"
              className="w-full px-3 py-1.5 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-gray-200"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">부품명</label>
            <input
              value={partName}
              onChange={(e) => setPartName(e.target.value)}
              placeholder="Check Valve"
              className="w-full px-3 py-1.5 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-gray-200"
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={!tagCode.trim() || !partName.trim()}
            className="w-full py-2 rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            추가
          </button>
        </div>
      )}

      {toast && (
        <div className="fixed bottom-6 right-6 flex items-center gap-2 px-4 py-2.5 rounded-lg bg-green-600 text-white text-sm shadow-lg animate-fade-in z-50">
          <CheckCircle size={16} />
          TAG 추가 완료
        </div>
      )}
    </div>
  );
}
