export type Role = "student" | "teacher";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  class_id: number;
  class_name: string;
  avatar_color: string;
}

export interface Question {
  id: number;
  slug: string;
  subject: string;
  topic: string;
  concept_tag: string;
  text: string;
  hint: string;
  difficulty: string;
  exam_frequency_score: number;
}

export interface Diagnosis {
  id: number;
  is_correct: boolean;
  misconception_tag: string | null;
  misconception_label: string | null;
  micro_explanation: string;
  confidence: number;
  created_at: string;
}

export interface Doubt {
  id: number;
  doubt_text: string;
  concept_tag: string;
  ai_response: string;
  created_at: string;
}

export interface PlanItem {
  id: number;
  topic: string;
  reason: string;
  priority_score: number;
  estimated_minutes: number;
  completed: boolean;
}

export interface StudyPlan {
  id: number | null;
  generated_at: string | null;
  items: PlanItem[];
}

export interface StudentOverview {
  accuracy: number;
  questions_attempted: number;
  streak: number;
  active_gaps: number;
  recent: Array<{ id: number; topic: string; is_correct: boolean; misconception_label: string | null; created_at: string }>;
}

export interface Dashboard {
  classroom: { id: number; name: string; student_count: number };
  summary: { active_students: number; total_students: number; accuracy: number; questions_answered: number };
  misconceptions: Array<{ tag: string; label: string; affected_students: number; events: number; class_percentage: number }>;
  topics: Array<{ topic: string; accuracy: number; attempts: number }>;
  recent_activity: Array<{ id: number; student_name: string; topic: string; is_correct: boolean; misconception_label: string | null; created_at: string }>;
  demo_data: boolean;
}

