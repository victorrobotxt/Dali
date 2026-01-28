// glashaus-web/src/types/api.ts

export type ReportStatus = 'PENDING' | 'PROCESSING' | 'VERIFIED' | 'MANUAL_REVIEW' | 'REJECTED';

export interface AuditRequest {
  url: string;
  price_override?: number;
}

export interface AuditResponse {
  listing_id: number;
  status: string;
}

export interface AIAnalysisResult {
  address_prediction: string;
  landmarks: string[];
  neighborhood_match: string;
  building_type: string;
  is_panel_block: boolean;
  construction_year_est: number;
  room_count: number;
  ceiling_height: number;
  has_storage: boolean; // <--- FIXED: Added this
  light_exposure?: string; // <--- Added for completeness
  act16_due_date?: string; // <--- Added for completeness
  heating_inventory: {
    ac_units: number;
    radiators: number;
    has_central_heating: boolean;
  };
  net_area_sqm: number;
  visual_red_flags: string[];
}

export interface ForensicReport {
  report_id: number;
  status: ReportStatus;
  risk_score: number;
  ai_confidence: number;
  discrepancies: {
    scraped: {
      source_url: string;
      price_predicted: number;
      area_sqm: number;
      neighborhood: string;
      image_urls: string[];
    };
    ai: AIAnalysisResult;
    geo: {
      match: boolean;
      detected_neighborhood: string;
      warning?: string;
    };
    cadastre: {
      cadastre_id: string;
      official_area: number;
      social_risk_ratio: number;
    };
    legal_status: {
      status: string;
      is_trap: boolean;
      legal_flags: string[];
    };
    city_risk?: {
        is_expropriated: boolean;
    };
    compliance?: {
        has_act16: boolean;
    };
  };
  manual_notes?: string;
  cost: number;
  created_at: string;
}
