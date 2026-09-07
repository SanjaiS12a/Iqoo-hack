import { ArrowRight, BrainCircuit, Building2, ChartNoAxesCombined, Check, Sparkles } from "lucide-react";
import { useState } from "react";

import { api, session } from "../api";
import type { Role, User } from "../types";
import { Spinner } from "../components/ui";

export function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const [loading, setLoading] = useState<Role | null>(null);
  const [error, setError] = useState("");

  const demoLogin = async (role: Role) => {
    setLoading(role);
    setError("");
    try {
      const email = role === "student" ? "aarav@classmind.demo" : role === "teacher" ? "meera@classmind.demo" : "admin@classmind.demo";
      const result = await api.login(email, "demo1234");
      session.save(result.access_token);
      onLogin(result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not connect to ClassMind");
    } finally {
      setLoading(null);
    }
  };

  return (
    <main className="login-page">
      <section className="login-story">
        <div className="brand login-brand"><span className="brand-mark"><BrainCircuit /></span><span>ClassMind</span></div>
        <div className="story-copy">
          <span className="kicker"><Sparkles size={16} /> AI teaching co-pilot</span>
          <h1>Know who learned.<br /><em>Know what to do next.</em></h1>
          <p>Turn every answer and doubt into a clear classroom signal, then guide each learner with the right next step.</p>
          <div className="story-points">
            <span><Check /> Pinpoint misconceptions, not just wrong answers</span>
            <span><Check /> See the whole class pulse as it changes</span>
            <span><Check /> Build exam-aware revision plans automatically</span>
          </div>
        </div>
        <div className="insight-preview">
          <div className="preview-icon"><ChartNoAxesCombined /></div>
          <div><span>Live class signal</span><strong>14 learners need help with transposition</strong></div>
          <div className="mini-bars"><i /><i /><i /></div>
        </div>
      </section>
      <section className="login-panel">
        <div className="login-box">
          <span className="eyebrow">Ready-to-run demo</span>
          <h2>Every learner understood.</h2>
          <p>Choose a workspace to explore the complete closed learning loop. Demo data is synthetic.</p>
          <div className="role-options">
            <button className="role-option student-option" onClick={() => demoLogin("student")} disabled={loading !== null}>
              <div className="role-icon"><BrainCircuit /></div>
              <div><strong>Enter as student</strong><span>Practice, ask doubts and follow a personal plan</span></div>
              {loading === "student" ? <Spinner /> : <ArrowRight />}
            </button>
            <button className="role-option teacher-option" onClick={() => demoLogin("teacher")} disabled={loading !== null}>
              <div className="role-icon"><ChartNoAxesCombined /></div>
              <div><strong>Enter as teacher</strong><span>See live gaps and generate a re-teach</span></div>
              {loading === "teacher" ? <Spinner /> : <ArrowRight />}
            </button>
            <button className="role-option admin-option" onClick={() => demoLogin("admin")} disabled={loading !== null}>
              <div className="role-icon"><Building2 /></div>
              <div><strong>Enter as administrator</strong><span>Manage Grades 1–12, sections and assignments</span></div>
              {loading === "admin" ? <Spinner /> : <ArrowRight />}
            </button>
          </div>
          {error && <div className="error-notice">{error}. Make sure the backend is running on port 8000.</div>}
          <div className="demo-credentials"><span>Demo password</span><code>demo1234</code></div>
        </div>
      </section>
    </main>
  );
}
