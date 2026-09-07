import type { Classroom, Dashboard, Diagnosis, Doubt, GradeSummary, Portion, Question, StudentOverview, StudyPlan, User } from "./types";

const TOKEN_KEY = "classmind_token";
const API_BASE = import.meta.env.VITE_API_URL ?? "";

export const session = {
  token: () => localStorage.getItem(TOKEN_KEY),
  save: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = session.token();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Something went wrong" }));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "Request failed");
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request<User>("/api/auth/me"),
  health: () => request<{ status: string; ai_provider: string; model: string }>("/api/health"),
  overview: () => request<StudentOverview>("/api/student/overview"),
  questions: () => request<Question[]>("/api/student/questions"),
  submit: (question_id: number, answer_text: string) =>
    request<Diagnosis>("/api/student/submissions", { method: "POST", body: JSON.stringify({ question_id, answer_text }) }),
  doubts: () => request<Doubt[]>("/api/student/doubts"),
  askDoubt: (doubt_text: string) => request<Doubt>("/api/student/doubts", { method: "POST", body: JSON.stringify({ doubt_text }) }),
  plan: () => request<StudyPlan>("/api/student/study-plan"),
  generatePlan: () => request<StudyPlan>("/api/student/study-plan/generate", { method: "POST" }),
  updatePlan: (id: number, completed: boolean) =>
    request<{ id: number; completed: boolean }>(`/api/student/study-plan/items/${id}`, { method: "PATCH", body: JSON.stringify({ completed }) }),
  teacherClasses: () => request<Classroom[]>("/api/teacher/classes"),
  dashboard: (classId: number) => request<Dashboard>(`/api/teacher/classes/${classId}/dashboard`),
  students: (classId: number) => request<Array<{ id: number; name: string; attempts: number; accuracy: number; active_gaps: number }>>(`/api/teacher/classes/${classId}/students`),
  reteach: (classId: number, item: Dashboard["misconceptions"][number]) =>
    request<{ id: number; script: string }>(`/api/teacher/classes/${classId}/reteach`, {
      method: "POST",
      body: JSON.stringify({ misconception_tag: item.tag, misconception_label: item.label, affected_students: item.affected_students }),
    }),
  portions: (classId: number) => request<Portion[]>(`/api/teacher/classes/${classId}/portions`),
  uploadPortion: async (classId: number, file: File) => {
    const body = new FormData(); body.append("file", file);
    const response = await fetch(`${API_BASE}/api/teacher/classes/${classId}/portions`, { method: "POST", headers: { Authorization: `Bearer ${session.token()}` }, body });
    if (!response.ok) { const payload = await response.json(); throw new Error(payload.detail ?? "Upload failed"); }
    return response.json() as Promise<Portion>;
  },
  updatePortion: (classId: number, portion: Portion) => request<Portion>(`/api/teacher/classes/${classId}/portions/${portion.id}`, { method: "PUT", body: JSON.stringify({ title: portion.title, subject: portion.subject, topics: portion.topics, questions: portion.questions }) }),
  publishPortion: (classId: number, portionId: number) => request<Portion>(`/api/teacher/classes/${classId}/portions/${portionId}/publish`, { method: "POST" }),
  grades: () => request<GradeSummary[]>("/api/admin/grades"),
  adminClasses: () => request<Classroom[]>("/api/admin/classes"),
  createClass: (payload: { grade: number; section: string; name: string; subject: string }) =>
    request<Classroom>("/api/admin/classes", { method: "POST", body: JSON.stringify(payload) }),
  adminUsers: () => request<User[]>("/api/admin/users"),
  assignTeacher: (classId: number, teacherId: number) => request(`/api/admin/classes/${classId}/teachers/${teacherId}`, { method: "POST" }),
  placeStudent: (classId: number, studentId: number) => request<User>(`/api/admin/classes/${classId}/students/${studentId}`, { method: "POST" }),
};
