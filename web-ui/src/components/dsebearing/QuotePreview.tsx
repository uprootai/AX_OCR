/**
 * DSE Bearing Quote Preview Component
 * 견적서 미리보기 및 편집 기능 제공
 */

import { useState, useMemo } from 'react';
import { Edit2, Save, X, FileSpreadsheet, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export interface QuoteLineItem {
  no: string;
  description: string;
  material: string;
  material_cost: number;
  labor_cost: number;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface QuoteData {
  success: boolean;
  quote_number: string;
  date: string;
  items: QuoteLineItem[];
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  currency: string;
}

interface QuotePreviewProps {
  quote: QuoteData;
  customerId?: string;
  onEdit?: (updatedQuote: QuoteData) => void;
  onExport?: (format: 'excel' | 'pdf') => void;
}

export function QuotePreview({ quote, customerId, onEdit, onExport }: QuotePreviewProps) {
  const { t } = useTranslation();
  const [isEditing, setIsEditing] = useState(false);
  const [editedItems, setEditedItems] = useState<QuoteLineItem[]>(quote.items);
  const [discountRate, setDiscountRate] = useState(
    quote.subtotal > 0 ? (quote.discount / quote.subtotal) * 100 : 0
  );

  // 편집된 합계 계산
  const calculatedTotals = useMemo(() => {
    const subtotal = editedItems.reduce((sum, item) => sum + item.total_price, 0);
    const discount = subtotal * (discountRate / 100);
    const taxRate = quote.total > 0 ? quote.tax / (quote.total - quote.tax) : 0.1;
    const tax = (subtotal - discount) * taxRate;
    const total = subtotal - discount + tax;
    return { subtotal, discount, tax, total };
  }, [editedItems, discountRate, quote.total, quote.tax]);

  const handleQuantityChange = (index: number, newQty: number) => {
    if (newQty < 1) return;
    const updated = [...editedItems];
    const item = updated[index];
    const unitPrice = item.material_cost + item.labor_cost;
    updated[index] = {
      ...item,
      quantity: newQty,
      total_price: unitPrice * newQty,
    };
    setEditedItems(updated);
  };

  const handleSave = () => {
    const updatedQuote: QuoteData = {
      ...quote,
      items: editedItems,
      ...calculatedTotals,
    };
    onEdit?.(updatedQuote);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedItems(quote.items);
    setDiscountRate(quote.subtotal > 0 ? (quote.discount / quote.subtotal) * 100 : 0);
    setIsEditing(false);
  };

  const formatCurrency = (value: number) => {
    if (quote.currency === 'USD') {
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
    }
    return new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW' }).format(value);
  };

  const displayItems = isEditing ? editedItems : quote.items;
  const displayTotals = isEditing ? calculatedTotals : {
    subtotal: quote.subtotal,
    discount: quote.discount,
    tax: quote.tax,
    total: quote.total,
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold">{t('quote.titleWithEnglish')}</h2>
            <p className="text-blue-100 text-sm mt-1">
              {quote.quote_number}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-100">{t('quote.issueDate')}</p>
            <p className="font-medium">{quote.date}</p>
            {customerId && (
              <p className="text-sm text-blue-100 mt-1">{t('quote.customer')}: {customerId}</p>
            )}
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex justify-between items-center px-6 py-3 bg-gray-50 dark:bg-gray-700 border-b dark:border-gray-600">
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSave}
                className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
              >
                <Save className="h-4 w-4" />
                {t('quote.save')}
              </button>
              <button
                onClick={handleCancel}
                className="flex items-center gap-1 px-3 py-1.5 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
              >
                <X className="h-4 w-4" />
                {t('quote.cancel')}
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            >
              <Edit2 className="h-4 w-4" />
              {t('quote.edit')}
            </button>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onExport?.('excel')}
            className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
            disabled={isEditing}
          >
            <FileSpreadsheet className="h-4 w-4" />
            Excel
          </button>
          <button
            onClick={() => onExport?.('pdf')}
            className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
            disabled={isEditing}
          >
            <FileText className="h-4 w-4" />
            PDF
          </button>
        </div>
      </div>

      {/* Items Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">No</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{t('quote.itemName')}</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{t('quote.material')}</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">{t('quote.materialCost')}</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">{t('quote.laborCost')}</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600 dark:text-gray-300">{t('quote.quantity')}</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">{t('quote.unitPrice')}</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-300">{t('quote.amount')}</th>
            </tr>
          </thead>
          <tbody className="divide-y dark:divide-gray-700">
            {displayItems.map((item, index) => (
              <tr key={item.no} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{item.no}</td>
                <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{item.description}</td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{item.material}</td>
                <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                  {formatCurrency(item.material_cost)}
                </td>
                <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                  {formatCurrency(item.labor_cost)}
                </td>
                <td className="px-4 py-3 text-center">
                  {isEditing ? (
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => handleQuantityChange(index, parseInt(e.target.value) || 1)}
                      className="w-16 px-2 py-1 text-center border rounded dark:bg-gray-700 dark:border-gray-600"
                    />
                  ) : (
                    <span className="text-gray-900 dark:text-gray-100">{item.quantity}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                  {formatCurrency(item.unit_price)}
                </td>
                <td className="px-4 py-3 text-right font-medium text-gray-900 dark:text-gray-100">
                  {formatCurrency(item.total_price)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <div className="px-6 py-4 space-y-2">
          <div className="flex justify-between text-gray-600 dark:text-gray-400">
            <span>{t('quote.subtotal')}</span>
            <span>{formatCurrency(displayTotals.subtotal)}</span>
          </div>
          <div className="flex justify-between items-center text-gray-600 dark:text-gray-400">
            <span className="flex items-center gap-2">
              {t('quote.discount')}
              {isEditing && (
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.5"
                  value={discountRate}
                  onChange={(e) => setDiscountRate(parseFloat(e.target.value) || 0)}
                  className="w-16 px-2 py-0.5 text-center border rounded text-sm dark:bg-gray-700 dark:border-gray-600"
                />
              )}
              {!isEditing && displayTotals.discount > 0 && (
                <span className="text-xs">({((displayTotals.discount / displayTotals.subtotal) * 100).toFixed(1)}%)</span>
              )}
            </span>
            <span className="text-red-600">-{formatCurrency(displayTotals.discount)}</span>
          </div>
          <div className="flex justify-between text-gray-600 dark:text-gray-400">
            <span>{t('quote.tax')}</span>
            <span>{formatCurrency(displayTotals.tax)}</span>
          </div>
          <div className="flex justify-between text-lg font-bold text-gray-900 dark:text-white pt-2 border-t dark:border-gray-600">
            <span>{t('quote.total')}</span>
            <span className="text-blue-600 dark:text-blue-400">{formatCurrency(displayTotals.total)}</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 bg-gray-100 dark:bg-gray-700 text-xs text-gray-500 dark:text-gray-400">
        <p>{t('quote.validityNote')}</p>
        <p>{t('quote.deliveryNote')}</p>
      </div>
    </div>
  );
}

export default QuotePreview;
