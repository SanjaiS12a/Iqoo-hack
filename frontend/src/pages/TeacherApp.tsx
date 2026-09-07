import { useMutation, useQuery } from "@tanstack/react-query";
import { Activity, ArrowUpRight, BookOpenCheck, CheckCircle2, Clock3, RefreshCw, Sparkles, Target, Users, WandSparkles, X, XCircle } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "../api";
import { Badge, Card, ErrorNotice, Spinner } from "../components/ui";
import type { Dashboard } from "../types";

function DashboardView() {
  const [selected, setSelected] = useState<Dashboard["misconceptions"][number] | null>(null);
  const [script, setScript] = useState("");
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard, refetchInterval: 5000 });
  const reteach = useMutation({ mutationFn: (item: Dashboard["misconceptions"][number]) => api.reteach(item), onSuccess: value => setScript(value.script) });
  if (dashboard.isLoading) return <div className="center-loader"><Spinner /></div>;
  if (dashboard.error || !dashboard.data) return <ErrorNotice message={(dashboard.error as Error)?.message ?? "Could not load the class pulse"} />;
  const data = dashboard.data;
  const metrics = [
    ["Learners active", `${data.summary.active_students}/${data.summary.total_students}`, Users, "teal"],
    ["Class accuracy", `${data.summary.accuracy}%`, Target, "blue"],
    ["Answers analysed", data.summary.questions_answered, BookOpenCheck, "amber"],
    ["Priority signals", data.misconceptions.length, Activity, "red"],
  ] as const;
  const handleReteach = (item: Dashboard["misconceptions"][number]) => { setSelected(item); setScript(""); reteach.mutate(item); };
  return <>
    <div className="page-heading"><div><div className="live-label"><i /> Live class pulse · refreshes every 5 seconds</div><h1>Where does 9A need you?</h1><p>Class-level signals from answers and doubts, ranked for action.</p></div><button className="secondary-button" onClick={() => dashboard.refetch()}><RefreshCw size={17} /> Refresh now</button></div>
    {data.demo_data && <div className="demo-banner"><Sparkles size={18} /><div><strong>Presentation-ready demo data</strong><span>Class activity is synthetic and clearly separated from future live classroom records.</span></div></div>}
    <div className="metric-grid">{metrics.map(([label, value, Icon, tone]) => <Card key={label} className="metric-card"><div className={`metric-icon ${tone}`}><Icon /></div><div><span>{label}</span><strong>{value}</strong></div></Card>)}</div>
    <div className="two-column wide-left">
      <Card><div className="card-heading"><div><span className="eyebrow">Action queue</span><h2>Top misconceptions</h2></div><Badge tone="red">Needs attention</Badge></div><div className="misconception-list">{data.misconceptions.map((item, index) => <div className="misconception-row" key={item.tag}><div className="rank">{String(index + 1).padStart(2, "0")}</div><div className="signal-main"><div><strong>{item.label}</strong><span>{item.affected_students} learners · {item.class_percentage}% of class</span></div><div className="signal-bar"><i style={{ width: `${item.class_percentage}%` }} /></div></div><button className="icon-action" onClick={() => handleReteach(item)} aria-label={`Generate re-teach for ${item.label}`}><WandSparkles /></button></div>)}</div></Card>
      <Card><div className="card-heading"><div><span className="eyebrow">Topic health</span><h2>Accuracy by concept</h2></div></div><div className="chart-wrap"><ResponsiveContainer width="100%" height={260}><BarChart data={data.topics} layout="vertical" margin={{ left: 8, right: 10 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e8e5dc" /><XAxis type="number" domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} /><YAxis type="category" dataKey="topic" width={108} tick={{ fontSize: 11 }} /><Tooltip formatter={(value) => [`${value}%`, "Accuracy"]} /><Bar dataKey="accuracy" fill="#15847d" radius={[0, 6, 6, 0]} barSize={18} /></BarChart></ResponsiveContainer></div></Card>
    </div>
    <Card><div className="card-heading"><div><span className="eyebrow">Just now</span><h2>Recent classroom activity</h2></div><span className="soft-label"><Clock3 size={15} /> Latest 8 signals</span></div><div className="activity-list">{data.recent_activity.map(item => <div className="activity-row" key={item.id}><span className={item.is_correct ? "status success" : "status warning"}>{item.is_correct ? <CheckCircle2 /> : <XCircle />}</span><div><strong>{item.student_name}</strong><span>{item.is_correct ? `${item.topic} · concept understood` : item.misconception_label}</span></div><time>{new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time></div>)}</div></Card>
    {(selected || script) && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-label="Re-teach script"><button className="modal-close" onClick={() => { setSelected(null); setScript(""); }}><X /></button><div className="modal-icon"><WandSparkles /></div><span className="eyebrow">Two-minute re-teach</span><h2>{selected?.label}</h2>{reteach.isPending ? <div className="generating"><Spinner /><p>Turning this class signal into a focused explanation…</p></div> : reteach.error ? <ErrorNotice message={reteach.error.message} /> : <><div className="script-box">{script}</div><div className="modal-actions"><button className="secondary-button" onClick={() => navigator.clipboard.writeText(script)}>Copy script</button><button className="primary-button" onClick={() => { setSelected(null); setScript(""); }}>Ready to teach <ArrowUpRight size={17} /></button></div></>}</section></div>}
  </>;
}

function StudentsView() {
  const { data = [], isLoading, error } = useQuery({ queryKey: ["students"], queryFn: api.students });
  return <><div className="page-heading"><div><span className="eyebrow">40 learner profiles</span><h1>Learner progress</h1><p>Scan participation and current learning signals across the class.</p></div></div>{isLoading ? <div className="center-loader"><Spinner /></div> : error ? <ErrorNotice message={(error as Error).message} /> : <Card><div className="student-table"><div className="table-head"><span>Learner</span><span>Attempts</span><span>Accuracy</span><span>Active gaps</span></div>{data.map((student, index) => <div className="table-row" key={student.id}><div><i style={{ background: ["#0f766e", "#d97706", "#64748b"][index % 3] }}>{student.name.split(" ").map(x => x[0]).slice(0, 2).join("")}</i><strong>{student.name}</strong></div><span>{student.attempts}</span><span><b className={student.accuracy >= 70 ? "positive" : student.accuracy ? "caution" : "neutral"}>{student.accuracy}%</b></span><span><Badge tone={student.active_gaps > 1 ? "red" : student.active_gaps ? "amber" : "gray"}>{student.active_gaps}</Badge></span></div>)}</div></Card>}</>;
}

export function TeacherApp({ view }: { view: string }) {
  return view === "students" ? <StudentsView /> : <DashboardView />;
}

