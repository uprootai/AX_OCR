/**
 * ImagePreviewModal Component
 * 업로드된 이미지 확대 모달
 */

interface ImagePreviewModalProps {
  uploadedImage: string;
  uploadedFileName?: string | null;
  onClose: () => void;
}

/**
 * ImagePreviewModal 컴포넌트
 * 이미지를 전체 화면으로 확대하여 보여줌
 */
export function ImagePreviewModal({
  uploadedImage,
  uploadedFileName,
  onClose,
}: ImagePreviewModalProps) {
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-[90vw] max-h-[90vh] bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 닫기 버튼 */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-10 w-8 h-8 flex items-center justify-center bg-black/50 hover:bg-black/70 text-white rounded-full transition-colors"
          title="닫기 (ESC)"
        >
          x
        </button>
        {/* 이미지 */}
        <img
          src={uploadedImage}
          alt="Uploaded preview full"
          className="max-w-[85vw] max-h-[85vh] object-contain"
        />
        {/* 파일 정보 */}
        {uploadedFileName && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
            <div className="text-white text-sm font-medium">{uploadedFileName}</div>
            <div className="text-white/70 text-xs mt-1">
              크기: {Math.round(uploadedImage.length / 1024)} KB (base64) | 클릭하여 닫기
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
