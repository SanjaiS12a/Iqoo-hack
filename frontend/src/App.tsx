import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, session } from "./api";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/ui";
import { LoginPage } from "./pages/LoginPage";
import { AdminApp } from "./pages/AdminApp";
import { PortionsPage } from "./pages/PortionsPage";
import { StudentApp } from "./pages/StudentApp";
import { TeacherApp } from "./pages/TeacherApp";
import type { User } from "./types";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(Boolean(session.token()));
  const [view, setView] = useState("home");
  const [activeClassId, setActiveClassId] = useState<number | null>(null);
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, retry: false });
  const classes = useQuery({ queryKey: ["teacher-classes", user?.id], queryFn: api.teacherClasses, enabled: user?.role === "teacher" });

  useEffect(() => {
    if (!session.token()) return;
    api.me().then(value => { setUser(value); setView(value.role === "teacher" ? "dashboard" : value.role === "admin" ? "school" : "home"); }).catch(() => session.clear()).finally(() => setChecking(false));
  }, []);

  useEffect(() => {
    if (classes.data?.length && !classes.data.some(item => item.id === activeClassId)) setActiveClassId(classes.data[0].id);
  }, [classes.data, activeClassId]);

  const loggedIn = (value: User) => { setUser(value); setView(value.role === "teacher" ? "dashboard" : value.role === "admin" ? "school" : "home"); };
  const logout = () => { session.clear(); setUser(null); setView("home"); };

  if (checking) return <div className="splash"><Spinner /><span>Opening ClassMind…</span></div>;
  if (!user) return <LoginPage onLogin={loggedIn} />;
  const teacherContent = activeClassId ? (view === "portions" ? <PortionsPage classId={activeClassId} /> : <TeacherApp view={view} classId={activeClassId} />) : <div className="center-loader"><Spinner /></div>;
  return <Layout user={user} view={view} onView={setView} onLogout={logout} aiMode={health.data?.ai_provider ?? "demo"} classes={classes.data} activeClassId={activeClassId} onClassChange={setActiveClassId}>{user.role === "student" ? <StudentApp view={view} onNavigate={setView} /> : user.role === "admin" ? <AdminApp view={view} /> : teacherContent}</Layout>;
}
