
const API_URL = "https://documind-ai-ey5s.onrender.com";

// PDF upload elements
const pdfInput = document.getElementById("pdfInput");
const chooseFileBtn = document.getElementById("chooseFileBtn");
const uploadBtn = document.getElementById("uploadBtn");
const fileName = document.getElementById("fileName");
const uploadStatus = document.getElementById("uploadStatus");

// Chat elements
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const chatMessages = document.getElementById("chatMessages");
const chatStatus = document.getElementById("chatStatus");
const chatError = document.getElementById("chatError");

let selectedFile = null;
let isDocumentUploaded = false;
let isChatting = false;

// Show a status message
function showStatus(element, message, type = "") {
    element.textContent = message;
    element.className = "status-message";

    if (type) {
        element.classList.add(type);
    }
}

// Open the file selector
chooseFileBtn.addEventListener("click", () => {
    pdfInput.click();
});

// Handle PDF selection
pdfInput.addEventListener("change", () => {
    selectedFile = pdfInput.files[0] || null;

    isDocumentUploaded = false;
    questionInput.disabled = true;
    sendBtn.disabled = true;

    if (!selectedFile) {
        fileName.textContent = "No file selected";
        uploadBtn.disabled = true;
        return;
    }

    if (
        !selectedFile.name.toLowerCase().endsWith(".pdf") ||
        selectedFile.type !== "application/pdf"
    ) {
        selectedFile = null;
        pdfInput.value = "";
        fileName.textContent = "No file selected";
        uploadBtn.disabled = true;

        showStatus(
            uploadStatus,
            "Please select a valid PDF file.",
            "error"
        );
        return;
    }

    fileName.textContent = selectedFile.name;
    uploadBtn.disabled = false;

    showStatus(uploadStatus, "");
    showStatus(chatError, "");
    chatStatus.textContent = "Ready to process your PDF";
});

// Upload the PDF
uploadBtn.addEventListener("click", async () => {
    if (!selectedFile) {
        showStatus(uploadStatus, "Please choose a PDF first.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    uploadBtn.disabled = true;
    chooseFileBtn.disabled = true;

    showStatus(
        uploadStatus,
        "Uploading and processing your PDF. This may take a moment..."
    );

    chatStatus.textContent = "Processing document...";

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "PDF upload failed.");
        }

        isDocumentUploaded = true;

        showStatus(
            uploadStatus,
            `${data.filename} processed successfully! ${data.total_chunks} text chunks created.`,
            "success"
        );

        chatStatus.textContent = `Document ready: ${data.filename}`;

        questionInput.disabled = false;
        sendBtn.disabled = false;

        addMessage(
            "assistant",
            `I've processed "${data.filename}". You can now ask me questions about its contents.`
        );

    } catch (error) {
        showStatus(
            uploadStatus,
            error.message || "Unable to connect to the backend.",
            "error"
        );

        chatStatus.textContent = "Upload failed";

    } finally {
        uploadBtn.disabled = !selectedFile;
        chooseFileBtn.disabled = false;
    }
});

// Add a message to the chat window
function addMessage(role, text, sources = []) {
    const messageDiv = document.createElement("div");

    messageDiv.classList.add("message");

    if (role === "user") {
        messageDiv.classList.add("user-message");
    } else {
        messageDiv.classList.add("assistant-message");
    }

    const label = document.createElement("div");
    label.classList.add("message-label");
    label.textContent = role === "user" ? "You" : "DocuMind AI";

    const messageText = document.createElement("p");
    messageText.textContent = text;

    messageDiv.appendChild(label);
    messageDiv.appendChild(messageText);

    // Display retrieved PDF passages
    if (sources.length > 0) {
        const sourceHeading = document.createElement("p");
        sourceHeading.textContent = "Relevant PDF passages:";
        sourceHeading.style.marginTop = "12px";
        sourceHeading.style.fontWeight = "bold";

        messageDiv.appendChild(sourceHeading);

        sources.forEach((source, index) => {
            const sourceText = document.createElement("p");

            sourceText.style.marginTop = "8px";
            sourceText.style.fontSize = "12px";
            sourceText.style.whiteSpace = "pre-wrap";

            sourceText.textContent =
                `${index + 1}. ${source.text}`;

            messageDiv.appendChild(sourceText);
        });
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send a question to the backend
chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question || !isDocumentUploaded || isChatting) {
        return;
    }

    addMessage("user", question);

    questionInput.value = "";
    isChatting = true;
    questionInput.disabled = true;
    sendBtn.disabled = true;

    showStatus(chatError, "");
    chatStatus.textContent = "Thinking...";

    const loadingMessage = document.createElement("div");
    loadingMessage.classList.add("message", "assistant-message");
    loadingMessage.textContent = "Searching your document and generating an answer...";
    loadingMessage.id = "loadingMessage";

    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to answer your question.");
        }

        addMessage(
            "assistant",
            data.answer,
            data.sources || []
        );

        chatStatus.textContent = "Ready for your next question";

    } catch (error) {
        showStatus(
            chatError,
            error.message || "Unable to connect to the backend.",
            "error"
        );

        chatStatus.textContent = "Something went wrong";

    } finally {
        const loadingElement = document.getElementById("loadingMessage");

        if (loadingElement) {
            loadingElement.remove();
        }

        isChatting = false;

        questionInput.disabled = !isDocumentUploaded;
        sendBtn.disabled = !isDocumentUploaded;

        questionInput.focus();
    }
});
