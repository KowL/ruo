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

export const runLimitUpAnalysis = async (date?: string, forceRerun: boolean = false): Promise<AnalysisResponse> => {
    const response = await client.post<AnalysisResponse>('/analysis/limit-up', { date, force_rerun: forceRerun });
    return response as any;
};

export const runOpeningAnalysis = async (date?: string, forceRerun: boolean = false): Promise<AnalysisResponse> => {
    const response = await client.post<AnalysisResponse>('/analysis/opening-analysis', { date, force_rerun: forceRerun });
    return response as any;
};

export const getAnalysisReport = async (reportType: string, date: string): Promise<AnalysisResponse> => {
    const response = await client.get<AnalysisResponse>(`/analysis/report`, {
        params: { report_type: reportType, date }
    });
    return response as any;
};
