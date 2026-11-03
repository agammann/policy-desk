"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowDown, ArrowRight, ArrowUpRight, BookOpen, Check, ChevronDown, CircleHelp, FileText, FolderOpen, LoaderCircle, MessageSquareText, Plus, ShieldCheck, Sparkles, Trash2, UploadCloud, X } from "lucide-react";
import { API, request, type Answer, type Citation, type DocumentRecord, type DocumentsResponse } from "./api";

type Message = { question: string; result: Answer };
const suggestions = ["What is the policy for taking time off?", "What expenses are eligible for reimbursement?", "How should security incidents be reported?"];

function FileIcon() { return <span className="file-icon"><FileText size={18} strokeWidth={1.7}/></span>; }
function Brand() { return <div className="brand"><span className="brand-mark"><BookOpen size={18}/></span><span>Policy Desk</span></div>; }
function AnswerText({ text, onCitation }: { text: string; onCitation: (id: number) => void }) {
  return <>{text.split(/(\[\d+\])/g).map((part, index) => /^\[\d+\]$/.test(part) ? <button type="button" className="inline-citation" onClick={() => onCitation(Number(part.slice(1, -1)))} key={index} aria-label={`View source ${part.slice(1, -1)}`}>{part.slice(1, -1)}</button> : <span key={index}>{part}</span>)}</>;
}
function Source({ citation, selected }: { citation: Citation; selected: boolean }) {
  return <article className={`source ${selected ? "selected" : ""}`} id={`source-${citation.id}`}>
    <div className="source-top"><div className="source-title"><span className="source-number">{citation.id}</span><div><strong>{citation.document_name}</strong><span>Page {citation.page}</span></div></div><a className="source-link" href={`${API}/api/documents/${encodeURIComponent(citation.document_id)}/file#page=${citation.page}`} target="_blank" rel="noreferrer" aria-label={`Open ${citation.document_name} at page ${citation.page}`}><ArrowUpRight size={16}/></a></div>
    <p><mark>{citation.text}</mark></p>
  </article>;
}

export default function Home() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<number | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState("");
  const [connected, setConnected] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const displayedMessage = messages[selectedMessage ?? messages.length - 1];

  const refresh = useCallback(async () => {
    try { const data = await request<DocumentsResponse>("/api/documents"); setDocuments(data.documents); setConnected(true); }
    catch { setConnected(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => { if (messages.length) scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages]);

  async function upload(files: FileList | File[]) {
    if (busy || uploading || removing) return;
    const selected = Array.from(files);
    if (!selected.length) return;
    if (selected.some(file => !file.name.toLowerCase().endsWith(".pdf"))) { setError("Please choose PDF files only."); return; }
    setError(""); setUploading(true);
    try {
      const form = new FormData(); selected.forEach(file => form.append("files", file));
      const data = await request<DocumentsResponse>("/api/documents", { method: "POST", body: form });
      setDocuments(data.documents); setConnected(true);
      if (data.errors?.length) setError(data.errors.map(item => typeof item === "string" ? item : `${item.filename || "File"}: ${item.message || "Could not upload"}`).join(" "));
    } catch (err) { setError(err instanceof Error ? err.message : "Upload failed."); }
    finally { setUploading(false); if (fileInput.current) fileInput.current.value = ""; }
  }
  async function removeDocument(id: string) {
    if (busy || uploading || removing) return;
    setError(""); setRemoving(true);
    try { await request(`/api/documents/${encodeURIComponent(id)}`, { method: "DELETE" }); await refresh(); setMessages([]); setSelectedMessage(null); setSelectedCitation(null); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not remove document."); }
    finally { setRemoving(false); }
  }
  async function ask(text: string) {
    const trimmed = text.trim(); if (!trimmed || busy || uploading || removing || !documents.length) return;
    setError(""); setBusy(true); setQuestion("");
    try {
      const result = await request<Answer>("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: trimmed }) });
      setMessages(current => [...current, { question: trimmed, result }]); setSelectedMessage(null); setSelectedCitation(null);
    } catch (err) { setQuestion(trimmed); setError(err instanceof Error ? err.message : "Could not answer that question."); }
    finally { setBusy(false); }
  }
  function submit(event: FormEvent) { event.preventDefault(); void ask(question); }

  return <div className="app-shell">
    <aside className="sidebar">
      <Brand/>
      <div className="workspace-label">WORKSPACE</div>
      <button className="nav-item active"><MessageSquareText size={18}/> <span>Ask your policies</span></button>
      <div className="sidebar-section"><div className="section-label">YOUR LIBRARY <span>{documents.length}</span></div>
        <button className="upload-button" onClick={() => fileInput.current?.click()} disabled={busy || uploading || removing}><Plus size={17}/> {uploading ? "Adding documents…" : "Add documents"}</button>
        <input ref={fileInput} type="file" accept="application/pdf,.pdf" multiple hidden onChange={event => { if (event.target.files) void upload(event.target.files); }}/>
        <div className="document-list">{documents.length ? documents.map(document => <div className="document-row" key={document.id}><FileIcon/><div className="document-info"><strong title={document.name}>{document.name}</strong><span>{document.pages} {document.pages === 1 ? "page" : "pages"}</span></div><button className="delete-button" aria-label={`Remove ${document.name}`} title="Remove document" disabled={busy || uploading || removing} onClick={() => void removeDocument(document.id)}><Trash2 size={15}/></button></div>) : <p className="library-empty">Your documents will appear here.</p>}</div>
      </div>
      <div className="sidebar-bottom"><div className="status"><span className={connected ? "status-dot" : "status-dot offline"}></span>{connected ? "Ready to help" : "Service offline"}</div><div className="privacy"><ShieldCheck size={16}/><span>Your documents, your answers.</span></div></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div><span>Workspace</span><span className="top-separator">/</span><strong>Ask your policies</strong></div><div className="top-right"><span className="top-status"><span className="status-dot"></span> {documents.length} {documents.length === 1 ? "document" : "documents"} in library</span><button className="help-button" title="Upload policies, then ask a question about them." aria-label="Help"><CircleHelp size={18}/></button></div></header>
      <div className="content" ref={scrollRef}>
        <div className="content-inner">
          <div className="page-heading"><div><h1>Policy Q&A</h1><p>Ask questions about your policy documents and get answers with citations.</p></div>{messages.length > 0 && <button className="new-chat" disabled={busy || removing} onClick={() => { setMessages([]); setSelectedMessage(null); setSelectedCitation(null); }}><Plus size={16}/> New conversation</button>}</div>
          {error && <div className="error-banner" role="alert"><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError("")}><X size={16}/></button></div>}
          {!documents.length && <div className={`upload-zone ${dragging ? "dragging" : ""}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); void upload(event.dataTransfer.files); }}><div className="upload-icon"><UploadCloud size={23}/></div><div><strong>Start with your documents</strong><p>Upload policies or manuals to build your searchable library.</p></div><button onClick={() => fileInput.current?.click()} disabled={busy || uploading || removing}>{uploading ? "Uploading…" : "Upload PDFs"} <ArrowRight size={16}/></button><span className="upload-hint">or drag and drop PDF files here</span></div>}
          {messages.length === 0 ? <div className="welcome"><div className="welcome-symbol"><Sparkles size={22}/></div><h2>What would you like to know?</h2><p>Ask a question in your own words. We’ll find the relevant passages and show you where the answer came from.</p><div className="suggestion-label">TRY ASKING</div><div className="suggestions">{suggestions.map(item => <button key={item} onClick={() => void ask(item)} disabled={!documents.length || busy || uploading || removing}><span>{item}</span><ArrowUpRight size={16}/></button>)}</div></div> : <div className="conversation">{messages.map((message, index) => <div className="exchange" key={`${message.question}-${index}`}><div className="question-bubble">{message.question}</div><div className="answer-block"><div className="answer-head"><span className="answer-avatar"><Sparkles size={16}/></span><strong>Policy Desk</strong><span>{message.result.mode === "generated" ? "Answer" : "Relevant passages"}</span></div><div className="answer-copy"><AnswerText text={message.result.answer} onCitation={id => { setSelectedMessage(index); setSelectedCitation(id); window.setTimeout(() => document.getElementById(`source-${id}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 0); }}/></div>{index < messages.length - 1 && <div className="past-sources">{message.result.citations.length} cited {message.result.citations.length === 1 ? "source" : "sources"}</div>}</div></div>)}{busy && <div className="thinking"><LoaderCircle size={17}/> Searching your documents…</div>}</div>}
        </div>
      </div>
      <div className="composer-wrap"><form className="composer" onSubmit={submit}><input value={question} onChange={event => setQuestion(event.target.value)} placeholder={documents.length ? "Ask a question about your documents..." : "Upload a PDF to start asking questions..."} aria-label="Ask a question" disabled={!documents.length || busy || uploading || removing}/><button type="submit" disabled={!documents.length || !question.trim() || busy || uploading || removing} aria-label="Send question">{busy ? <LoaderCircle size={18} className="spin"/> : <ArrowRight size={19}/>}</button></form><p>Answers are based on your uploaded documents. Check the cited sources for context.</p></div>
    </main>
    <aside className="evidence-panel"><div className="evidence-heading"><div><div className="evidence-kicker">THE DETAILS</div><h2>Sources</h2><p>Highlighted excerpts from your documents.</p></div><span className="source-count">{displayedMessage?.result.citations.length || 0}</span></div><div className="evidence-body">{displayedMessage?.result.citations.length ? <><div className="evidence-intro"><Check size={15}/> Extracted passages cited in this answer</div>{displayedMessage.result.citations.map(citation => <Source key={citation.id} citation={citation} selected={citation.id === selectedCitation}/>)}</> : <div className="source-empty"><div><FileText size={23}/></div><strong>Your sources will appear here</strong><p>Ask a question to see the passages used to answer it, with links back to each document.</p></div>}</div><div className="evidence-footer"><ShieldCheck size={16}/><span>Review sources to verify answers.</span></div></aside>
  </div>;
}



