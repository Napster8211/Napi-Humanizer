/**
 * NapsterTec Text Intelligence Engine - Frontend Workspace Controller
 * Enforces safe DOM updates using textContent and property setters.
 * No user input or API output is ever injected via direct HTML assignment.
 * Features: SSE Streaming, Selection-Based Editing, Opt-in Local History, Style Profiles.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const originalText = document.getElementById("originalText");
    const revisedText = document.getElementById("revisedText");
    const originalCounts = document.getElementById("originalCounts");
    const revisedCounts = document.getElementById("revisedCounts");
    const detectedLangBadge = document.getElementById("detectedLangBadge");

    const modeSelect = document.getElementById("modeSelect");
    const intensitySelect = document.getElementById("intensitySelect");
    const toneInput = document.getElementById("toneInput");
    const audienceInput = document.getElementById("audienceInput");
    const customInstructions = document.getElementById("customInstructions");
    const streamCheckbox = document.getElementById("streamCheckbox");
    const fallbackCheckbox = document.getElementById("fallbackCheckbox");

    const refineBtn = document.getElementById("refineBtn");
    const refineBtnSpinner = document.getElementById("refineBtnSpinner");
    const refineBtnText = document.getElementById("refineBtnText");
    const cancelBtn = document.getElementById("cancelBtn");
    const analyzeBtn = document.getElementById("analyzeBtn");

    const sampleBtn = document.getElementById("sampleBtn");
    const clearBtn = document.getElementById("clearBtn");
    const documentFile = document.getElementById("documentFile");
    const uploadStatus = document.getElementById("uploadStatus");
    const copyBtn = document.getElementById("copyBtn");
    const exportTxtBtn = document.getElementById("exportTxtBtn");
    const exportMdBtn = document.getElementById("exportMdBtn");

    const alertBox = document.getElementById("alertBox");
    const alertMessage = document.getElementById("alertMessage");
    const alertIcon = document.getElementById("alertIcon");
    const alertCloseBtn = document.getElementById("alertCloseBtn");

    const selectionBanner = document.getElementById("selectionBanner");
    const selectionLength = document.getElementById("selectionLength");
    const clearSelectionBtn = document.getElementById("clearSelectionBtn");

    const warningsBox = document.getElementById("warningsBox");
    const warningsList = document.getElementById("warningsList");

    const valReadingEase = document.getElementById("valReadingEase");
    const valGradeLevel = document.getElementById("valGradeLevel");
    const valDiversity = document.getElementById("valDiversity");
    const valReadingTime = document.getElementById("valReadingTime");
    const valWordDelta = document.getElementById("valWordDelta");
    const valWordDeltaDetail = document.getElementById("valWordDeltaDetail");

    const changeSummaryBox = document.getElementById("changeSummaryBox");
    const changeSummaryList = document.getElementById("changeSummaryList");
    const envStatusText = document.getElementById("envStatusText");

    // Modals
    const styleProfileBtn = document.getElementById("styleProfileBtn");
    const styleModal = document.getElementById("styleModal");
    const closeStyleModalBtn = document.getElementById("closeStyleModalBtn");
    const saveProfileBtn = document.getElementById("saveProfileBtn");
    const clearProfileBtn = document.getElementById("clearProfileBtn");
    const profileTone = document.getElementById("profileTone");
    const profileAudience = document.getElementById("profileAudience");
    const profileForbidden = document.getElementById("profileForbidden");
    const profileGuidelines = document.getElementById("profileGuidelines");

    const historyModalBtn = document.getElementById("historyModalBtn");
    const historyModal = document.getElementById("historyModal");
    const closeHistoryModalBtn = document.getElementById("closeHistoryModalBtn");
    const closeHistoryBtn = document.getElementById("closeHistoryBtn");
    const clearHistoryBtn = document.getElementById("clearHistoryBtn");
    const historyOptInCheckbox = document.getElementById("historyOptInCheckbox");
    const historyList = document.getElementById("historyList");
    const historyCount = document.getElementById("historyCount");

    const toolTabs = document.querySelectorAll(".tool-tab");
    const pageTitle = document.getElementById("pageTitle");
    const pageDescription = document.getElementById("pageDescription");
    const actionHelper = document.getElementById("actionHelper");
    const actionSubcopy = document.getElementById("actionSubcopy");
    const insightsTitle = document.getElementById("insightsTitle");
    const insightsDisclaimer = document.getElementById("insightsDisclaimer");
    const detectorNotice = document.getElementById("detectorNotice");
    const detectorResult = document.getElementById("detectorResult");
    const detectorPercent = document.getElementById("detectorPercent");
    const detectorStatus = document.getElementById("detectorStatus");
    const detectorMethod = document.getElementById("detectorMethod");
    const detectorHighlights = document.getElementById("detectorHighlights");

    const toolDefinitions = {
        humanize: {
            title: "Make your draft clearer.",
            description: "Polish wording, improve flow, and keep your meaning intact.",
            action: "Humanize text",
            helper: "Ready when you are.",
            subcopy: "Your text is processed with your selected tool.",
            mode: "natural",
            analyze: false,
            insights: "Writing signals",
        },
        detector: {
            title: "Understand your writing patterns.",
            description: "Review sentence-level AI-likeness signals without treating them as an authorship verdict.",
            action: "Analyze writing",
            helper: "Signals help you decide what to review.",
            subcopy: "The percentage is an estimate, not proof of authorship.",
            mode: "proofread",
            analyze: true,
            insights: "Descriptive writing signals",
        },
        grammar: {
            title: "Tidy up grammar and mechanics.",
            description: "Correct spelling, punctuation, and grammar while keeping your voice.",
            action: "Check grammar",
            helper: "Keep your voice. Fix the details.",
            subcopy: "Review the suggested result before using it.",
            mode: "proofread",
            analyze: false,
            insights: "Grammar check insights",
        },
        summarizer: {
            title: "Find the essential point.",
            description: "Reduce repetition and extra wording while preserving the important details.",
            action: "Summarize text",
            helper: "Shorter does not have to mean vague.",
            subcopy: "Use the advanced settings if you want more or less compression.",
            mode: "concise",
            analyze: false,
            insights: "Summary insights",
        },
        tone: {
            title: "Choose the right tone.",
            description: "Shape the same message for a professional, conversational, academic, or custom audience.",
            action: "Change tone",
            helper: "Same meaning. A better fit for the moment.",
            subcopy: "Add a preferred tone or audience under fine-tune settings.",
            mode: "professional",
            analyze: false,
            insights: "Tone change insights",
        },
        readability: {
            title: "See how your draft reads.",
            description: "Get quick readability and structure signals before you revise.",
            action: "Analyze writing",
            helper: "A useful snapshot before the next edit.",
            subcopy: "These metrics describe the text; they do not judge the author.",
            mode: "proofread",
            analyze: true,
            insights: "Readability insights",
        },
    };
    let activeTool = "humanize";

    let abortController = null;
    let activeSelectionRange = null;

    function setActiveTool(toolId) {
        const definition = toolDefinitions[toolId] || toolDefinitions.humanize;
        activeTool = toolDefinitions[toolId] ? toolId : "humanize";
        toolTabs.forEach((tab) => {
            const selected = tab.dataset.tool === activeTool;
            tab.classList.toggle("active", selected);
            tab.setAttribute("aria-selected", selected ? "true" : "false");
        });
        pageTitle.textContent = definition.title;
        pageDescription.textContent = definition.description;
        actionHelper.textContent = definition.helper;
        actionSubcopy.textContent = definition.subcopy;
        refineBtnText.textContent = definition.action;
        analyzeBtn.classList.toggle("hidden", !definition.analyze);
        refineBtn.classList.toggle("hidden", definition.analyze);
        insightsTitle.textContent = definition.insights;
        detectorNotice.classList.toggle("hidden", activeTool !== "detector");
        insightsDisclaimer.textContent = activeTool === "detector"
            ? "Estimated linguistic signal only. It is not proof of AI authorship."
            : "Descriptive indicators only. They do not estimate AI authorship.";
        if (modeSelect && definition.mode) modeSelect.value = definition.mode;
    }

    toolTabs.forEach((tab) => tab.addEventListener("click", () => setActiveTool(tab.dataset.tool)));
    setActiveTool("humanize");

    // Load persisted Style Profile
    function loadSavedStyleProfile() {
        try {
            const raw = localStorage.getItem("napstertec_style_profile");
            if (raw) {
                const data = JSON.parse(raw);
                profileTone.value = data.preferred_tone || "";
                profileAudience.value = data.target_audience || "";
                profileForbidden.value = (data.forbidden_words || []).join(", ");
                profileGuidelines.value = data.custom_guidelines || "";
            }
        } catch (e) {}
    }

    function getActiveStyleProfile() {
        const tone = profileTone.value.trim();
        const aud = profileAudience.value.trim();
        const forbidden = profileForbidden.value.split(",").map(s => s.trim()).filter(Boolean);
        const guidelines = profileGuidelines.value.trim();

        if (!tone && !aud && forbidden.length === 0 && !guidelines) {
            return null;
        }

        return {
            name: "UserCustom",
            preferred_tone: tone || null,
            target_audience: aud || null,
            forbidden_words: forbidden,
            custom_guidelines: guidelines || null,
        };
    }

    loadSavedStyleProfile();

    saveProfileBtn.addEventListener("click", () => {
        const prof = getActiveStyleProfile();
        if (prof) {
            localStorage.setItem("napstertec_style_profile", JSON.stringify(prof));
            showAlert("Style profile saved successfully.", false);
        } else {
            localStorage.removeItem("napstertec_style_profile");
            showAlert("Style profile reset.", false);
        }
        styleModal.classList.add("hidden");
    });

    clearProfileBtn.addEventListener("click", () => {
        profileTone.value = "";
        profileAudience.value = "";
        profileForbidden.value = "";
        profileGuidelines.value = "";
        localStorage.removeItem("napstertec_style_profile");
        showAlert("Style profile cleared.", false);
    });

    styleProfileBtn.addEventListener("click", () => styleModal.classList.remove("hidden"));
    closeStyleModalBtn.addEventListener("click", () => styleModal.classList.add("hidden"));

    // Session History Management (Zero-storage by default)
    function loadHistory() {
        const isOptedIn = localStorage.getItem("napstertec_history_optin") === "true";
        historyOptInCheckbox.checked = isOptedIn;

        if (!isOptedIn) {
            historyCount.textContent = "0";
            return [];
        }

        try {
            const raw = localStorage.getItem("napstertec_session_history");
            const items = raw ? JSON.parse(raw) : [];
            historyCount.textContent = items.length.toString();
            return items;
        } catch (e) {
            return [];
        }
    }

    function saveHistoryItem(item) {
        if (!historyOptInCheckbox.checked) return;
        const items = loadHistory();
        items.unshift({
            id: item.request_id || Date.now().toString(),
            timestamp: new Date().toLocaleTimeString(),
            mode: item.mode,
            original: item.original_text,
            revised: item.revised_text,
        });
        // Retain max 10 recent revisions
        if (items.length > 10) items.pop();
        localStorage.setItem("napstertec_session_history", JSON.stringify(items));
        historyCount.textContent = items.length.toString();
    }

    function renderHistoryUI() {
        const items = loadHistory();
        historyList.replaceChildren();

        if (items.length === 0) {
            const p = document.createElement("p");
            p.className = "history-empty";
            p.textContent = historyOptInCheckbox.checked
                ? "No revisions recorded yet in this session."
                : "History is disabled. Check the opt-in box above to enable local session history.";
            historyList.appendChild(p);
            return;
        }

        items.forEach((item) => {
            const div = document.createElement("div");
            div.className = "history-item";

            const header = document.createElement("div");
            header.className = "history-item-header";
            const modeSpan = document.createElement("span");
            modeSpan.textContent = `Mode: ${item.mode.toUpperCase()}`;
            const timeSpan = document.createElement("span");
            timeSpan.textContent = item.timestamp;
            header.appendChild(modeSpan);
            header.appendChild(timeSpan);

            const preview = document.createElement("div");
            preview.className = "history-item-preview";
            preview.textContent = item.revised;

            div.appendChild(header);
            div.appendChild(preview);
            historyList.appendChild(div);
        });
    }

    historyOptInCheckbox.addEventListener("change", () => {
        localStorage.setItem("napstertec_history_optin", historyOptInCheckbox.checked ? "true" : "false");
        if (!historyOptInCheckbox.checked) {
            localStorage.removeItem("napstertec_session_history");
            historyCount.textContent = "0";
        }
        renderHistoryUI();
    });

    clearHistoryBtn.addEventListener("click", () => {
        localStorage.removeItem("napstertec_session_history");
        historyCount.textContent = "0";
        renderHistoryUI();
        showAlert("All local session history has been cleared.", false);
    });

    historyModalBtn.addEventListener("click", () => {
        renderHistoryUI();
        historyModal.classList.remove("hidden");
    });
    closeHistoryModalBtn.addEventListener("click", () => historyModal.classList.add("hidden"));
    closeHistoryBtn.addEventListener("click", () => historyModal.classList.add("hidden"));
    loadHistory();

    // Helper: Calculate count statistics safely
    function updateCounts(element, targetBadge) {
        const text = element.value || "";
        const chars = text.length;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        targetBadge.textContent = `${words} words | ${chars} chars`;
    }

    async function handleDocumentUpload() {
        const file = documentFile.files && documentFile.files[0];
        if (!file) return;
        uploadStatus.textContent = `Reading ${file.name}…`;
        uploadStatus.className = "upload-status is-active";
        const formData = new FormData();
        formData.append("file", file);
        try {
            const response = await fetch("/api/v1/extract", { method: "POST", body: formData });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || "The document could not be processed.");
            }
            originalText.value = data.text || "";
            revisedText.value = "";
            activeSelectionRange = null;
            selectionBanner.classList.add("hidden");
            updateCounts(originalText, originalCounts);
            updateCounts(revisedText, revisedCounts);
            displayWarnings([]);
            displayChangeSummary(null);
            uploadStatus.textContent = `${data.filename} loaded · ${data.char_count.toLocaleString()} characters. Uploads are not stored.`;
            uploadStatus.className = "upload-status is-active";
            showAlert("Document loaded into the editor.", false);
            documentFile.value = "";
        } catch (err) {
            uploadStatus.textContent = err.message;
            uploadStatus.className = "upload-status is-error";
            showAlert(err.message, true);
            documentFile.value = "";
        }
    }

    originalText.addEventListener("input", () => {
        updateCounts(originalText, originalCounts);
        activeSelectionRange = null;
        selectionBanner.classList.add("hidden");
    });
    revisedText.addEventListener("input", () => updateCounts(revisedText, revisedCounts));

    // Selection detection
    function checkTextSelection() {
        const start = originalText.selectionStart;
        const end = originalText.selectionEnd;
        if (start !== undefined && end !== undefined && end > start) {
            activeSelectionRange = [start, end];
            selectionLength.textContent = (end - start).toString();
            selectionBanner.classList.remove("hidden");
        } else {
            // Keep active range if user clicks outside unless cleared explicitly
        }
    }

    originalText.addEventListener("mouseup", checkTextSelection);
    originalText.addEventListener("keyup", checkTextSelection);

    clearSelectionBtn.addEventListener("click", () => {
        activeSelectionRange = null;
        selectionBanner.classList.add("hidden");
    });

    // Alerts
    function showAlert(msg, isError = true, variant = "") {
        alertBox.className = isError ? "alert-box alert-error" : variant === "warning" ? "alert-box alert-warning" : "alert-box alert-success";
        alertIcon.textContent = isError ? "!" : variant === "warning" ? "i" : "OK";
        alertMessage.textContent = msg;
        alertBox.classList.remove("hidden");
    }

    function hideAlert() {
        alertBox.classList.add("hidden");
    }

    alertCloseBtn.addEventListener("click", hideAlert);

    // Set Loading State
    function setLoading(isLoading) {
        if (isLoading) {
            refineBtn.disabled = true;
            refineBtnSpinner.classList.remove("hidden");
            refineBtnText.textContent = "Working...";
            cancelBtn.classList.remove("hidden");
        } else {
            refineBtn.disabled = false;
            refineBtnSpinner.classList.add("hidden");
            refineBtnText.textContent = toolDefinitions[activeTool]?.action || "Humanize";
            cancelBtn.classList.add("hidden");
            abortController = null;
        }
    }

    // Cancel Request
    cancelBtn.addEventListener("click", () => {
        if (abortController) {
            abortController.abort();
            setLoading(false);
            showAlert("Request was cancelled by user.", false);
        }
    });

    // Populate Metrics
    function displayMetrics(metrics) {
        if (!metrics) return;
        valReadingEase.textContent = metrics.flesch_reading_ease.toFixed(1);
        valGradeLevel.textContent = metrics.flesch_kincaid_grade.toFixed(1);
        valDiversity.textContent = (metrics.lexical_diversity * 100).toFixed(1) + "%";
        valReadingTime.textContent = metrics.reading_time_minutes.toFixed(2) + " min";
        if (metrics.detected_language) {
            detectedLangBadge.textContent = `Lang: ${metrics.detected_language.toUpperCase()}`;
        }
    }

    // Populate Warnings Safely
    function displayWarnings(warnings) {
        warningsList.replaceChildren();
        if (!warnings || warnings.length === 0) {
            warningsBox.classList.add("hidden");
            return;
        }
        warnings.forEach((warn) => {
            const li = document.createElement("li");
            li.textContent = warn;
            warningsList.appendChild(li);
        });
        warningsBox.classList.remove("hidden");
    }

    // Populate Change Summary Safely
    function displayChangeSummary(summary) {
        changeSummaryList.replaceChildren();
        if (!summary) {
            changeSummaryBox.classList.add("hidden");
            valWordDelta.textContent = "-";
            valWordDeltaDetail.textContent = "Word additions / deletions";
            return;
        }

        const sign = summary.net_word_change >= 0 ? "+" : "";
        valWordDelta.textContent = `${sign}${summary.net_word_change}`;
        valWordDeltaDetail.textContent = `+${summary.added_words} added / -${summary.removed_words} removed`;

        if (summary.key_modifications && summary.key_modifications.length > 0) {
            summary.key_modifications.forEach((mod) => {
                const li = document.createElement("li");
                li.textContent = mod;
                changeSummaryList.appendChild(li);
            });
            changeSummaryBox.classList.remove("hidden");
        } else {
            changeSummaryBox.classList.add("hidden");
        }
    }

    function displayDetector(data) {
        if (!detectorResult || activeTool !== "detector") return;
        detectorResult.classList.remove("hidden");
        const percent = Number.isFinite(Number(data.ai_likelihood_percent))
            ? Math.max(0, Math.min(100, Number(data.ai_likelihood_percent)))
            : 0;
        detectorPercent.textContent = `${percent}%`;
        const status = data.detector_status === "insufficient_text"
            ? "Add at least 80 words for a more meaningful scan."
            : percent === 0
                ? "No passages crossed the conservative signal threshold."
                : "Some passages matched multiple linguistic signals.";
        detectorStatus.textContent = status;
        detectorMethod.textContent = data.detector_notice || "This estimate is not proof of authorship.";
        detectorHighlights.replaceChildren();
        const segments = Array.isArray(data.detector_segments) ? data.detector_segments : [];
        const flagged = segments.filter((segment) => segment.flagged);
        if (flagged.length === 0) {
            detectorHighlights.classList.add("hidden");
            return;
        }
        const heading = document.createElement("strong");
        heading.textContent = "Flagged passages to review";
        detectorHighlights.appendChild(heading);
        flagged.forEach((segment) => {
            const item = document.createElement("div");
            item.className = "detector-highlight-item";
            const quote = document.createElement("mark");
            quote.textContent = segment.text;
            const reason = document.createElement("span");
            reason.textContent = (segment.reasons || []).join(" · ");
            item.appendChild(quote);
            item.appendChild(reason);
            detectorHighlights.appendChild(item);
        });
        detectorHighlights.classList.remove("hidden");
    }

    // Handle Rewrite Request (Synchronous or SSE Streaming)
    async function handleRewrite() {
        const text = originalText.value;
        if (!text.trim()) {
            showAlert("Please enter or paste text to refine.");
            originalText.focus();
            return;
        }

        hideAlert();
        displayWarnings([]);
        setLoading(true);
        abortController = new AbortController();

        const payload = {
            text: text,
            mode: modeSelect.value,
            intensity: intensitySelect.value,
            tone: toneInput.value.trim() || null,
            audience: audienceInput.value.trim() || null,
            instructions: customInstructions.value.trim() || null,
            fallback_to_local: fallbackCheckbox.checked,
            include_change_summary: true,
            selection_range: activeSelectionRange,
            style_profile: getActiveStyleProfile(),
        };

        const useStreaming = streamCheckbox.checked;

        if (useStreaming) {
            await handleStreamingRewrite(payload);
        } else {
            await handleStandardRewrite(payload);
        }
    }

    async function handleStandardRewrite(payload) {
        try {
            const response = await fetch("/api/v1/rewrite", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                signal: abortController.signal,
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMsg = data.message || `Request failed with HTTP ${response.status}`;
                showAlert(errorMsg, true);
                setLoading(false);
                return;
            }

            revisedText.value = data.revised_text || "";
            updateCounts(revisedText, revisedCounts);
            displayMetrics(data.metrics);
            displayWarnings(data.warnings);
            displayChangeSummary(data.change_summary);

            saveHistoryItem(data);

            if (data.is_fallback) {
                showAlert("Basic corrections applied (limited mode).", false, "warning");
            } else {
                showAlert("Done.", false);
            }

        } catch (err) {
            if (err.name === "AbortError") return;
            showAlert(`Network or server error: ${err.message}`, true);
        } finally {
            setLoading(false);
        }
    }

    async function handleStreamingRewrite(payload) {
        revisedText.value = "";
        updateCounts(revisedText, revisedCounts);

        try {
            const response = await fetch("/api/v1/rewrite/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                signal: abortController.signal,
            });

            if (!response.ok) {
                const errData = await response.json();
                showAlert(errData.message || "Failed to start streaming rewrite.", true);
                setLoading(false);
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";
            let sawComplete = false;

            const processEvent = (rawEvent) => {
                const line = rawEvent.trim();
                if (!line) return;
                const eventMatch = line.match(/^event:\s*(\w+)/m);
                const dataMatch = line.match(/^data:\s*(.*)$/m);
                const eventType = eventMatch ? eventMatch[1] : "message";
                let dataJson = {};
                if (dataMatch) {
                    try {
                        dataJson = JSON.parse(dataMatch[1]);
                    } catch (e) {
                        showAlert("Received an invalid streaming event from the server.", true);
                        return;
                    }
                }

                if (eventType === "reset") {
                        revisedText.value = dataJson.text || "";
                        updateCounts(revisedText, revisedCounts);
                } else if (eventType === "chunk") {
                        revisedText.value += dataJson.chunk || "";
                        updateCounts(revisedText, revisedCounts);
                } else if (eventType === "complete") {
                        sawComplete = true;
                        revisedText.value = dataJson.revised_text || revisedText.value;
                        updateCounts(revisedText, revisedCounts);
                        displayMetrics(dataJson.metrics);
                        displayWarnings(dataJson.warnings);
                        displayChangeSummary(dataJson.change_summary);
                        saveHistoryItem(dataJson);

                        if (dataJson.is_fallback) {
                            showAlert("Basic corrections applied (limited mode).", false, "warning");
                        } else {
                            showAlert("Done.", false);
                        }
                } else if (eventType === "error") {
                        showAlert(dataJson.message || "Streaming error occurred.", true);
                }
            };

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const events = buffer.split(/\r?\n\r?\n/);
                buffer = events.pop() || "";
                events.forEach(processEvent);
            }
            buffer += decoder.decode();
            if (buffer.trim()) processEvent(buffer);
            if (!sawComplete && !abortController?.signal.aborted) {
                showAlert("The streaming response ended before completion.", true);
            }

        } catch (err) {
            if (err.name === "AbortError") return;
            showAlert(`Streaming error: ${err.message}`, true);
        } finally {
            setLoading(false);
        }
    }

    // Handle Analyze Request
    async function handleAnalyze() {
        const text = originalText.value.trim();
        if (!text) {
            showAlert("Please enter text to analyze.");
            return;
        }

        hideAlert();
        try {
            const response = await fetch("/api/v1/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text }),
            });
            const data = await response.json();

            if (!response.ok) {
                showAlert(data.message || "Failed to analyze text.", true);
                return;
            }

            displayMetrics(data.metrics);
            displayDetector(data);
            const spanWarnings = data.protected_spans.map(
                (s) => `Detected [${s.span_type.toUpperCase()}]: ${s.text}`
            );
            displayWarnings(spanWarnings);
            if (activeTool === "detector") {
                detectorNotice.classList.remove("hidden");
                showAlert("Descriptive writing analysis complete. No authorship verdict was made.", false);
            } else {
                showAlert("Readability analysis complete.", false);
            }
        } catch (err) {
            showAlert(`Analysis error: ${err.message}`, true);
        }
    }

    // Load Sample Text
    documentFile.addEventListener("change", handleDocumentUpload);
    sampleBtn.addEventListener("click", () => {
        originalText.value =
            "In order to facilitate the expeditious implementation of project Alpha, " +
            "the engineering team will convene on January 15, 2026 at https://meet.google.com/xyz-123. " +
            "Due to the fact that Q3 revenue expanded by 18.5% ($4,500,000), " +
            "we recieve substantial positive momentum as noted by Smith et al. (2024). " +
            "teh overall system latency is reduced by 2.4x.";
        updateCounts(originalText, originalCounts);
        activeSelectionRange = null;
        selectionBanner.classList.add("hidden");
        hideAlert();
    });

    // Clear Text
    clearBtn.addEventListener("click", () => {
        originalText.value = "";
        revisedText.value = "";
        activeSelectionRange = null;
        selectionBanner.classList.add("hidden");
        updateCounts(originalText, originalCounts);
        updateCounts(revisedText, revisedCounts);
        displayMetrics({ flesch_reading_ease: 0, flesch_kincaid_grade: 0, lexical_diversity: 0, reading_time_minutes: 0 });
        if (detectorResult) detectorResult.classList.add("hidden");
        if (detectorHighlights) {
            detectorHighlights.replaceChildren();
            detectorHighlights.classList.add("hidden");
        }
        displayWarnings([]);
        displayChangeSummary(null);
        hideAlert();
    });

    // Copy to Clipboard
    copyBtn.addEventListener("click", async () => {
        const text = revisedText.value;
        if (!text) {
            showAlert("No revised text to copy.");
            return;
        }
        try {
            await navigator.clipboard.writeText(text);
            showAlert("Revised text copied to clipboard!", false);
        } catch (e) {
            showAlert("Failed to copy to clipboard.", true);
        }
    });

    // Export helpers
    function downloadFile(filename, content, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    exportTxtBtn.addEventListener("click", () => {
        const text = revisedText.value;
        if (!text) {
            showAlert("No revised text to export.");
            return;
        }
        downloadFile("revised_text.txt", text, "text/plain;charset=utf-8");
    });

    exportMdBtn.addEventListener("click", () => {
        const text = revisedText.value;
        if (!text) {
            showAlert("No revised text to export.");
            return;
        }
        downloadFile("revised_text.md", text, "text/markdown;charset=utf-8");
    });

    // Event listeners
    refineBtn.addEventListener("click", handleRewrite);
    analyzeBtn.addEventListener("click", handleAnalyze);
});
