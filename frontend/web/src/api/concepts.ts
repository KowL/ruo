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
} from '../types/concept';

// 通用响应类型
interface ApiResponse<T> {
  status: string;
  data: T;
  message?: string;
}

// 获取概念列表
export const getConcepts = async (skip = 0, limit = 100): Promise<ConceptListItem[]> => {
  const response = await client.get<ApiResponse<ConceptListItem[]>>(`/concepts/?skip=${skip}&limit=${limit}`);
  return response.data.data;
};

// 获取概念详情
export const getConcept = async (id: number): Promise<ConceptDetail> => {
  const response = await client.get<ApiResponse<ConceptDetail>>(`/concepts/${id}`);
  return response.data.data;
};

// 创建概念
export const createConcept = async (data: CreateConceptRequest): Promise<Concept> => {
  const response = await client.post<ApiResponse<Concept>>('/concepts/', data);
  return response.data.data;
};

// 更新概念
export const updateConcept = async (id: number, data: UpdateConceptRequest): Promise<Concept> => {
  const response = await client.put<ApiResponse<Concept>>(`/concepts/${id}`, data);
  return response.data.data;
};

// 删除概念
export const deleteConcept = async (id: number): Promise<void> => {
  await client.delete<ApiResponse<void>>(`/concepts/${id}`);
};

// 添加股票到概念
export const addStockToConcept = async (
  conceptId: number,
  data: AddStockToConceptRequest
): Promise<ConceptStock> => {
  const response = await client.post<ApiResponse<ConceptStock>>(`/concepts/${conceptId}/stocks`, data);
  return response.data.data;
};

// 更新股票定位
export const updateStockPositioning = async (
  conceptId: number,
  stockSymbol: string,
  data: UpdateStockPositioningRequest
): Promise<ConceptStock> => {
  const response = await client.put<ApiResponse<ConceptStock>>(
    `/concepts/${conceptId}/stocks/${stockSymbol}`,
    data
  );
  return response.data.data;
};

// 从概念中移除股票
export const removeStockFromConcept = async (conceptId: number, stockSymbol: string): Promise<void> => {
  await client.delete<ApiResponse<void>>(`/concepts/${conceptId}/stocks/${stockSymbol}`);
};
