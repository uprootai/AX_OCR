// 공통 타입 정의

/** API 응답의 일반적인 데이터 구조 */
export type JSONValue = string | number | boolean | null | JSONValue[] | { [key: string]: JSONValue };

/** Record 형태의 객체 */
export type JSONObject = Record<string, JSONValue>;

/** API 응답 데이터 타입 */
export interface APIResponseData {
  [key: string]: unknown;
}

/** 파이프라인 결과 타입 */
export interface PipelineResult {
  status: string;
  data: Record<string, unknown>;
  processing_time?: number;
  error?: string;
}

/** Detection 결과 */
export interface Detection {
  class_name: string;
  confidence: number;
  bbox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  class_id?: number;
}

/** OCR Enhancement 결과 */
export interface EnhancementResult {
  strategy: string;
  improved_count?: number;
  details?: Record<string, unknown>;
}

/** 노드 실행 결과 */
export interface NodeExecutionResult {
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  output?: Record<string, unknown>;
  error?: string;
  processing_time?: number;
}

/** 워크플로우 실행 결과 */
export interface WorkflowExecutionResult {
  execution_id: string;
  status: 'running' | 'completed' | 'failed';
  node_results: NodeExecutionResult[];
  final_output?: Record<string, unknown>;
  total_time?: number;
}

/** Form 이벤트 핸들러 타입 */
export type FormEventHandler<T = HTMLInputElement> = React.ChangeEvent<T>;

/** 제네릭 콜백 함수 */
export type Callback<T = void> = () => T;
export type AsyncCallback<T = void> = () => Promise<T>;
