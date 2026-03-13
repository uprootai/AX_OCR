import type { FilterCheckboxProps } from './types';

export const FilterCheckbox = ({ label, icon, count, checked, onChange, color }: FilterCheckboxProps) => (
  <label
    className={`flex items-center gap-1 px-2 py-1 rounded cursor-pointer transition-colors ${
      checked ? 'bg-gray-100 dark:bg-gray-700' : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
    }`}
  >
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
      className="w-3 h-3 rounded"
    />
    <span className="text-xs">{icon}</span>
    <span className={`text-xs font-medium ${color}`}>{label}: {count}</span>
  </label>
);
