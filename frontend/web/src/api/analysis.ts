import client from './client';

export interface AnalysisResponse {
    success: boolean;
    message: string;
    result?: {
        date: string;
        [key: string]: any;
    };
    cached: boolean;
}

export const runKlineAnalysis = async (symbol: string, forceRerun: boolean = false): Promise<AnalysisResponse> => {
    const response = await client.post<AnalysisResponse>('/analysis/kline', { symbol, force_rerun: forceRerun });
    return response as any;
};

export const runLimitUpAnalysis = async (date?: string, forceRerun: boolean = false): Promise<AnalysisResponse> => {
    const response = await client.post<AnalysisResponse>('/analysis/limit-up', { date, force_rerun: forceRerun });
    return response as any;
};

export const runOpeningAnalysis = async (date?: string, forceRerun: boolean = false): Promise<AnalysisResponse> => {
    const response = await client.post<AnalysisResponse>('/analysis/opening-analysis', { date, force_rerun: forceRerun });
    return response as any;
};

export const getAnalysisReport = async (reportType: string, date: string, symbol?: string): Promise<AnalysisResponse> => {
    const params: any = { report_type: reportType, date };
    if (symbol) params.symbol = symbol;
    const response = await client.get<AnalysisResponse>(`/analysis/report`, { params });
    return response as any;
};
