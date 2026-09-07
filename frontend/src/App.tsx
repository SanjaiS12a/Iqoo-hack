import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, session } from "./api";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/ui";
import { LoginPage } from "./pages/LoginPage";
import { StudentApp } from "./pages/StudentApp";
import { TeacherApp } from "./pages/TeacherApp";
import type { User } from "./types";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(Boolean(session.token()));
  const [view, setView] = useState("home");
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, retry: false });

  useEffect(() => {
    if (!session.token()) return;
    api.me().then(value => { setUser(value); setView(value.role === "teacher" ? "dashboard" : "home"); }).catch(() => session.clear()).finally(() => setChecking(false));
  }, []);

  const loggedIn = (value: User) => { setUser(value); setView(value.role === "teacher" ? "dashboard" : "home"); };
  const logout = () => { session.clear(); setUser(null); setView("home"); };

  if (checking) return <div className="splash"><Spinner /><span>Opening ClassMind…</span></div>;
  if (!user) return <LoginPage onLogin={loggedIn} />;
  return <Layout user={user} view={view} onView={setView} onLogout={logout} aiMode={health.data?.ai_provider ?? "demo"}>{user.role === "student" ? <StudentApp view={view} onNavigate={setView} /> : <TeacherApp view={view} />}</Layout>;
}

