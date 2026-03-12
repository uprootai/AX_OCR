import { Image, FileImage, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';

interface ImagePreviewCardProps {
  uploadedImage: string | null;
  uploadedFileName: string | null;
  uploadedGTFile: { name: string } | null;
  showImageModal: boolean;
  onShowModal: () => void;
}

export function ImagePreviewCard({
  uploadedImage,
  uploadedFileName,
  uploadedGTFile,
  showImageModal: _showImageModal,
  onShowModal,
}: ImagePreviewCardProps) {
  const { t } = useTranslation();

  return (
    <>
      <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2 text-green-700 dark:text-green-300">
            <FileImage className="w-4 h-4" />
            {t('nodeDetail.currentImage')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {uploadedImage ? (
            <div className="space-y-2">
              <div className="relative group">
                <img
                  src={uploadedImage}
                  alt="Uploaded preview"
                  className="w-full h-auto rounded-lg border border-green-300 dark:border-green-700 max-h-48 object-contain bg-white cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={onShowModal}
                  title="클릭하여 확대"
                />
                <div className="absolute bottom-2 right-2 bg-black/50 text-white text-[10px] px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                  🔍 클릭하여 확대
                </div>
              </div>
              <div
                className="flex items-center gap-2 text-xs text-green-600 dark:text-green-400 cursor-pointer hover:text-green-700"
                onClick={onShowModal}
              >
                <Image className="w-3 h-3" />
                <span className="truncate font-medium">{uploadedFileName || t('nodeDetail.image')}</span>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {t('nodeDetail.size')}: {Math.round(uploadedImage.length / 1024)} KB (base64)
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-gray-400 dark:text-gray-500">
              <Image className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">{t('nodeDetail.noImageUploaded')}</p>
              <p className="text-xs mt-1">{t('nodeDetail.useUploadButton')}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {uploadedGTFile && (
        <div className="flex items-center gap-2 px-3 py-2 text-xs text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 dark:border-amber-700">
          <FileText className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">GT: {uploadedGTFile.name}</span>
        </div>
      )}
    </>
  );
}

interface ImageModalProps {
  uploadedImage: string;
  uploadedFileName: string | null;
  onClose: () => void;
}

export function ImageModal({ uploadedImage, uploadedFileName, onClose }: ImageModalProps) {
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-[90vw] max-h-[90vh] bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-10 w-8 h-8 flex items-center justify-center bg-black/50 hover:bg-black/70 text-white rounded-full transition-colors"
          title="닫기 (ESC)"
        >
          ✕
        </button>
        <img
          src={uploadedImage}
          alt="Uploaded preview full"
          className="max-w-[85vw] max-h-[85vh] object-contain"
        />
        {uploadedFileName && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
            <div className="text-white text-sm font-medium">
              📁 {uploadedFileName}
            </div>
            <div className="text-white/70 text-xs mt-1">
              크기: {Math.round(uploadedImage.length / 1024)} KB (base64) | 클릭하여 닫기
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
