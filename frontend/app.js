// // === Adjust backend URL if needed ===
// const BASE_URL = "http://localhost:8000/api";

// // File Upload Form
// document.getElementById("uploadForm").addEventListener("submit", async function(e) {
//   e.preventDefault();

//   const fileInput = document.getElementById("fileInput");
//   if (!fileInput.files.length) {
//     alert("Please select a file first!");
//     return;
//   }

//   const file = fileInput.files[0];
//   const formData = new FormData();
//   formData.append("file", file);

//   document.getElementById("status").innerText = "Processing...";

//   try {
//     const response = await fetch(`${BASE_URL}/upload`, {
//       method: "POST",
//       body: formData
//     });

//     if (!response.ok) throw new Error(`Upload failed: ${response.statusText}`);

//     const data = await response.json();
//     document.getElementById("status").innerText =
//       `File processed: ${data.filename}`;

//     // Render clauses
//     const clausesDiv = document.getElementById("clauses");
//     clausesDiv.innerHTML = "";
//     (data.clauses || []).forEach(c => {
//       const p = document.createElement("p");
//       p.innerText = `Clause ${c.id}: ${c.text}`;
//       clausesDiv.appendChild(p);
//     });

//     // Render risks
//     const risksDiv = document.getElementById("risks");
//     risksDiv.innerHTML = "";
//     (data.risks || []).forEach(r => {
//       const p = document.createElement("p");
//       p.innerText = `- ${r}`;
//       risksDiv.appendChild(p);
//     });

//     // Render timeline
//     const timelineDiv = document.getElementById("timeline");
//     timelineDiv.innerHTML = "";
//     (data.timeline || []).forEach(t => {
//       const p = document.createElement("p");
//       p.innerText = `${t.date}: ${t.event}`;
//       timelineDiv.appendChild(p);
//     });

//   } catch (err) {
//     document.getElementById("status").innerText = "Error: " + err.message;
//   }
// });

// // Chatbox for What-if questions
// document.getElementById("chatSend").addEventListener("click", async function() {
//   const input = document.getElementById("chatInput").value;
//   if (!input.trim()) return;

//   const chatOutput = document.getElementById("chatOutput");
//   chatOutput.innerHTML += `<p><b>You:</b> ${input}</p>`;

//   try {
//     const response = await fetch(`${BASE_URL}/chat`, {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ question: input })
//     });

//     if (!response.ok) throw new Error(`Chat failed: ${response.statusText}`);

//     const data = await response.json();
//     chatOutput.innerHTML += `<p><b>AI:</b> ${data.answer}</p>`;

//   } catch (err) {
//     chatOutput.innerHTML += `<p><b>Error:</b> ${err.message}</p>`;
//   }

//   document.getElementById("chatInput").value = "";
// });




// document.getElementById("uploadForm").addEventListener("submit", async function (event) {
//   event.preventDefault();

//   const fileInput = document.getElementById("fileInput");
//   const responseBox = document.getElementById("responseBox");

//   if (fileInput.files.length === 0) {
//     responseBox.textContent = "Please select a file first.";
//     return;
//   }

//   const formData = new FormData();
//   formData.append("file", fileInput.files[0]);

//   responseBox.textContent = "Uploading...";

//   try {
//     const response = await fetch("http://127.0.0.1:8000/upload", {
//       method: "POST",
//       body: formData,
//     });

//     if (!response.ok) {
//       const errorData = await response.json();
//       throw new Error(errorData.detail || "Upload failed");
//     }

//     const result = await response.json();
//     responseBox.textContent = JSON.stringify(result, null, 2);
//   } catch (error) {
//     responseBox.textContent = "Error: " + error.message;
//   }
// });


// document.getElementById("uploadForm").addEventListener("submit", async function (event) {
//   event.preventDefault();

//   const fileInput = document.getElementById("fileInput");
//   const responseBox = document.getElementById("responseBox");

//   if (fileInput.files.length === 0) {
//     responseBox.textContent = "Please select a file first.";
//     return;
//   }

//   const formData = new FormData();
//   formData.append("file", fileInput.files[0]);

//   responseBox.textContent = "Uploading...";

//   // Auto-detect backend (use current origin if possible, otherwise fallback to localhost:8000)
//   let backendUrl;
//   if (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
//     backendUrl = "http://127.0.0.1:8000"; // local dev backend
//   } else {
//     backendUrl = window.location.origin; // same domain as frontend when deployed
//   }

//   try {
//     const response = await fetch(`${backendUrl}/upload`, {
//       method: "POST",
//       body: formData,
//     });

//     if (!response.ok) {
//       const errorData = await response.json();
//       throw new Error(errorData.detail || "Upload failed");
//     }

//     const result = await response.json();
//     responseBox.textContent = JSON.stringify(result, null, 2);
//   } catch (error) {
//     responseBox.textContent = "Error: " + error.message;
//   }
// });
