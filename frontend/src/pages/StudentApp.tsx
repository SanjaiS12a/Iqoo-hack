import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, BookOpen, Check, CheckCircle2, ChevronRight, CircleHelp, Clock3, Flame, Lightbulb, Mic, RefreshCw, Send, Sparkles, Target, Trophy, XCircle } from "lucide-react";
import { useState } from "react";

import { api } from "../api";
import { Badge, Card, EmptyState, ErrorNotice, Spinner } from "../components/ui";
import type { Diagnosis, Question } from "../types";

function Welcome({ onNavigate }: { onNavigate: (view: string) => void }) {
  const { data, isLoading, error } = useQuery({ queryKey: ["overview"], queryFn: api.overview });
  if (isLoading) return <div className="center-loader"><Spinner /></div>;
  if (error || !data) return <ErrorNotice message={(error as Error)?.message ?? "Could not load your progress"} />;
  const metrics = [
    ["Accuracy", `${data.accuracy}%`, Target, "teal"],
    ["Questions tried", data.questions_attempted, BookOpen, "blue"],
    ["Learning streak", `${data.streak} days`, Flame, "amber"],
    ["Active gaps", data.active_gaps, Lightbulb, "red"],
  ] as const;
  return <>
    <div className="page-heading"><div><span className="eyebrow">Monday, 7 September</span><h1>Good evening, Aarav</h1><p>One focused step today can clear your biggest learning gap.</p></div><button className="primary-button" onClick={() => onNavigate("practice")}>Continue practice <ArrowRight size={18} /></button></div>
    <div className="metric-grid">{metrics.map(([label, value, Icon, tone]) => <Card key={label} className="metric-card"><div className={`metric-icon ${tone}`}><Icon /></div><div><span>{label}</span><strong>{value}</strong></div></Card>)}</div>
    <div className="two-column wide-left">
      <Card><div className="card-heading"><div><span className="eyebrow">Your next move</span><h2>Build confidence with balance</h2></div><Badge tone="amber">High priority</Badge></div><div className="focus-card"><div className="focus-number">01</div><div><h3>Solving linear equations</h3><p>Practice moving one term at a time while keeping both sides balanced.</p><div className="progress-line"><i style={{ width: "42%" }} /></div><span>2 of 5 checkpoints complete</span></div></div><button className="text-button" onClick={() => onNavigate("practice")}>Start a 10-minute practice <ChevronRight size={17} /></button></Card>
      <Card><div className="card-heading"><div><span className="eyebrow">This week</span><h2>Your momentum</h2></div><Trophy className="muted-icon" /></div><div className="week-dots">{["M", "T", "W", "T", "F", "S", "S"].map((day, index) => <div key={`${day}${index}`}><i className={index < 4 ? "done" : index === 4 ? "today" : ""}>{index < 4 ? <Check size={14} /> : ""}</i><span>{day}</span></div>)}</div><p className="encouragement"><Sparkles size={17} /> Four focused days in a row. Keep it light and consistent.</p></Card>
    </div>
    <Card><div className="card-heading"><div><span className="eyebrow">Learning history</span><h2>Recent attempts</h2></div></div>{data.recent.length ? <div className="activity-list">{data.recent.map(item => <div className="activity-row" key={item.id}><span className={item.is_correct ? "status success" : "status warning"}>{item.is_correct ? <CheckCircle2 /> : <XCircle />}</span><div><strong>{item.topic}</strong><span>{item.is_correct ? "Concept understood" : item.misconception_label}</span></div><time>{new Date(item.created_at).toLocaleDateString()}</time></div>)}</div> : <EmptyState icon={<BookOpen />} title="Your learning story starts here" text="Try a question to see your progress." />}</Card>
  </>;
}

function Practice() {
  const [selected, setSelected] = useState<Question | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<Diagnosis | null>(null);
  const queryClient = useQueryClient();
  const { data: questions, isLoading, error } = useQuery({ queryKey: ["questions"], queryFn: api.questions });
  const submit = useMutation({ mutationFn: () => api.submit(selected!.id, answer), onSuccess: value => { setResult(value); queryClient.invalidateQueries({ queryKey: ["overview"] }); } });
  if (isLoading) return <div className="center-loader"><Spinner /></div>;
  if (error || !questions) return <ErrorNotice message={(error as Error)?.message ?? "Could not load questions"} />;
  if (!selected) return <><div className="page-heading"><div><span className="eyebrow">Question bank</span><h1>Choose your next challenge</h1><p>Show your working so ClassMind can understand how you think.</p></div></div><div className="question-grid">{questions.map((q, index) => <button className="question-card" key={q.id} onClick={() => setSelected(q)}><div className="question-top"><span>0{index + 1}</span><Badge tone={q.difficulty === "Challenge" ? "amber" : "teal"}>{q.difficulty}</Badge></div><h2>{q.topic}</h2><p>{q.text}</p><div><span>Demo exam weight {Math.round(q.exam_frequency_score * 100)}%</span><ArrowRight /></div></button>)}</div><p className="data-note">Exam weights are illustrative values for this demo.</p></>;
  return <><button className="back-button" onClick={() => { setSelected(null); setResult(null); setAnswer(""); }}>← Back to question bank</button><div className="practice-layout"><Card className="problem-card"><div className="card-heading"><div><Badge>{selected.difficulty}</Badge><h1>{selected.topic}</h1></div><span className="question-count">Focused practice</span></div><div className="problem-text">{selected.text}</div><details><summary><Lightbulb size={17} /> Need a hint?</summary><p>{selected.hint}</p></details></Card><Card><span className="eyebrow">Your working</span><h2>Think on the page</h2><p className="field-help">Include each step, even if you are unsure. The reasoning helps diagnose the exact gap.</p><textarea value={answer} onChange={e => setAnswer(e.target.value)} placeholder="Example: 2x + 4 = 10&#10;2x = 10 - 4&#10;..." rows={9} /><button className="primary-button full" disabled={!answer.trim() || submit.isPending} onClick={() => submit.mutate()}>{submit.isPending ? <><Spinner /> Checking your steps…</> : <>Check my reasoning <Sparkles size={18} /></>}</button>{submit.error && <ErrorNotice message={submit.error.message} />}</Card></div>{result && <div className={`feedback-panel ${result.is_correct ? "correct" : "incorrect"}`}><div className="feedback-icon">{result.is_correct ? <CheckCircle2 /> : <Lightbulb />}</div><div><span className="eyebrow">{result.is_correct ? "Concept clear" : "Learning signal found"}</span><h2>{result.is_correct ? "That reasoning holds up." : result.misconception_label}</h2><p>{result.micro_explanation}</p><span className="confidence">Diagnosis confidence · {Math.round(result.confidence * 100)}%</span></div><button className="secondary-button" onClick={() => { setSelected(null); setResult(null); setAnswer(""); }}>Try another</button></div>}</>;
}

function Doubts() {
  const [text, setText] = useState("");
  const queryClient = useQueryClient();
  const { data = [], isLoading } = useQuery({ queryKey: ["doubts"], queryFn: api.doubts });
  const ask = useMutation({ mutationFn: () => api.askDoubt(text), onSuccess: () => { setText(""); queryClient.invalidateQueries({ queryKey: ["doubts"] }); } });
  const startSpeech = () => {
    const SpeechRecognition = (window as unknown as { webkitSpeechRecognition?: new () => { lang: string; start: () => void; onresult: (event: { results: ArrayLike<{ 0: { transcript: string } }> }) => void } }).webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("Speech input is not available in this browser. You can type your doubt instead.");
    const recognition = new SpeechRecognition(); recognition.lang = "en-IN"; recognition.onresult = event => setText(event.results[0][0].transcript); recognition.start();
  };
  return <><div className="page-heading"><div><span className="eyebrow">Your private tutor</span><h1>Ask without hesitation</h1><p>Type or speak naturally. Hindi or English phrasing is welcome when OpenAI mode is connected.</p></div></div><Card className="ask-card"><div className="ask-input"><textarea value={text} onChange={e => setText(e.target.value)} rows={3} placeholder="What part of linear equations feels confusing?" /><button className="mic-button" onClick={startSpeech} aria-label="Speak your doubt"><Mic /></button></div><div className="ask-footer"><span><Sparkles size={16} /> Demo mode recognizes common equation doubts</span><button className="primary-button" disabled={text.trim().length < 3 || ask.isPending} onClick={() => ask.mutate()}>{ask.isPending ? <Spinner /> : <Send size={17} />} Ask ClassMind</button></div>{ask.error && <ErrorNotice message={ask.error.message} />}</Card><div className="conversation-list">{isLoading ? <Spinner /> : data.length ? data.map(item => <Card key={item.id} className="conversation"><div className="student-message"><span>You asked</span><p>{item.doubt_text}</p></div><div className="ai-message"><div className="ai-avatar"><Sparkles /></div><div><div><strong>ClassMind</strong><Badge>{item.concept_tag.replaceAll("_", " ")}</Badge></div><p>{item.ai_response}</p></div></div></Card>) : <EmptyState icon={<CircleHelp />} title="No doubt is too small" text="Ask your first question and build understanding one step at a time." />}</div></>;
}

function Plan() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["plan"], queryFn: api.plan });
  const generate = useMutation({ mutationFn: api.generatePlan, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plan"] }) });
  const update = useMutation({ mutationFn: ({ id, completed }: { id: number; completed: boolean }) => api.updatePlan(id, completed), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plan"] }) });
  if (isLoading) return <div className="center-loader"><Spinner /></div>;
  if (error) return <ErrorNotice message={(error as Error).message} />;
  const completed = data?.items.filter(item => item.completed).length ?? 0;
  return <><div className="page-heading"><div><span className="eyebrow">Exam-aware revision</span><h1>Your study plan</h1><p>Weak concepts and illustrative exam weights combine into one clear order.</p></div><button className="secondary-button" onClick={() => generate.mutate()} disabled={generate.isPending}><RefreshCw size={17} /> {data?.items.length ? "Refresh priorities" : "Generate my plan"}</button></div>{!data?.items.length ? <Card><EmptyState icon={<ClipboardIcon />} title="Ready when you are" text="Generate a plan from your learning signals and the demo exam weights." /></Card> : <><Card className="plan-progress"><div><span className="eyebrow">Plan progress</span><h2>{completed} of {data.items.length} priorities complete</h2></div><div className="circle-progress">{Math.round(completed / data.items.length * 100)}%</div></Card><div className="plan-list">{data.items.map((item, index) => <Card className={`plan-item ${item.completed ? "plan-done" : ""}`} key={item.id}><button className="check-button" aria-label={`Mark ${item.topic} ${item.completed ? "incomplete" : "complete"}`} onClick={() => update.mutate({ id: item.id, completed: !item.completed })}>{item.completed ? <Check /> : index + 1}</button><div className="plan-copy"><div><h2>{item.topic}</h2><Badge tone={index === 0 ? "amber" : "gray"}>{Math.round(item.priority_score)} priority</Badge></div><p>{item.reason}</p><span><Clock3 size={15} /> {item.estimated_minutes} minutes</span></div><ChevronRight /></Card>)}</div><p className="data-note">Exam weights are illustrative demo values, not claims based on an official past-paper dataset.</p></>}{generate.error && <ErrorNotice message={generate.error.message} />}</>;
}

function ClipboardIcon() { return <Target />; }

export function StudentApp({ view, onNavigate }: { view: string; onNavigate: (view: string) => void }) {
  if (view === "practice") return <Practice />;
  if (view === "doubts") return <Doubts />;
  if (view === "plan") return <Plan />;
  return <Welcome onNavigate={onNavigate} />;
}
