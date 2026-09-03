import {
  DashboardSummary,
  RiskQueueResponse,
  CustomerInvestigation,
  GraphResponse,
  RiskExplanation,
  DemoCustomer
} from '../types';

const API_BASE = '/api';

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const res = await fetch(`${API_BASE}/dashboard/summary`);
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export interface RiskQueueParams {
  limit?: number;
  offset?: number;
  risk_level?: string;
  review_required?: boolean;
  min_probability?: number;
  max_probability?: number;
  search?: string;
  sort?: 'asc' | 'desc';
}

export async function fetchRiskQueue(params: RiskQueueParams = {}): Promise<RiskQueueResponse> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set('limit', params.limit.toString());
  if (params.offset !== undefined) query.set('offset', params.offset.toString());
  if (params.risk_level) query.set('risk_level', params.risk_level);
  if (params.review_required !== undefined) query.set('review_required', params.review_required.toString());
  if (params.min_probability !== undefined) query.set('min_probability', params.min_probability.toString());
  if (params.max_probability !== undefined) query.set('max_probability', params.max_probability.toString());
  if (params.search) query.set('search', params.search);
  if (params.sort) query.set('sort', params.sort);

  const res = await fetch(`${API_BASE}/risk/customers?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch risk queue');
  return res.json();
}

export async function fetchCustomerInvestigation(customerId: string): Promise<CustomerInvestigation> {
  const res = await fetch(`${API_BASE}/risk/customers/${customerId}/investigation`);
  if (!res.ok) throw new Error(`Failed to fetch investigation for customer ${customerId}`);
  return res.json();
}

export async function fetchCustomerGraph(customerId: string): Promise<GraphResponse> {
  const res = await fetch(`${API_BASE}/risk/customers/${customerId}/graph`);
  if (!res.ok) throw new Error(`Failed to fetch graph for customer ${customerId}`);
  return res.json();
}

export async function fetchCustomerExplanation(customerId: string): Promise<RiskExplanation> {
  const res = await fetch(`${API_BASE}/risk/customers/${customerId}/explanation`);
  if (!res.ok) throw new Error(`Failed to fetch AI explanation for customer ${customerId}`);
  return res.json();
}

export async function fetchDemoCustomers(): Promise<DemoCustomer[]> {
  const res = await fetch(`${API_BASE}/demo/customers`);
  if (!res.ok) throw new Error('Failed to fetch demo customers');
  return res.json();
}

export async function fetchSampleDatasets(): Promise<import('../types').SampleDatasetItem[]> {
  const res = await fetch(`${API_BASE}/analysis/sample-datasets`);
  if (!res.ok) throw new Error('Failed to fetch sample datasets');
  return res.json();
}

export async function uploadMerchantDataset(
  file: File
): Promise<import('../types').DatasetValidationResult> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/analysis/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to upload dataset');
  }
  return res.json();
}

export async function validateMerchantPayload(
  records: any[],
  filename: string = 'payload.json'
): Promise<import('../types').DatasetValidationResult> {
  const res = await fetch(`${API_BASE}/analysis/validate-payload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, records }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to validate payload');
  }
  return res.json();
}
