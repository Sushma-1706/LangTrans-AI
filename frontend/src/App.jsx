import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, PlayCircle, Clock, CheckCircle, Download, History, Sparkles, Languages, Trash2 } from 'lucide-react';
import { format } from 'date-fns';
import './App.css';

const API_URL = "http://localhost:8000";

function App() {
  const [file, setFile] = useState(null);
  const [translate, setTranslate] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // History State
  const [history, setHistory] = useState([]);

  // Load History
  useEffect(() => {
    const saved = localStorage.getItem('ai_summary_history');
    if (saved) {
      setHistory(JSON.parse(saved));
    }
  }, []);

  // Save to History
  const addToHistory = (resultData) => {
    const newEntry = {
      id: Date.now(),
      date: new Date().toISOString(),
      fileName: file ? file.name : "Unknown File",
      result: resultData.result,
      transcript: resultData.transcript
    };
    
    const updatedHistory = [newEntry, ...history].slice(0, 15);
    setHistory(updatedHistory);
    localStorage.setItem('ai_summary_history', JSON.stringify(updatedHistory));
  };

  // --- NEW: Delete Function ---
  const deleteHistoryItem = (e, id) => {
    e.stopPropagation(); // Prevents the item from opening when you click delete
    const updatedHistory = history.filter(item => item.id !== id);
    setHistory(updatedHistory);
    localStorage.setItem('ai_summary_history', JSON.stringify(updatedHistory));
  };

  const loadFromHistory = (entry) => {
    setData({ result: entry.result, transcript: entry.transcript });
    setStatus("completed");
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("translate", translate);

    try {
      setLoading(true);
      setProgress(10);
      setData(null);
      
      const res = await axios.post(`${API_URL}/upload`, formData);
      setJobId(res.data.job_id);
      setStatus("queued");
    } catch (err) {
      console.error(err);
      setLoading(false);
      alert("Upload failed.");
    }
  };

  useEffect(() => {
    let interval;
    if (jobId && status !== "completed" && status !== "failed") {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_URL}/job/${jobId}`);
          setStatus(res.data.status);
          setProgress(res.data.progress || 20);

          if (res.data.status === "completed") {
            setData(res.data);
            setLoading(false);
            setProgress(100);
            addToHistory(res.data);
          } else if (res.data.status === "failed") {
            setLoading(false);
            alert("Job failed: " + res.data.error);
          }
        } catch (e) { console.error(e); }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [jobId, status]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const downloadJSON = () => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([JSON.stringify(data.result, null, 2)], { type: 'application/json' }));
    link.download = "summary_report.json";
    link.click();
  };

  const downloadTranscript = () => {
    if (!data.transcript) return;
    const textContent = data.transcript.map(s => `[${formatTime(s.start)}] ${s.text}`).join("\n");
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([textContent], { type: 'text/plain' }));
    link.download = "transcript.txt";
    link.click();
  };

  return (
    <div className="app-layout">
      
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="logo-area">
          <Sparkles size={24} color="#a5b4fc" />
          <span>LangTrans-AI</span>
        </div>
        
        <h3><History size={16}/> History</h3>
        <div className="history-list">
          {history.length === 0 && <p className="empty-history">No history yet.</p>}
          {history.map(item => (
            <div key={item.id} className="history-item" onClick={() => loadFromHistory(item)}>
              
              {/* Content (Clickable) */}
              <div className="history-content">
                <div className="history-title">{item.result.title || item.fileName}</div>
                <div className="history-date">{format(new Date(item.date), 'MMM d, h:mm a')}</div>
              </div>

              {/* Delete Button (Stops Click Event) */}
              <button 
                className="delete-btn" 
                onClick={(e) => deleteHistoryItem(e, item.id)}
                title="Delete this summary"
              >
                <Trash2 size={16} />
              </button>

            </div>
          ))}
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="main-content">
        <div className="center-wrapper">
          
          <div className="hero-header">
            <h1>Multimodal AI Summarizer</h1>
            <p>Upload video or audio to generate structured intelligence.</p>
          </div>

          {/* UPLOAD CARD */}
          <div className="glass-card">
            <div className="upload-area">
              <UploadCloud size={48} color="#6366f1" />
              <p style={{marginTop: '15px', color: '#64748b'}}>
                {file ? `Selected: ${file.name}` : "Drag & Drop or Click to Upload"}
              </p>
              <input 
                type="file" 
                id="fileInput" 
                style={{display:'none'}} 
                onChange={(e) => setFile(e.target.files[0])} 
                accept="audio/*,video/*"
              />
              <button className="upload-btn" onClick={() => document.getElementById('fileInput').click()}>
                 Choose File
              </button>
            </div>

            <div style={{marginTop: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px'}}>
              <input 
                type="checkbox" 
                id="transToggle"
                checked={translate} 
                onChange={(e) => setTranslate(e.target.checked)} 
                style={{width: '18px', height: '18px', cursor: 'pointer', accentColor: '#6366f1'}}
              />
              <label htmlFor="transToggle" style={{cursor: 'pointer', fontSize: '0.95rem', color: '#475569', display:'flex', alignItems:'center', gap:'6px'}}>
                <Languages size={16} /> Translate to English (if Foreign Audio)
              </label>
            </div>

            {loading && (
              <div style={{marginTop: '25px'}}>
                <p style={{marginBottom:'5px', fontSize:'0.9rem', color:'#64748b'}}>
                    Status: <b>{status?.replace('_', ' ').toUpperCase()}</b>
                </p>
                <div style={{background: '#e2e8f0', height: '8px', borderRadius: '4px', overflow:'hidden'}}>
                   <div style={{width: `${progress}%`, background: '#6366f1', height: '100%', transition: 'width 0.5s ease'}}></div>
                </div>
              </div>
            )}

            {!loading && file && (
              <button className="upload-btn" style={{marginTop:'25px'}} onClick={handleUpload}>
                <Sparkles size={18}/> Generate Summary
              </button>
            )}
          </div>

          {/* RESULTS */}
          {data && data.result && (
            <div className="glass-card result-container">
              <div className="result-header">
                <h2>{data.result.title}</h2>
                <div style={{display:'flex', gap:'10px'}}>
                   <span className="badge">⏱ {data.result.duration}</span>
                   <span className="badge">📉 {data.result.compression_ratio}</span>
                </div>
              </div>

              <div style={{textAlign:'left'}}>
                <h3>Executive Summary</h3>
                <p style={{lineHeight: '1.6', color: '#334155'}}>{data.result.executive_summary}</p>
              </div>

              <div className="grid-2">
                <div className="info-box">
                   <h3><FileText size={18}/> Key Topics</h3>
                   <ul>{data.result.key_topics?.map((t, i) => <li key={i}>{t}</li>)}</ul>
                </div>
                <div className="info-box">
                   <h3><CheckCircle size={18}/> Action Items</h3>
                   <ul>{data.result.action_items?.map((t, i) => <li key={i}>{t}</li>)}</ul>
                </div>
              </div>

              <div style={{textAlign:'left', marginTop:'30px'}}>
                 <h3><PlayCircle size={18}/> Full Transcript</h3>
                 <div className="transcript-preview">
                    {data.transcript?.slice(0, 50).map((seg, i) => (
                      <div key={i} className="t-row">
                        <span className="t-time">{formatTime(seg.start)}</span>
                        <span>{seg.text}</span>
                      </div>
                    ))}
                 </div>
              </div>
              
              <div style={{marginTop: '25px', display:'flex', gap:'15px', justifyContent:'center'}}>
                 <button className="upload-btn" style={{background:'#334155', margin:0}} onClick={downloadJSON}>
                    <Download size={18}/> JSON Report
                 </button>
                 <button className="upload-btn" style={{background:'#334155', margin:0}} onClick={downloadTranscript}>
                    <Download size={18}/> Transcript
                 </button>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}

export default App;