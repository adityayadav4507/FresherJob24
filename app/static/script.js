let currentProfile = {};
let currentJobs = [];
let selectedJob = null;
let currentLaTeX = "";
let currentCoverLetter = "";
let currentKeywords = [];
let currentEditorMode = "visual";

// Page Lifecycle
document.addEventListener("DOMContentLoaded", () => {
    loadProfile();
});

// Tab Navigation
function switchTab(tabId) {
    document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    
    document.getElementById(`tab-${tabId}`).classList.add("active");
    
    // Highlight matching link
    const activeLink = Array.from(document.querySelectorAll(".nav-item")).find(link => link.getAttribute("href") === `#${tabId}`);
    if (activeLink) activeLink.classList.add("active");
}

// Visual vs Code Editor Switcher
function switchEditorMode(mode) {
    currentEditorMode = mode;
    document.querySelectorAll(".editor-tab").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".editor-pane").forEach(pane => pane.classList.remove("active"));
    
    const clickedTab = Array.from(document.querySelectorAll(".editor-tab")).find(btn => btn.innerText.toLowerCase().includes(mode));
    if (clickedTab) clickedTab.classList.add("active");
    
    document.getElementById(`editor-${mode}`).classList.add("active");
}

// 1. Profile Persona Logic
async function loadProfile() {
    try {
        const response = await fetch("/api/profile");
        currentProfile = await response.json();
        
        // Populate inputs
        document.getElementById("prof-name").value = currentProfile.name || "";
        document.getElementById("prof-email").value = currentProfile.email || "";
        document.getElementById("prof-phone").value = currentProfile.phone || "";
        document.getElementById("prof-github").value = currentProfile.github || "";
        document.getElementById("prof-linkedin").value = currentProfile.linkedin || "";
        
        // Render Skills
        renderSkillsForm(currentProfile.skills || {});
        
        // Render Education
        renderEducationForm(currentProfile.education || []);
        
        // Render Projects
        renderProjectsForm(currentProfile.projects || []);
        
    } catch (e) {
        console.error("Error fetching profile details:", e);
    }
}

function renderSkillsForm(skills) {
    const container = document.getElementById("skills-container");
    container.innerHTML = "";
    
    const categories = ["Languages", "Frontend", "Backend", "Cloud & Dev Tools", "AI & Data"];
    categories.forEach(cat => {
        const list = skills[cat] || [];
        const div = document.createElement("div");
        div.className = "skills-category";
        div.innerHTML = `
            <label>${cat}</label>
            <input type="text" id="skills-${cat}" value="${list.join(', ')}" placeholder="Comma-separated items">
        `;
        container.appendChild(div);
    });
}

function renderEducationForm(eduList) {
    const container = document.getElementById("education-list");
    container.innerHTML = "";
    
    eduList.forEach((edu, idx) => {
        const div = document.createElement("div");
        div.className = "list-row";
        div.id = `edu-row-${idx}`;
        div.innerHTML = `
            <div class="form-group col-4">
                <label>Institution</label>
                <input type="text" class="edu-inst" value="${edu.institution || ''}" placeholder="IIT BHU">
            </div>
            <div class="form-group col-3">
                <label>Degree / Major</label>
                <input type="text" class="edu-degree" value="${edu.degree || ''}" placeholder="B.Tech Mining">
            </div>
            <div class="form-group col-2">
                <label>GPA / Grade</label>
                <input type="text" class="edu-gpa" value="${edu.gpa || ''}" placeholder="CGPA 7.26">
            </div>
            <div class="form-group col-2">
                <label>Dates</label>
                <input type="text" class="edu-dates" value="${edu.dates || ''}" placeholder="Oct 2022 - May 2026">
            </div>
            <button type="button" class="btn btn-sm btn-secondary" style="margin-top:24px;" onclick="removeFormRow('edu-row-${idx}')"><i class="fa-solid fa-trash"></i></button>
        `;
        container.appendChild(div);
    });
}

function addEducationRow() {
    const list = document.querySelectorAll(".edu-inst");
    const count = list.length;
    const container = document.getElementById("education-list");
    const div = document.createElement("div");
    div.className = "list-row";
    div.id = `edu-row-${count}`;
    div.innerHTML = `
        <div class="form-group col-4">
            <label>Institution</label>
            <input type="text" class="edu-inst" value="" placeholder="Institution Name">
        </div>
        <div class="form-group col-3">
            <label>Degree / Major</label>
            <input type="text" class="edu-degree" value="" placeholder="Degree Details">
        </div>
        <div class="form-group col-2">
            <label>GPA / Grade</label>
            <input type="text" class="edu-gpa" value="" placeholder="GPA / Percentage">
        </div>
        <div class="form-group col-2">
            <label>Dates</label>
            <input type="text" class="edu-dates" value="" placeholder="Start - End Date">
        </div>
        <button type="button" class="btn btn-sm btn-secondary" style="margin-top:24px;" onclick="removeFormRow('edu-row-${count}')"><i class="fa-solid fa-trash"></i></button>
    `;
    container.appendChild(div);
}

function renderProjectsForm(projList) {
    const container = document.getElementById("projects-list");
    container.innerHTML = "";
    
    projList.forEach((proj, idx) => {
        const div = document.createElement("div");
        div.className = "list-row";
        div.style.flexDirection = "column";
        div.id = `proj-row-${idx}`;
        div.innerHTML = `
            <div class="form-grid" style="width:100%;">
                <div class="form-group col-4">
                    <label>Project Title</label>
                    <input type="text" class="proj-name" value="${proj.name || ''}" placeholder="Project Title">
                </div>
                <div class="form-group col-4">
                    <label>Tech Stack</label>
                    <input type="text" class="proj-stack" value="${proj.tech_stack || ''}" placeholder="React JS, Python">
                </div>
                <div class="form-group col-2">
                    <label>Live URL</label>
                    <input type="text" class="proj-link" value="${proj.link || ''}">
                </div>
                <div class="form-group col-2">
                    <label>GitHub URL</label>
                    <input type="text" class="proj-github" value="${proj.github || ''}">
                </div>
                <div class="form-group col-12 margin-top-sm">
                    <label>Bullet Points (One per line)</label>
                    <textarea class="proj-bullets" rows="4">${(proj.bullets || []).join('\n')}</textarea>
                </div>
            </div>
            <button type="button" class="btn btn-sm btn-secondary margin-top-sm" onclick="removeFormRow('proj-row-${idx}')"><i class="fa-solid fa-trash"></i> Delete Project</button>
        `;
        container.appendChild(div);
    });
}

function addProjectRow() {
    const list = document.querySelectorAll(".proj-name");
    const count = list.length;
    const container = document.getElementById("projects-list");
    const div = document.createElement("div");
    div.className = "list-row";
    div.style.flexDirection = "column";
    div.id = `proj-row-${count}`;
    div.innerHTML = `
        <div class="form-grid" style="width:100%;">
            <div class="form-group col-4">
                <label>Project Title</label>
                <input type="text" class="proj-name" value="" placeholder="Project Title">
            </div>
            <div class="form-group col-4">
                <label>Tech Stack</label>
                <input type="text" class="proj-stack" value="" placeholder="Tech Stack">
            </div>
            <div class="form-group col-2">
                <label>Live URL</label>
                <input type="text" class="proj-link" value="">
            </div>
            <div class="form-group col-2">
                <label>GitHub URL</label>
                <input type="text" class="proj-github" value="">
            </div>
            <div class="form-group col-12 margin-top-sm">
                <label>Bullet Points (One per line)</label>
                <textarea class="proj-bullets" rows="4"></textarea>
            </div>
        </div>
        <button type="button" class="btn btn-sm btn-secondary margin-top-sm" onclick="removeFormRow('proj-row-${count}')"><i class="fa-solid fa-trash"></i> Delete Project</button>
    `;
    container.appendChild(div);
}

function removeFormRow(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

async function saveProfile(event) {
    if (event) event.preventDefault();
    
    // Parse skills
    const skills = {};
    const categories = ["Languages", "Frontend", "Backend", "Cloud & Dev Tools", "AI & Data"];
    categories.forEach(cat => {
        const val = document.getElementById(`skills-${cat}`).value;
        skills[cat] = val.split(",").map(x => x.trim()).filter(Boolean);
    });
    
    // Parse Education
    const education = [];
    const eduRows = document.getElementById("education-list").children;
    for (let row of eduRows) {
        const inst = row.querySelector(".edu-inst").value;
        const degree = row.querySelector(".edu-degree").value;
        const gpa = row.querySelector(".edu-gpa").value;
        const dates = row.querySelector(".edu-dates").value;
        if (inst) {
            education.append({ institution: inst, degree, gpa, dates });
        }
    }
    
    // Parse Projects
    const projects = [];
    const projRows = document.getElementById("projects-list").children;
    for (let row of projRows) {
        const name = row.querySelector(".proj-name").value;
        const tech_stack = row.querySelector(".proj-stack").value;
        const link = row.querySelector(".proj-link").value;
        const github = row.querySelector(".proj-github").value;
        const bulletsText = row.querySelector(".proj-bullets").value;
        const bullets = bulletsText.split("\n").map(x => x.trim()).filter(Boolean);
        if (name) {
            projects.append({ name, tech_stack, link, github, bullets });
        }
    }
    
    const profilePayload = {
        name: document.getElementById("prof-name").value,
        email: document.getElementById("prof-email").value,
        phone: document.getElementById("prof-phone").value,
        github: document.getElementById("prof-github").value,
        linkedin: document.getElementById("prof-linkedin").value,
        education,
        projects,
        skills,
        achievements: currentProfile.achievements || [],
        responsibilities: currentProfile.responsibilities || []
    };
    
    try {
        const response = await fetch("/api/profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(profilePayload)
        });
        const res = await response.json();
        if (res.status === "success") {
            alert("Profile successfully saved!");
            loadProfile();
        }
    } catch (e) {
        console.error("Error saving profile details:", e);
    }
}

// 2. Jobs Feed Discovery Logic
async function searchJobs(forceRefresh = false) {
    const container = document.getElementById("jobs-container");
    const loader = document.getElementById("loading-container");
    
    container.innerHTML = "";
    loader.classList.remove("hidden");
    
    switchTab("jobs");
    
    try {
        const response = await fetch(`/api/jobs/search?refresh=${forceRefresh}`);
        const data = await response.json();
        currentJobs = data.jobs || [];
        
        loader.classList.add("hidden");
        
        if (currentJobs.length === 0) {
            container.innerHTML = `<div class="card col-12"><p>No relevant IT SDE/AI/Data jobs posted in the last 24 hours found. Please try again later.</p></div>`;
            return;
        }
        
        currentJobs.forEach(job => {
            const card = document.createElement("div");
            card.className = "job-card";
            card.onclick = () => viewJobDetails(job);
            
            // Score formatting
            const score = job.score || 50;
            let scoreClass = "low";
            if (score >= 80) scoreClass = "high";
            else if (score >= 60) scoreClass = "med";
            
            // Badge formatting
            let badgeHtml = "";
            if (job.source_type === "startup") {
                badgeHtml = `<span class="job-badge bg-orange"><i class="fa-solid fa-rocket"></i> Startup</span>`;
            } else if (job.source_type === "linkedin") {
                badgeHtml = `<a href="${job.url}" target="_blank" class="job-badge bg-blue" onclick="event.stopPropagation();"><i class="fa-brands fa-linkedin"></i> LinkedIn <i class="fa-solid fa-up-right-from-square"></i></a>`;
            } else {
                badgeHtml = `<span class="job-badge bg-green"><i class="fa-solid fa-building"></i> Company</span>`;
            }
            
            card.innerHTML = `
                <div>
                    <div class="job-card-header">
                        <div class="job-title-block">
                            <h3>${job.title}</h3>
                            <p>${job.company} • ${job.location}</p>
                        </div>
                        <div class="score-badge ${scoreClass}">${score}% Match</div>
                    </div>
                    <div class="job-badges">
                        ${badgeHtml}
                        <span class="job-badge bg-blue">${job.source}</span>
                    </div>
                    <p class="job-snippet">${job.description || 'No description available.'}</p>
                </div>
                <div class="job-card-footer">
                    <span>${job.date_posted || 'Recently added'}</span>
                    <span class="btn btn-sm btn-primary">Select & Tailor</span>
                </div>
            `;
            container.appendChild(card);
        });
        
    } catch (e) {
        loader.classList.add("hidden");
        container.innerHTML = `<div class="card col-12"><p class="error-text">An error occurred during search. Please verify Groq credentials.</p></div>`;
        console.error("Error searching jobs:", e);
    }
}

// 3. Job Tailor Hub logic
async function viewJobDetails(job) {
    selectedJob = job;
    
    // Enable the Nav link
    document.getElementById("nav-tailor-tab").classList.remove("disabled");
    switchTab("tailor");
    
    // Set Header
    document.getElementById("tailor-header-title").innerText = `Tailor Workspace: ${job.title}`;
    document.getElementById("tailor-header-subtitle").innerText = `Generating cover letter and ATS optimized resume code for ${job.company}`;
    
    // Hide editor, show loader
    document.getElementById("tailor-workspace").classList.add("hidden");
    const loader = document.getElementById("tailor-loading");
    loader.classList.remove("hidden");
    
    try {
        const response = await fetch("/api/jobs/tailor", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job: selectedJob })
        });
        const res = await response.json();
        
        loader.classList.add("hidden");
        document.getElementById("tailor-workspace").classList.remove("hidden");
        
        // Load details
        document.getElementById("work-job-title").innerText = selectedJob.title;
        document.getElementById("work-job-company").innerText = selectedJob.company;
        document.getElementById("work-match-score").innerText = `${selectedJob.score || 50}%`;
        
        // Source tags setup
        const tag = document.getElementById("work-job-source-tag");
        if (selectedJob.source_type === "startup") {
            tag.className = "job-badge bg-orange";
            tag.innerHTML = `<i class="fa-solid fa-rocket"></i> Startup`;
        } else if (selectedJob.source_type === "linkedin") {
            tag.className = "job-badge bg-blue";
            tag.innerHTML = `<a href="${selectedJob.url}" target="_blank" style="color:inherit; text-decoration:none;"><i class="fa-brands fa-linkedin"></i> LinkedIn <i class="fa-solid fa-external-link"></i></a>`;
        } else {
            tag.className = "job-badge bg-green";
            tag.innerHTML = `<i class="fa-solid fa-building"></i> Company`;
        }
        
        // Show Cover letter & Keywords
        currentCoverLetter = res.cover_letter || "";
        currentKeywords = res.keywords || [];
        currentLaTeX = res.latex_code || "";
        
        document.getElementById("work-cover-letter").value = currentCoverLetter;
        
        // Display Keywords
        const kwContainer = document.getElementById("work-keywords");
        kwContainer.innerHTML = "";
        currentKeywords.forEach(kw => {
            const span = document.createElement("span");
            span.className = "kw-tag";
            span.innerText = kw;
            kwContainer.appendChild(span);
        });
        
        // Load LaTeX in editor
        document.getElementById("raw-latex-editor").value = currentLaTeX;
        
        // Initialize Visual Form Editor panel
        loadVisualResumeFields(currentLaTeX);
        
    } catch (e) {
        loader.classList.add("hidden");
        alert("An error occurred during resume tailoring. Verify Groq connection.");
        console.error("Error tailoring materials:", e);
    }
}

// 4. Visual Resume Editor Sync logic
function loadVisualResumeFields(latexCode) {
    document.getElementById("vis-name").value = currentProfile.name || "";
    document.getElementById("vis-email").value = currentProfile.email || "";
    document.getElementById("vis-phone").value = currentProfile.phone || "";
    document.getElementById("vis-linkedin").value = currentProfile.linkedin || "";
    document.getElementById("vis-github").value = currentProfile.github || "";
    
    // Parse projects out of the LaTeX code and build a form for their bullet points
    const container = document.getElementById("vis-projects-container");
    container.innerHTML = "";
    
    currentProfile.projects.forEach((proj, idx) => {
        const div = document.createElement("div");
        div.className = "visual-project-box";
        div.style.marginTop = "20px";
        div.style.borderTop = "1px solid var(--border)";
        div.style.paddingTop = "12px";
        
        // Attempt to search tailored bullet items from LaTeX code
        let bulletText = "";
        const pattern_str = `\\\\resumeProjectHeading\\s*\\{\\s*\\\\textbf\\s*\\{\\s*\\\\large\\s*\\{\\s*${escapeRegex(proj.name)}\\s*\\}\\s*\\}\\s*\\}.*?\\\\resumeItemListStart(.*?)\\\\resumeItemListEnd`;
        const match = new RegExp(pattern_str, "s").exec(latexCode);
        
        if (match) {
            const itemsBlock = match[1];
            // Extract each item
            const itemMatches = [...itemsBlock.matchAll(/\\resumeItem\s*\{(.*?)\}/g)];
            bulletText = itemMatches.map(m => m[1].replace(/\\textbf\{(.*?)\}/g, "$1").replace(/\\&/g, "&").replace(/\\%/g, "%")).join("\n");
        } else {
            bulletText = proj.bullets.join("\n");
        }
        
        div.innerHTML = `
            <label style="color:var(--accent); font-weight:700;">Project: ${proj.name}</label>
            <div class="form-group margin-top-sm">
                <label>Tailored Description Bullets</label>
                <textarea id="vis-proj-bullets-${idx}" class="vis-proj-bullets-field" rows="4" data-proj-name="${proj.name}" oninput="syncVisualToCode()">${bulletText}</textarea>
            </div>
        `;
        container.appendChild(div);
    });
    
    // Trigger preview render
    renderPrintResumePreview();
}

function syncVisualToCode() {
    let latex = currentLaTeX;
    
    // Read details
    const name = document.getElementById("vis-name").value;
    const email = document.getElementById("vis-email").value;
    const phone = document.getElementById("vis-phone").value;
    const linkedin = document.getElementById("vis-linkedin").value;
    const github = document.getElementById("vis-github").value;
    
    // Replace Header Info
    latex = latex.replace(/\\textbf\{\\Huge\\scshape\s+(.*?)\}/i, `\\textbf{\\Huge\\scshape ${name}}`);
    latex = latex.replace(/\\href\{mailto:[^\}]+\}/i, `\\href{mailto:${email}}`);
    latex = latex.replace(/\\href\{https:\/\/www\.linkedin\.com[^\}]+\}/i, `\\href{${linkedin}}`);
    latex = latex.replace(/\\href\{https:\/\/github\.com[^\}]+\}/i, `\\href{${github}}`);
    latex = latex.replace(/\\small\s+\{\\faMobile\\enspace\s+\\textbf\{[^\}]+\}\}/i, `\\small {\\faMobile\\enspace \\textbf{${phone}}}`);
    
    // Replace visual project bullets back into LaTeX
    const bulletFields = document.querySelectorAll(".vis-proj-bullets-field");
    bulletFields.forEach(field => {
        const projName = field.getAttribute("data-proj-name");
        const bullets = field.value.split("\n").map(x => x.trim()).filter(Boolean);
        
        const latex_bullets = [];
        bullets.forEach(b => {
            let eb = b.replace(/&/g, "\\&").replace(/%/g, "\\%").replace(/\$/g, "\\$").replace(/_/g, "\\_").replace(/#/g, "\\#");
            // Bold key terms
            currentKeywords.forEach(kw => {
                const pattern = new RegExp(`\\b(${escapeRegex(kw)})\\b`, "gi");
                eb = eb.replace(pattern, "\\\\textbf{$1}");
            });
            latex_bullets.append(`            \\resumeItem{${eb}}`);
        });
        const new_bullet_block = "\n" + latex_bullets.join("\n") + "\n          ";
        
        const pattern_str = `(\\\\resumeProjectHeading\\s*\\{\\s*\\\\textbf\\s*\\{\\s*\\\\large\\s*\\{\\s*${escapeRegex(projName)}\\s*\\}\\s*\\}\\s*\\}.*?\\\\resumeItemListStart)(.*?)(\\\\resumeItemListEnd)`;
        const rx = new RegExp(pattern_str, "s");
        const match = rx.exec(latex);
        if (match) {
            latex = latex.replace(match[0], match[1] + new_bullet_block + match[3]);
        }
    });
    
    currentLaTeX = latex;
    document.getElementById("raw-latex-editor").value = latex;
    
    // Render print preview
    renderPrintResumePreview();
}

function renderPrintResumePreview() {
    const container = document.getElementById("print-resume-container");
    container.innerHTML = "";
    
    // Read current form values
    const name = document.getElementById("vis-name").value;
    const email = document.getElementById("vis-email").value;
    const phone = document.getElementById("vis-phone").value;
    const linkedin = document.getElementById("vis-linkedin").value;
    const github = document.getElementById("vis-github").value;
    
    // Build standard single-column HTML matching the LaTeX design
    let projectsHtml = "";
    currentProfile.projects.forEach((proj, idx) => {
        const bulletsText = document.getElementById(`vis-proj-bullets-${idx}`)?.value || "";
        const bullets = bulletsText.split("\n").map(x => x.trim()).filter(Boolean);
        
        let listItems = "";
        bullets.forEach(b => {
            // Apply bold formatting to matched keywords in preview
            let text = b;
            currentKeywords.forEach(kw => {
                const pattern = new RegExp(`\\b(${escapeRegex(kw)})\\b`, "gi");
                text = text.replace(pattern, "<strong>$1</strong>");
            });
            listItems += `<li>${text}</li>`;
        });
        
        projectsHtml += `
            <div style="margin-top: 10px;">
                <div class="print-row">
                    <strong>${proj.name}</strong>
                    <span>${proj.tech_stack}</span>
                </div>
                <ul class="print-bullets">
                    ${listItems}
                </ul>
            </div>
        `;
    });
    
    let skillsHtml = "";
    for (let cat in currentProfile.skills) {
        skillsHtml += `
            <div class="print-skills-item">
                <strong>${cat}:</strong> ${currentProfile.skills[cat].join(", ")}
            </div>
        `;
    }
    
    let eduHtml = "";
    currentProfile.education.forEach(edu => {
        eduHtml += `
            <div style="margin-top: 5px;">
                <div class="print-row">
                    <strong>${edu.institution}</strong>
                    <span>${edu.location}</span>
                </div>
                <div class="print-row">
                    <em>${edu.degree} -- <strong>${edu.gpa}</strong></em>
                    <span>${edu.dates}</span>
                </div>
            </div>
        `;
    });

    let achievementsHtml = "";
    currentProfile.achievements.forEach(ach => {
        achievementsHtml += `
            <div style="margin-top: 5px;">
                <div class="print-row">
                    <strong>${ach.title}</strong>
                    <span>${ach.organization}</span>
                </div>
                <ul class="print-bullets">
                    ${ach.bullets.map(b => `<li>${b}</li>`).join("")}
                </ul>
            </div>
        `;
    });
    
    container.innerHTML = `
        <div class="print-resume">
            <div class="print-header">
                <div class="print-name">${name}</div>
                <div class="print-contacts">
                    Email: ${email} | Phone: ${phone} | GitHub: ${github} | LinkedIn: ${linkedin}
                </div>
            </div>
            
            <div class="print-section">
                <div class="print-section-title">Education</div>
                ${eduHtml}
            </div>
            
            <div class="print-section">
                <div class="print-section-title">Projects</div>
                ${projectsHtml}
            </div>
            
            <div class="print-section">
                <div class="print-section-title">Technical Skills</div>
                ${skillsHtml}
            </div>
            
            <div class="print-section">
                <div class="print-section-title">Achievements</div>
                ${achievementsHtml}
            </div>
        </div>
    `;
}

// 5. Exporter triggers
function downloadTexFile() {
    const text = document.getElementById("raw-latex-editor").value;
    const blob = new Blob([text], { type: "text/plain" });
    const a = document.createElement("a");
    a.download = `${currentProfile.name.replace(/\s+/g, '_')}_Resume.tex`;
    a.href = URL.createObjectURL(blob);
    a.click();
}

function printResume() {
    // Standard browser print will print page using the CSS print media query
    window.print();
}

// Utilities
function copyToClipboard(id) {
    const text = document.getElementById(id).value;
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
}

function escapeRegex(string) {
    return string.replace(/[/\-\\^$*+?.()|[\]{}]/g, '\\$&');
}

function escapeRegex(string) {
    return string.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
}
