import client from './client';

export interface AnalysisResponse {
    success: boolean;
    message: string;
    result?: {
        date: string;
        report_id?: number;
        [key: string]: any;
    };
    cached: boolean;
}

export interface HistoryItem {
    id: number;
    report_date: string;
    analysis_type: string;
    analysis_name: string;
    symbol: string;
    summary: string;
    status: string;
    recommendation?: string;
    confidence?: number;
    created_at: string;
}

export interface HistoryListResponse {
    success: boolean;
    message: string;
    result?: {
        items: HistoryItem[];
    };
    total: number;
    page: number;
    page_size: number;
}

export const runKlineAnalysis = async (symbol: string, forceRerun: boolean = false): Promise<AnalysisResponse> => {
    const response = await client.post<AnalysisResponse>('/analysis/kline', { symbol, force_rerun: forceRerun });
    return response as any;
};

export interface AnalysisParam {
    date?: string;
    [key: string]: any;
}

export interface UnifiedAnalysisRequest {
    analysisType: 'limit-up' | 'opening-analysis' | 'prompt';
    analysisName?: string;
    prompt?: string;
    analysisParam?: AnalysisParam;
}

// 统一分析接口
export const runAnalysis = async (request: UnifiedAnalysisRequest): Promise<AnalysisResponse> => {
    const response = await client.post<AnalysisResponse>('/analysis/start', request);
    return response as any;
};

export const getAnalysisReport = async (analysisType: string, date: string, symbol?: string): Promise<AnalysisResponse> => {
    const params: any = { analysis_type: analysisType, date };
    if (symbol) params.symbol = symbol;
    const response = await client.get<AnalysisResponse>(`/analysis/report`, { params });
    return response as any;
};

export const getAnalysisHistory = async (
    page: number = 1, 
    pageSize: number = 20, 
    analysisType?: string,
    startDate?: string,
    endDate?: string
): Promise<HistoryListResponse> => {
    const params: any = { page, page_size: pageSize };
    if (analysisType) params.analysis_type = analysisType;
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await client.get<HistoryListResponse>(`/analysis/history`, { params });
    return response as any;
};

export const getHistoryDetail = async (reportId: number): Promise<AnalysisResponse> => {
    const response = await client.get<AnalysisResponse>(`/analysis/history/${reportId}`);
    return response as any;
};

