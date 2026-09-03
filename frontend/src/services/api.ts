import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Container {
  id: string;
  container_type: string;
  material: string;
  weight_kg: number;
  age_months: number;
  usage_count: number;
  recyclable: boolean;
  status: string;
  created_at: string;
}

export interface Inspection {
  id?: number;
  container_id: string;
  inspector_id?: number;
  damage_level: string;
  structural_condition: string;
  cleanliness_score: number;
  contamination: string;
  safety_risk: string;
  sensor_available: boolean;
  network_available: boolean;
  location_available: boolean;
  location: string;
  inspection_completeness: number;
  raw_data_json?: string;
  inspection_date?: string;
  created_at?: string;
}

export interface Recommendation {
  id: number;
  container_id: string;
  inspection_id: number;
  recommended_action: string;
  confidence: number;
  score: number;
  financial_score: number;
  environmental_score: number;
  reusability_score: number;
  operational_score: number;
  rules_triggered_json: string;
  explanation: string;
  status: string;
  reviewer_id?: number;
  override_reason?: string;
  review_date?: string;
  created_at: string;
  
  // Custom frontend fields mapped from backend
  evidence?: {
    financial_breakdown: Record<string, { expected_recovery: number; processing_cost: number; net_value: number }>;
    environmental_breakdown: Record<string, { waste_avoided_kg: number; carbon_avoided_kg: number; processing_emission: number; disposal_emission: number }>;
    score_breakdown: Record<string, { financial_score: number; environmental_score: number; reusability_score: number; operational_score: number; final_score: number; prohibited: boolean }>;
    ml_prediction: { action: string; confidence: number };
  };
  financial_reason?: string;
  environmental_reason?: string;
  safety_reason?: string;
  requires_human_confirmation?: boolean;
  alternative_actions?: Array<{ action: string; score: number; net_value: number }>;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  action: string;
  entity_type: string;
  entity_id: string;
  old_value_json?: string;
  new_value_json?: string;
  ip_address?: string;
  timestamp: string;
}

export interface RuleInfo {
  rule_name: string;
  is_triggered: boolean;
  severity: string;
  explanation: string;
  prohibited_actions: string[];
}

export interface AnalyticsData {
  total_processed: number;
  total_financial_recovery: number;
  total_waste_avoided_kg: number;
  total_carbon_saved_kg: number;
  actions_distribution: Record<string, number>;
  override_rate: number;
}

export const apiService = {
  // Health
  checkHealth: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Containers
  getContainers: async (): Promise<Container[]> => {
    const response = await apiClient.get('/api/containers');
    return response.data;
  },

  getContainer: async (id: string): Promise<Container> => {
    const response = await apiClient.get(`/api/containers/${id}`);
    return response.data;
  },

  createContainer: async (container: Omit<Container, 'status' | 'created_at'>): Promise<Container> => {
    const response = await apiClient.post('/api/containers', container);
    return response.data;
  },

  // Inspections
  createInspection: async (inspection: Inspection): Promise<Inspection> => {
    const response = await apiClient.post('/api/inspections', inspection);
    return response.data;
  },

  getInspection: async (id: number): Promise<Inspection> => {
    const response = await apiClient.get(`/api/inspections/${id}`);
    return response.data;
  },

  // Recommendations
  createRecommendation: async (container_id: string, inspection_id: number): Promise<Recommendation> => {
    const response = await apiClient.post('/api/recommendations', { container_id, inspection_id });
    return response.data;
  },

  getRecommendation: async (id: number): Promise<Recommendation> => {
    const response = await apiClient.get(`/api/recommendations/${id}`);
    return response.data;
  },

  approveRecommendation: async (id: number, reviewerId?: number): Promise<Recommendation> => {
    const response = await apiClient.post(`/api/recommendations/${id}/approve`, { reviewer_id: reviewerId });
    return response.data;
  },

  overrideRecommendation: async (id: number, overrideAction: string, overrideReason: string, reviewerId?: number): Promise<Recommendation> => {
    const response = await apiClient.post(`/api/recommendations/${id}/override`, {
      override_action: overrideAction,
      override_reason: overrideReason,
      reviewer_id: reviewerId,
    });
    return response.data;
  },

  // Rules
  getRules: async (): Promise<RuleInfo[]> => {
    const response = await apiClient.get('/api/rules');
    return response.data;
  },

  // Audit Logs
  getAuditLogs: async (): Promise<AuditLog[]> => {
    const response = await apiClient.get('/api/audit-logs');
    return response.data;
  },

  // Analytics
  getAnalytics: async (): Promise<AnalyticsData> => {
    const response = await apiClient.get('/api/analytics');
    return response.data;
  },

  // Sync Queue
  triggerSync: async () => {
    const response = await apiClient.post('/api/sync');
    return response.data;
  },
};
