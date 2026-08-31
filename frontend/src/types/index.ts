export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface DashboardSummary {
  total_customers: number;
  customers_requiring_review: number;
  high_risk_customers: number;
  medium_risk_customers: number;
  low_risk_customers: number;
  total_transactions: number;
  high_risk_percentage: number;
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
  };
  investigation_statistics: {
    avg_risk_probability: number;
    review_queue_size: number;
    threshold_frozen: number;
  };
}

export interface RiskQueueItem {
  customer_id: string;
  risk_probability: number;
  risk_level: RiskLevel;
  review_required: boolean;
  primary_signals: string[];
}

export interface RiskQueueResponse {
  items: RiskQueueItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface DemoCustomer {
  customer_id: string;
  category: string;
  description: string;
  risk_probability: number;
  risk_level: RiskLevel;
  review_required: boolean;
}

export interface SignalStrength {
  detected: boolean;
  strength: 'LOW' | 'MEDIUM' | 'HIGH';
  details?: Record<string, any>;
}

export interface SharedDevice {
  device_id: string;
  customer_count: number;
  transaction_count: number;
  other_customers: string[];
}

export interface SharedIP {
  ip_address: string;
  customer_count: number;
  transaction_count: number;
  other_customers: string[];
}

export interface CouponCoordination {
  coupon_id: string;
  customer_count: number;
  shared_device_count: number;
  shared_ip_count: number;
}

export interface ReferralConnections {
  referrer_id: string | null;
  referred_accounts: string[];
  referral_in_degree: number;
  referral_out_degree: number;
  referral_component_size: number;
}

export interface TemporalCluster {
  time_window_seconds: number;
  customer_count: number;
  transaction_count: number;
  total_amount: number;
  transactions: Array<{
    connected_customer: string;
    target_tx_id: string;
    target_tx_time: string;
    target_tx_amount: number;
    other_tx_id: string;
    other_tx_time: string;
    other_tx_amount: number;
    time_diff: number;
  }>;
}

export interface MultiSignalConnection {
  connected_customer: string;
  signal_count: number;
  signals: string[];
}

export interface CustomerInvestigation {
  customer: {
    customer_id: string;
    account_age_days: number;
    account_created_at: string;
  };
  risk: {
    risk_probability: number;
    review_required: boolean;
    risk_level: RiskLevel;
  };
  behavior: {
    transaction_count: number;
    total_transaction_amount: number;
    average_transaction_amount: number;
    median_transaction_amount: number;
    coupon_usage_count: number;
    unique_coupons_used: number;
    referrals_made: number;
    was_referred: boolean;
    active_days: number;
    night_transaction_ratio: number;
  };
  signals: {
    shared_devices: SharedDevice[];
    shared_ips: SharedIP[];
    coupon_coordination: CouponCoordination[];
    referral_connections: ReferralConnections;
    temporal_clusters: TemporalCluster[];
  };
  strengths: {
    shared_device: SignalStrength;
    shared_ip: SignalStrength;
    coupon_coordination: SignalStrength;
    referral_coordination: SignalStrength;
    temporal_coordination: SignalStrength;
  };
  multi_signal_connections: MultiSignalConnection[];
  summary: {
    signal_count: number;
    connected_customer_count: number;
    investigation_timestamp: string;
  };
}

export interface GraphNode {
  id: string;
  type: string;
  data: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  label?: string;
  data?: Record<string, any>;
}

export interface GraphResponse {
  customer_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_connections_count: number;
  displayed_nodes_count: number;
  prioritization_note: string;
}

export interface RiskExplanation {
  headline: string;
  summary: string;
  key_signals: string[];
  observed_evidence: string[];
  recommended_action: string;
  uncertainty: string;
}
