import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, Check, FileImage, FileText, Pencil, Plus, Sparkles, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

import { api } from "../api";
import { Badge, Card, EmptyState, ErrorNotice, Spinner } from "../components/ui";
import type { Portion } from "../types";

export function PortionsPage({ classId }: { classId: number }) {
  const input = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Portion | null>(null);
  const { data = [], isLoading, error } = useQuery({ queryKey: ["portions", classId], queryFn: () => api.portions(classId) });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["portions", classId] });
  const upload = useMutation({ mutationFn: (file: File) => api.uploadPortion(classId, file), onSuccess: portion => { refresh(); setEditing(portion); } });
  const update = useMutation({ mutationFn: (portion: Portion) => api.updatePortion(classId, portion), onSuccess: portion => { refresh(); setEditing(portion); } });
  const publish = useMutation({ mutationFn: (id: number) => api.publishPortion(classId, id), onSuccess: () => { refresh(); setEditing(null); } });
  const handleFile = (file?: File) => file && upload.mutate(file);
  if (isLoading) return <div className="center-loader"><Spinner /></div>;
  if (error) return <ErrorNotice message={(error as Error).message} />;
  return <>
    <div className="page-heading"><div><span className="eyebrow">Class-specific curriculum</span><h1>Portions</h1><p>Upload a PDF or page image. AI builds an editable draft before anything reaches students.</p></div><button className="primary-button" onClick={() => input.current?.click()}><Plus size={17} /> Upload portion</button><input ref={input} hidden type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={event => handleFile(event.target.files?.[0])} /></div>
    <div className="upload-zone" onClick={() => input.current?.click()}><UploadCloud /><div><strong>{upload.isPending ? "Reading and structuring your portion…" : "Drop a portion page here or choose a file"}</strong><span>PDF, PNG or JPEG · maximum 20 MB · teacher review required</span></div>{upload.isPending && <Spinner />}</div>
    {upload.error && <ErrorNotice message={upload.error.message} />}
    {!data.length ? <Card><EmptyState icon={<FileText />} title="No portions yet" text="Upload this class's current syllabus portion to create focused learning content." /></Card> : <div className="portion-grid">{data.map(portion => <Card key={portion.id} className="portion-card"><div className="portion-file"><span>{portion.original_filename.endsWith("pdf") ? <FileText /> : <FileImage />}</span><Badge tone={portion.status === "published" ? "teal" : portion.status === "draft" ? "amber" : "gray"}>{portion.status}</Badge></div><h2>{portion.title}</h2><p>{portion.subject} · {portion.topics.length} topics · {portion.questions.length} questions</p><div className="portion-meta"><span><Sparkles size={14} /> {portion.provider} extraction</span><span>{new Date(portion.created_at).toLocaleDateString()}</span></div>{portion.status === "draft" ? <button className="secondary-button full" onClick={() => setEditing(structuredClone(portion))}><Pencil size={16} /> Review draft</button> : <div className="published-label"><Check /> Available to this class</div>}</Card>)}</div>}
    {editing && <div className="modal-backdrop"><section className="modal portion-editor" role="dialog" aria-modal="true" aria-label="Review portion"><span className="eyebrow">AI draft · review required</span><input className="title-input" value={editing.title} onChange={event => setEditing({ ...editing, title: event.target.value })} /><input className="subject-input" value={editing.subject} onChange={event => setEditing({ ...editing, subject: event.target.value })} /><h3>Topics and learning outcomes</h3><div className="draft-list">{editing.topics.map((topic, index) => <div key={index}><input value={topic.title} onChange={event => { const topics = [...editing.topics]; topics[index] = { ...topic, title: event.target.value }; setEditing({ ...editing, topics }); }} /><textarea rows={2} value={topic.learning_outcome} onChange={event => { const topics = [...editing.topics]; topics[index] = { ...topic, learning_outcome: event.target.value }; setEditing({ ...editing, topics }); }} /></div>)}</div><h3>Generated practice</h3><div className="question-review">{editing.questions.map((question, index) => <div key={index}><strong>{index + 1}. {question.text}</strong><span>{question.topic} · {question.difficulty}</span></div>)}</div>{(update.error || publish.error) && <ErrorNotice message={(update.error || publish.error)!.message} />}<div className="modal-actions"><button className="secondary-button" onClick={() => setEditing(null)}>Close</button><button className="secondary-button" disabled={update.isPending} onClick={() => update.mutate(editing)}>Save draft</button><button className="primary-button" disabled={publish.isPending || update.isPending} onClick={() => publish.mutate(editing.id)}>{publish.isPending ? <Spinner /> : <Check size={16} />} Publish to students</button></div></section></div>}
  </>;
}

