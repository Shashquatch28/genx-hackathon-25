// Config
const baseURL = "http://127.0.0.1:8000/api";

const endpoints = {
  upload: "/upload",   
  chat:   "/chat"
};


// Helpers
const $ = (q)=>document.querySelector(q);
const $$ = (q)=>document.querySelectorAll(q);

const setText = (el, text="") => { el.textContent = text ?? ""; };
const setHTMLSafe = (el, text="") => { el.textContent = text ?? ""; }; // prevent injection

function setLoading(btn, isLoading, textIdle="Upload & Analyze", textBusy="Analyzing…"){
  btn.disabled = !!isLoading;
  btn.textContent = isLoading ? textBusy : textIdle;
}

function scrollToHash(hash){
  const target = document.querySelector(hash);
  if(!target) return;
  const top = target.getBoundingClientRect().top + window.scrollY - 70;
  window.scrollTo({ top, behavior: "smooth" });
}


// Navigation behavior
const navToggle = $("#navToggle");
const navLinks = $("#navLinks");
navToggle?.addEventListener("click", ()=> navLinks.classList.toggle("open"));
navLinks?.addEventListener("click", (e)=>{
  if(e.target.matches("a")) navLinks.classList.remove("open");
});

$$(".nav-link").forEach(a=>{
  a.addEventListener("click", (e)=>{
    e.preventDefault();
    const href = a.getAttribute("href");
    if(href?.startsWith("#")) scrollToHash(href);
  });
});

// Highlight active section
const sections = ["#home","#analyze","#results","#timeline","#risks","#about"].map(id=>document.querySelector(id));
const navMap = {};
$$(".nav-link").forEach(a=> navMap[a.getAttribute("href")] = a);

const io = new IntersectionObserver((entries)=>{
  entries.forEach(entry=>{
    if(entry.isIntersecting){
      const id = `#${entry.target.id}`;
      $$(".nav-link").forEach(n=>n.classList.remove("active"));
      navMap[id]?.classList.add("active");
    }
  });
},{ rootMargin: "-40% 0px -55% 0px", threshold: 0.01 });
sections.forEach(s=> s && io.observe(s));

// Sticky navbar subtle effect
const navbar = $("#navbar");
let lastY = window.scrollY;
document.addEventListener("scroll", ()=>{
  const y = window.scrollY;
  navbar.style.boxShadow = y>10 ? "0 8px 30px rgba(0,0,0,.25)" : "none";
  lastY = y;
});


// Tabs
$$(".tab-btn").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    $$(".tab-btn").forEach(b=>b.classList.remove("active"));
    $$(".tab-content").forEach(c=>c.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});


// Upload + Analyze
const uploadBtn = $("#uploadBtn");
const fileInput = $("#fileInput");
const uploadStatus = $("#uploadStatus");
const fileBadge = $("#fileBadge");

let LAST_RESULT = null;   // keep recent analysis to share with chatbot
let LAST_FILE_ID = null;  // if backend returns some id

uploadBtn?.addEventListener("click", async ()=>{
  const file = fileInput.files?.[0];
  if(!file){ alert("Please choose a file first."); return; }

  const formData = new FormData();
  formData.append("file", file);

  setLoading(uploadBtn, true);
  setText(uploadStatus, `Uploading ${file.name}…`);
  try{
    const res = await fetch(baseURL + endpoints.upload, { method: "POST", body: formData });
    if(!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();

    LAST_RESULT = data;
    LAST_FILE_ID = data.file_id ?? null;

    $("#simple").textContent  = data.simplified || "No simplified output.";
    $("#advanced").textContent = data.advanced || "No advanced output.";

    const tList = $("#timelineList"); tList.innerHTML = "";
    (data.timeline || []).forEach(ev=>{
      const li = document.createElement("li");
      li.textContent = `${ev.date ?? "—"} • ${ev.event ?? ""}`;
      tList.appendChild(li);
    });

    const rList = $("#riskList"); rList.innerHTML = "";
    (data.risks || []).forEach(risk=>{
      const li = document.createElement("li");
      li.textContent = risk;
      rList.appendChild(li);
    });

    // UI niceties
    fileBadge.hidden = false;
    fileBadge.textContent = file.name;
    setText(uploadStatus, "Done. Jump to Results ↓");
    scrollToHash("#results");
  } catch(err){
    console.error(err);
    setText(uploadStatus, "Upload failed. Check console & CORS settings on backend.");
    alert("Upload failed. Ensure FastAPI allows CORS for your frontend origin.");
  } finally{
    setLoading(uploadBtn, false);
  }
});

// Quick question (sends text to chatbot endpoint too)
$("#askBtn")?.addEventListener("click", ()=>{
  const q = $("#quickQuestion").value.trim();
  if(!q) return;
  openChat();
  enqueueUserMessage(q);
  sendChat(q);
});


// Chatbot
const chatToggle = $("#chatToggle");
const chatPanel  = $("#chatPanel");
const chatClose  = $("#chatClose");
const chatForm   = $("#chatForm");
const chatInput  = $("#chatText");
const chatMsgs   = $("#chatMessages");

function openChat(){ chatPanel.classList.add("open"); chatInput?.focus(); }
function closeChat(){ chatPanel.classList.remove("open"); }
chatToggle?.addEventListener("click", openChat);
chatClose?.addEventListener("click", closeChat);

function appendMsg(role, text, extraClass=""){
  const div = document.createElement("div");
  div.className = `msg ${role} ${extraClass}`.trim();
  div.textContent = text;
  chatMsgs.appendChild(div);
  chatMsgs.scrollTop = chatMsgs.scrollHeight;
  return div;
}

function enqueueUserMessage(text){
  return appendMsg("user", text);
}

function enqueueBotThinking(){
  return appendMsg("bot", "Thinking…", "thinking");
}

chatForm?.addEventListener("submit", (e)=>{
  e.preventDefault();
  const text = chatInput.value.trim();
  if(!text) return;
  enqueueUserMessage(text);
  chatInput.value = "";
  sendChat(text);
});

async function sendChat(message){
  const thinking = enqueueBotThinking();
  try{
    const payload = {
      message,
      file_id: LAST_FILE_ID,
      context: {
        simplified: LAST_RESULT?.simplified ?? null,
        advanced: LAST_RESULT?.advanced ?? null,
        timeline: LAST_RESULT?.timeline ?? null,
        risks: LAST_RESULT?.risks ?? null
      }
    };

    const res = await fetch(baseURL + endpoints.chat, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    // If your backend streams (text/event-stream), handle it here
    const ctype = res.headers.get("content-type") || "";
    if(ctype.includes("text/event-stream")){
      // Stream tokens line-by-line
      thinking.textContent = "";
      thinking.classList.remove("thinking");
      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      while(true){
        const { value, done } = await reader.read();
        if(done) break;
        thinking.textContent += decoder.decode(value, { stream:true });
        chatMsgs.scrollTop = chatMsgs.scrollHeight;
      }
    } else {
      if(!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      const reply = data.reply || data.answer || JSON.stringify(data, null, 2);
      thinking.textContent = reply;
      thinking.classList.remove("thinking");
    }
  } catch(err){
    console.error(err);
    thinking.textContent = "I couldn't reach the chat endpoint. Check that your backend is running and CORS is enabled.";
    thinking.classList.remove("thinking");
  }
}

// Open chat if user presses "?" anywhere
document.addEventListener("keydown",(e)=>{
  if(e.key === "/" && !e.metaKey && !e.ctrlKey){
    e.preventDefault(); openChat();
  }
});
