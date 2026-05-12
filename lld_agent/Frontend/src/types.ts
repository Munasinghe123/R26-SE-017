/* ============================================================
   TypeScript types mirroring the backend Pydantic models
   ============================================================ */

// --- Input types ---

export interface ArchitecturalLayer {
  name: string;
  description: string;
  components: string[];
}

export interface HighLevelArchitecture {
  pattern: string;
  layers: ArchitecturalLayer[];
  architectural_constraints: string[];
}

export interface FunctionalRequirement {
  id: string;
  title: string;
  description: string;
}

export interface GenerateRequest {
  project_name: string;
  project_description: string;
  high_level_architecture: HighLevelArchitecture;
  functional_requirements: FunctionalRequirement[];
  export_formats: string[];
}

// --- Output types ---

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export interface ValidationError {
  rule_id: string;
  severity: Severity;
  message: string;
  suggestion: string;
  educational_feedback: string;
}

export interface NamingViolation {
  location: string;
  current_name: string;
  expected_name: string;
  convention: string;
  auto_fixed: boolean;
}

export interface TraceabilityEntry {
  requirement_id: string;
  mapped_classes: string[];
  mapped_sequences: string[];
  mapped_entities: string[];
  is_covered: boolean;
}

export interface OverDesignFlag {
  element_type: string;
  element_name: string;
  reason: string;
  educational_feedback: string;
}

export interface ValidationReport {
  passed: boolean;
  consistency_score: number;
  total_checks: number;
  passed_checks: number;
  errors: ValidationError[];
  naming_violations: NamingViolation[];
  naming_violations_fixed: number;
  traceability_matrix: TraceabilityEntry[];
  overdesign_flags: OverDesignFlag[];
  iteration: number;
}

export interface DiagramOutput {
  diagram_type: string;
  plantuml_syntax: string;
  mermaid_syntax: string;
  name: string;
  png_base64: string;
  svg_content: string;
}

export interface GenerateResponse {
  success: boolean;
  project_name: string;
  ir: Record<string, unknown>;
  diagrams: DiagramOutput[];
  validation_report: ValidationReport;
  educational_summary: string;
  iterations_used: number;
  exported_files: string[];
}

export interface HealthResponse {
  status: string;
  llm_provider: string;
  rag_enabled: boolean;
  kroki_url: string;
  version: string;
}
