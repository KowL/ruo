import client from './client';
import type {
  Concept,
  ConceptDetail,
  ConceptListItem,
  ConceptStock,
  CreateConceptRequest,
  UpdateConceptRequest,
  AddStockToConceptRequest,
  UpdateStockPositioningRequest,
  ConceptLibraryResponse,
  ConceptRankingResponse,
  ConceptMarketDetailResponse,
  ConceptDistributionResponse,
  ConceptMarketData,
} from '../types/concept';

// 通用响应类型
interface ApiResponse<T> {
  status: string;
  data: T;
  message?: string;
}

// ==================== 概念管理 API ====================

// 获取概念列表
export const getConceptList = async (skip = 0, limit = 100): Promise<ConceptListItem[]> => {
  const response = await client.get<ApiResponse<ConceptListItem[]>>(`/concept/list?skip=${skip}&limit=${limit}`);
  return response.data.data;
};

// 获取概念详情
export const getConcept = async (id: number): Promise<ConceptDetail> => {
  const response = await client.get<ApiResponse<ConceptDetail>>(`/concept/${id}`);
  return response.data.data;
};

// 创建概念
export const createConcept = async (data: CreateConceptRequest): Promise<Concept> => {
  const response = await client.post<ApiResponse<Concept>>('/concept/', data);
  return response.data.data;
};

// 更新概念
export const updateConcept = async (id: number, data: UpdateConceptRequest): Promise<Concept> => {
  const response = await client.put<ApiResponse<Concept>>(`/concept/${id}`, data);
  return response.data.data;
};

// 删除概念
export const deleteConcept = async (id: number): Promise<void> => {
  await client.delete<ApiResponse<void>>(`/concept/${id}`);
};

// 添加股票到概念
export const addStockToConcept = async (
  conceptId: number,
  data: AddStockToConceptRequest
): Promise<ConceptStock> => {
  const response = await client.post<ApiResponse<ConceptStock>>(`/concept/${conceptId}/stocks`, data);
  return response.data.data;
};

// 更新股票定位
export const updateStockPositioning = async (
  conceptId: number,
  stockSymbol: string,
  data: UpdateStockPositioningRequest
): Promise<ConceptStock> => {
  const response = await client.put<ApiResponse<ConceptStock>>(
    `/concept/${conceptId}/stocks/${stockSymbol}`,
    data
  );
  return response.data.data;
};

// 从概念中移除股票
export const removeStockFromConcept = async (conceptId: number, stockSymbol: string): Promise<void> => {
  await client.delete<ApiResponse<void>>(`/concept/${conceptId}/stocks/${stockSymbol}`);
};

// ==================== 概念库 (行情) API ====================

/**
 * 获取概念库列表
 */
export const getConceptLibrary = async (
  minHotScore: number = 0,
  limit: number = 50
): Promise<ConceptLibraryResponse> => {
  return client.get(
    `/concept?min_hot_score=${minHotScore}&limit=${limit}`
  );
};

/**
 * 获取概念强度排行榜
 */
export const getConceptRanking = async (
  sortBy: string = 'hot_score',
  limit: number = 20
): Promise<ConceptRankingResponse> => {
  return client.get(
    `/concept/ranking?sort_by=${sortBy}&limit=${limit}`
  );
};

/**
 * 获取涨停概念分布统计
 */
export const getConceptDistribution = async (): Promise<ConceptDistributionResponse> => {
  return client.get('/concept/distribution');
};

/**
 * 获取概念详情 (市场数据)
 */
export const getConceptMarketDetail = async (themeName: string): Promise<ConceptMarketDetailResponse> => {
  const encodedName = encodeURIComponent(themeName);
  const response = await client.get<ApiResponse<ConceptMarketData>>(
    `/concept/${encodedName}`
  );
  return response.data;
};
