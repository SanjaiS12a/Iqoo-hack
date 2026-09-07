export type Role = "student" | "teacher" | "admin";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  class_id: number | null;
  class_name: string | null;
  grade: number | null;
  section: string | null;
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
  active_portion?: Portion | null;
  recent: Array<{ id: number; topic: string; is_correct: boolean; misconception_label: string | null; created_at: string }>;
}

export interface Dashboard {
  classroom: Classroom;
  summary: { active_students: number; total_students: number; accuracy: number; questions_answered: number };
  misconceptions: Array<{ tag: string; label: string; affected_students: number; events: number; class_percentage: number }>;
  topics: Array<{ topic: string; accuracy: number; attempts: number }>;
  recent_activity: Array<{ id: number; student_name: string; topic: string; is_correct: boolean; misconception_label: string | null; created_at: string }>;
  demo_data: boolean;
}

export interface Classroom {
  id: number;
  name: string;
  subject: string;
  grade: number;
  section: string;
  join_code: string;
  student_count: number;
}

export interface PortionTopic {
  id?: number;
  title: string;
  learning_outcome: string;
  sequence: number;
}

export interface PortionQuestion {
  id?: number;
  text: string;
  expected_answer: string;
  difficulty: string;
  topic: string;
  exam_weight: number;
}

export interface Portion {
  id: number;
  class_id: number;
  title: string;
  subject: string;
  original_filename: string;
  status: "processing" | "draft" | "published" | "archived" | "failed";
  provider: string;
  created_at: string;
  published_at: string | null;
  topics: PortionTopic[];
  questions: PortionQuestion[];
}

export interface GradeSummary {
  grade: number;
  classes: Classroom[];
}
