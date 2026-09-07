import { BookOpenCheck, BrainCircuit, ChartNoAxesCombined, CircleHelp, ClipboardCheck, GraduationCap, LayoutDashboard, LogOut, Menu, Sparkles, Users, X } from "lucide-react";
import { useState, type ReactNode } from "react";

import type { Role, User } from "../types";

export type StudentView = "home" | "practice" | "doubts" | "plan";
export type TeacherView = "dashboard" | "students";

interface Props {
  user: User;
  view: string;
  onView: (view: string) => void;
  onLogout: () => void;
  children: ReactNode;
  aiMode: string;
}

const studentItems = [
  ["home", "Overview", LayoutDashboard],
  ["practice", "Practice", BookOpenCheck],
  ["doubts", "Ask ClassMind", CircleHelp],
  ["plan", "My study plan", ClipboardCheck],
] as const;

const teacherItems = [
  ["dashboard", "Class pulse", ChartNoAxesCombined],
  ["students", "Learners", Users],
] as const;

export function Layout({ user, view, onView, onLogout, children, aiMode }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const items = user.role === "student" ? studentItems : teacherItems;
  const switchView = (next: string) => {
    onView(next);
    setMenuOpen(false);
  };
  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <button className="mobile-close" onClick={() => setMenuOpen(false)} aria-label="Close menu"><X /></button>
        <div className="brand"><span className="brand-mark"><BrainCircuit /></span><span>ClassMind</span></div>
        <div className="role-card">
          <div className="avatar" style={{ background: user.avatar_color }}>{user.name.split(" ").map((x) => x[0]).slice(0, 2).join("")}</div>
          <div><strong>{user.name}</strong><span>{user.role === "teacher" ? "Teacher workspace" : "Student workspace"}</span></div>
        </div>
        <nav aria-label="Main navigation">
          <p className="nav-label">Workspace</p>
          {items.map(([id, label, Icon]) => (
            <button key={id} className={view === id ? "nav-active" : ""} onClick={() => switchView(id)}><Icon size={19} /><span>{label}</span></button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="ai-status"><Sparkles size={16} /><div><strong>{aiMode === "demo" ? "Demo AI active" : "OpenAI connected"}</strong><span>{aiMode === "demo" ? "Safe sample responses" : "Live analysis enabled"}</span></div></div>
          <button className="logout" onClick={onLogout}><LogOut size={18} /> Sign out</button>
        </div>
      </aside>
      {menuOpen && <button className="scrim" onClick={() => setMenuOpen(false)} aria-label="Close navigation" />}
      <main className="main-panel">
        <header className="topbar">
          <button className="menu-button" onClick={() => setMenuOpen(true)} aria-label="Open menu"><Menu /></button>
          <div><span className="eyebrow">{user.class_name}</span><strong>{user.role === "teacher" ? "Teaching workspace" : "Learning workspace"}</strong></div>
          <div className="topbar-pill"><GraduationCap size={17} /> Class 9 · Mathematics</div>
        </header>
        <div className="page">{children}</div>
      </main>
    </div>
  );
}

