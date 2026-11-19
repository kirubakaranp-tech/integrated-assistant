const API_URL = "http://127.0.0.1:8000";

let sessionId = crypto.randomUUID();

const messagesBox = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const fileInput = document.getElementById("file-input");
const notice = document.getElementById("notice");
const documentList = document.getElementById("document-list");
const toneSelect = document.getElementById("tone-select");
const draftButton = document.getElementById("draft-button");
const draftOutput = document.getElementById("draft-output");
const copyButton = document.getElementById("copy-button");

async function callApi(path, options) {
    let response;
    try {
        response = await fetch(API_URL + path, options);
    } catch (error) {
        throw new Error("Can't reach the server. Is the backend running (uvicorn app.main:app)?");
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const error = new Error(friendlyError(response.status, data));
        error.status = response.status;
        throw error;
    }
    return data;
}

function friendlyError(status, data) {
    const detail = typeof data.detail === "string" ? data.detail : "";
    if (status === 400) return "That file is empty.";
    if (status === 404) return detail || "Not found.";
    if (status === 413) return "That file is too big (the limit is 20 MB).";
    if (status === 415) return "Only PDF (.pdf) and Word (.docx) files can be uploaded.";
    if (status === 422) return detail || "Please check what you typed and try again.";
    if (status === 502 || status === 503) return "The AI service is not available right now. " + detail;
    return "Something went wrong (error " + status + "). Please try again.";
}

function showNotice(text, type) {
    notice.textContent = text;
    notice.className = "notice " + type;
}

function hideNotice() {
    notice.className = "notice hidden";
}

function scrollToBottom() {
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

function addMessage(text, type) {
    const emptyText = messagesBox.querySelector(".empty");
    if (emptyText) emptyText.remove();

    const bubble = document.createElement("div");
    bubble.className = "message " + type;
    bubble.textContent = text;
    messagesBox.appendChild(bubble);
    scrollToBottom();
    return bubble;
}

function addLoading() {
    const bubble = addMessage("", "assistant loading");
    bubble.innerHTML = "Thinking<span>.</span><span>.</span><span>.</span>";
    return bubble;
}

function sourceLabel(source) {
    return source.page ? `${source.file} (page ${source.page})` : source.file;
}

function addAnswer(data) {
    const bubble = addMessage(data.answer, "assistant");

    if (data.sources.length > 0) {
        const sources = document.createElement("div");
        sources.className = "sources";
        sources.textContent = "Sources: " + data.sources.map(sourceLabel).join(", ");
        bubble.appendChild(sources);
    }

    const panel = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "How I got this";
    panel.appendChild(summary);

    const steps = document.createElement("ul");
    for (const tool of data.tools_used) {
        const code = document.createElement("code");
        code.textContent = tool;
        const step = document.createElement("li");
        step.append("Called the tool ", code);
        steps.appendChild(step);
    }
    if (data.tools_used.length === 0) {
        const step = document.createElement("li");
        step.textContent = data.sources.length > 0
            ? "Searched the uploaded documents and answered from the matching parts."
            : "Found nothing about this in the documents or the tools.";
        steps.appendChild(step);
    }
    panel.appendChild(steps);
    bubble.appendChild(panel);
    scrollToBottom();
}

async function sendMessage(event) {
    event.preventDefault();
    const message = messageInput.value.trim();
    if (!message || sendButton.disabled) return;

    hideNotice();
    addMessage(message, "user");
    messageInput.value = "";
    sendButton.disabled = true;
    const loading = addLoading();

    try {
        const data = await callApi("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message, session_id: sessionId }),
        });
        loading.remove();
        addAnswer(data);
    } catch (error) {
        loading.remove();
        addMessage(error.message, "error");
    } finally {
        sendButton.disabled = false;
        messageInput.focus();
    }
}

chatForm.addEventListener("submit", sendMessage);

messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});

document.getElementById("new-chat-button").addEventListener("click", () => {
    sessionId = crypto.randomUUID();
    messagesBox.innerHTML = '<p class="empty">New chat started. Ask me anything.</p>';
    draftOutput.value = "";
    copyButton.disabled = true;
});

async function uploadFile() {
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    showNotice(`Uploading ${file.name}... (the first upload can take a minute)`, "info");

    try {
        const data = await callApi("/documents", { method: "POST", body: formData });
        showNotice(`Uploaded ${file.name}: ${data.chunks} chunks saved.`, "success");
        loadDocuments();
    } catch (error) {
        showNotice(`Could not upload ${file.name}: ${error.message}`, "error");
    } finally {
        fileInput.value = "";
    }
}

fileInput.addEventListener("change", uploadFile);

async function loadDocuments() {
    try {
        const documents = await callApi("/documents");
        documentList.innerHTML = "";
        if (documents.length === 0) {
            documentList.innerHTML = '<li class="muted">No documents yet</li>';
        }
        for (const doc of documents) {
            const item = document.createElement("li");
            item.textContent = doc.name;
            documentList.appendChild(item);
        }
    } catch (error) {
        showNotice(error.message, "error");
    }
}

async function draftEmail() {
    draftButton.disabled = true;
    draftButton.textContent = "Drafting...";
    draftOutput.value = "";

    try {
        const draft = await callApi("/draft-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, tone: toneSelect.value }),
        });
        draftOutput.value = `Subject: ${draft.subject}\n\n${draft.body}`;
        copyButton.disabled = false;
        hideNotice();
    } catch (error) {
        showNotice(error.status === 404 ? "Ask a question first, then draft the email." : error.message, "error");
    } finally {
        draftButton.disabled = false;
        draftButton.textContent = "Draft email";
    }
}

draftButton.addEventListener("click", draftEmail);

copyButton.addEventListener("click", async () => {
    await navigator.clipboard.writeText(draftOutput.value);
    copyButton.textContent = "Copied!";
    setTimeout(() => (copyButton.textContent = "Copy draft"), 1500);
});

loadDocuments();
