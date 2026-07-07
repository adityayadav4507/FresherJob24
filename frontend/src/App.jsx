import React, { useState } from 'react';

const API_HOST = window.location.port === '5173' ? 'http://localhost:8000' : '';

export default function App() {
  const [searchQuery, setSearchQuery] = useState('');
  
  // Pipeline loading states
  const [loadingGreenhouse, setLoadingGreenhouse] = useState(false);
  const [loadingLever, setLoadingLever] = useState(false);
  const [loadingLinkedin, setLoadingLinkedin] = useState(false);
  
  // Pipeline feeds
  const [greenhouseJobs, setGreenhouseJobs] = useState([]);
  const [leverJobs, setLeverJobs] = useState([]);
  const [linkedinJobs, setLinkedinJobs] = useState([]);
  
  const [activeTab, setActiveTab] = useState('greenhouse'); // greenhouse, lever, linkedin

  // Logs modal state
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [modalLogs, setModalLogs] = useState([]);
  const [modalPipeline, setModalPipeline] = useState('');

  const handleOpenLogs = (pipeline) => {
    setModalPipeline(pipeline);
    setModalLogs([]);
    setShowLogsModal(true);
    fetch(`${API_HOST}/api/logs/${pipeline}`)
      .then(res => res.json())
      .then(data => {
        setModalLogs(data.logs || []);
      })
      .catch(err => {
        console.error("Failed to load logs:", err);
        setModalLogs(["Error: Failed to fetch log stream from backend API."]);
      });
  };

  // Trigger search pipelines: run recommendation agent once, then feed roles to all 3 pipelines
  const handleSearch = (e) => {
    if (e) e.preventDefault();
    const cleanQuery = searchQuery.trim();
    if (!cleanQuery) return;
    
    // Clear feeds and set all loading states
    setLoadingGreenhouse(true);
    setLoadingLever(true);
    setLoadingLinkedin(true);
    
    setGreenhouseJobs([]);
    setLeverJobs([]);
    setLinkedinJobs([]);

    // Step 1: Run Recommendation Agent exactly once per query
    fetch(`${API_HOST}/api/recommendations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_role: cleanQuery })
    })
      .then(res => res.json())
      .then(recData => {
        const recommendedRoles = recData.recommended_roles || [cleanQuery];

        // Step 2: Feed recommended roles to all 3 pipelines concurrently
        // 1. Greenhouse Pipeline
        fetch(`${API_HOST}/api/jobs/search/greenhouse`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_role: cleanQuery, recommended_roles: recommendedRoles })
        })
          .then(res => res.json())
          .then(data => {
            setGreenhouseJobs(data.greenhouse || []);
          })
          .catch(err => console.error("Greenhouse pipeline failed:", err))
          .finally(() => setLoadingGreenhouse(false));

        // 2. Lever Pipeline
        fetch(`${API_HOST}/api/jobs/search/lever`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_role: cleanQuery, recommended_roles: recommendedRoles })
        })
          .then(res => res.json())
          .then(data => {
            setLeverJobs(data.lever || []);
          })
          .catch(err => console.error("Lever pipeline failed:", err))
          .finally(() => setLoadingLever(false));

        // 3. LinkedIn Search Pipeline
        fetch(`${API_HOST}/api/jobs/search/linkedin`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_role: cleanQuery, recommended_roles: recommendedRoles })
        })
          .then(res => res.json())
          .then(data => {
            setLinkedinJobs(data.linkedin || []);
          })
          .catch(err => console.error("LinkedIn pipeline failed:", err))
          .finally(() => setLoadingLinkedin(false));
      })
      .catch(err => {
        console.error("Recommendations lookup failed:", err);
        setLoadingGreenhouse(false);
        setLoadingLever(false);
        setLoadingLinkedin(false);
      });
  };

  const getActiveJobsList = () => {
    if (activeTab === 'greenhouse') return greenhouseJobs;
    if (activeTab === 'lever') return leverJobs;
    return linkedinJobs;
  };

  const isCurrentTabLoading = () => {
    if (activeTab === 'greenhouse') return loadingGreenhouse;
    if (activeTab === 'lever') return loadingLever;
    return loadingLinkedin;
  };

  const anyPipelineRunning = () => {
    return loadingGreenhouse || loadingLever || loadingLinkedin;
  };

  return (
    <div className="app-container no-print">
      {/* Navigation Top Bar */}
      <header className="app-header">
        <div className="logo-block">
          <i className="fa-solid fa-briefcase logo-icon"></i>
          <div>
            <h1>JobFinder</h1>
            <span>Real-time Isolated Discovery</span>
          </div>
        </div>
        <div className="header-status" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          <span style={{ marginRight: '16px' }}>
            <i className="fa-solid fa-circle-check" style={{ color: 'var(--accent-green)' }}></i> 3 Pipelines Active
          </span>
          <span><i className="fa-solid fa-code-branch"></i> Progressive Loader</span>
        </div>
      </header>

      <section className="screen-pane">
        {/* Top Search Input Box & Button */}
        <div className="glass-card" style={{ padding: '24px', textAlign: 'center', marginBottom: '30px' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '16px', justifyContent: 'center', alignItems: 'center', maxWidth: '700px', margin: '0 auto' }}>
            <input 
              type="text" 
              placeholder="Enter Target IT Job Role (e.g. SDE, AI Engineer, Backend Developer)" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ flex: 1, padding: '14px 20px', fontSize: '16px', borderRadius: '30px' }}
              required 
            />
            <button type="submit" className="btn btn-primary" style={{ padding: '14px 36px', fontSize: '14px', borderRadius: '30px' }} disabled={anyPipelineRunning()}>
              {anyPipelineRunning() ? "Searching..." : "Agent Find Job"} <i className="fa-solid fa-wand-magic-sparkles"></i>
            </button>
          </form>
          <p style={{ marginTop: '12px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            Fires parallel crawler queries that stream matching jobs to your dashboard in real-time as they complete.
          </p>
        </div>

        {/* Tab Controls and Debug Log Button */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', gap: '20px', flexWrap: 'wrap' }}>
          <div className="category-tabs" style={{ marginBottom: 0 }}>
            <button className={`category-tab ${activeTab === 'greenhouse' ? 'active' : ''}`} onClick={() => setActiveTab('greenhouse')}>
              <i className="fa-solid fa-rocket"></i> Greenhouse Startup Feed ({greenhouseJobs.length})
              {loadingGreenhouse && <span className="tab-spinner inline-spinner"></span>}
            </button>
            <button className={`category-tab ${activeTab === 'lever' ? 'active' : ''}`} onClick={() => setActiveTab('lever')}>
              <i className="fa-solid fa-file-code"></i> Lever Startup Feed ({leverJobs.length})
              {loadingLever && <span className="tab-spinner inline-spinner"></span>}
            </button>
            <button className={`category-tab ${activeTab === 'linkedin' ? 'active' : ''}`} onClick={() => setActiveTab('linkedin')}>
              <i className="fa-brands fa-linkedin-in"></i> LinkedIn Search Feed ({linkedinJobs.length})
              {loadingLinkedin && <span className="tab-spinner inline-spinner"></span>}
            </button>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => handleOpenLogs(activeTab)} style={{ borderRadius: '30px', padding: '10px 20px' }}>
            <i className="fa-solid fa-bug" style={{ marginRight: '8px' }}></i> View {activeTab} Pipeline Logs
          </button>
        </div>

        {/* Feed List or Loader */}
        {isCurrentTabLoading() ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <h3>Running Pipeline Discovery...</h3>
            <p>Crawling active matching jobs (7-day startup index, India/Remote, fresher experience)...</p>
          </div>
        ) : (
          <>
            {getActiveJobsList().length === 0 ? (
              <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <p>No jobs found on this pipeline matching the active filters.</p>
                <p className="small-text" style={{ marginTop: '6px' }}>
                  Note: start-ups do not update listings daily. Tap other feeds or View Pipeline Logs to inspect details.
                </p>
              </div>
            ) : (
              <div className="jobs-category-list">
                {getActiveJobsList().map((job, index) => (
                  <div className="job-list-card glass-card" key={job.id}>
                    <div className="job-info-left">
                      <h3>{index + 1}. {job.company}</h3>
                      <p className="job-info-meta">{job.title} • {job.location}</p>
                      <div className="job-info-tags">
                        <span className="badge badge-blue">{job.source}</span>
                        {job.easy_apply && <span className="badge badge-easyapply"><i className="fa-solid fa-bolt"></i> Easy Apply</span>}
                        {job.date_posted && <span className="badge badge-green">{job.date_posted}</span>}
                      </div>
                    </div>
                    <a href={job.url} target="_blank" rel="noreferrer" className="btn btn-primary btn-sm" style={{ textDecoration: 'none' }}>
                      Apply Now <i className="fa-solid fa-arrow-up-right-from-square"></i>
                    </a>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </section>

      {/* Debug Logs Modal */}
      {showLogsModal && (
        <div className="logs-modal-backdrop" style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)',
          display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }}>
          <div className="glass-card" style={{
            width: '90%', maxWidth: '850px', maxHeight: '85vh',
            padding: '30px', display: 'flex', flexDirection: 'column',
            boxShadow: '0 20px 50px rgba(0,0,0,0.8)', borderRadius: '16px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '16px' }}>
              <h2 style={{ margin: 0, fontSize: '20px', textTransform: 'capitalize', color: '#fff' }}>
                <i className="fa-solid fa-terminal" style={{ marginRight: '12px', color: 'var(--accent-purple)' }}></i>
                {modalPipeline} Pipeline Trace Logs
              </h2>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowLogsModal(false)} style={{ borderRadius: '20px', padding: '6px 16px' }}>
                Close <i className="fa-solid fa-xmark" style={{ marginLeft: '4px' }}></i>
              </button>
            </div>
            <div style={{
              flex: 1, overflowY: 'auto', backgroundColor: '#07080d',
              fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
              fontSize: '13px', padding: '20px', borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.05)', color: '#00ff66',
              whiteSpace: 'pre-wrap', lineHeight: '1.7', textAlign: 'left'
            }}>
              {modalLogs.length === 0 ? (
                <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '40px 0' }}>
                  <div className="spinner" style={{ margin: '0 auto 16px auto', width: '30px', height: '30px' }}></div>
                  Loading pipeline event traces...
                </div>
              ) : (
                modalLogs.join('\n')
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
