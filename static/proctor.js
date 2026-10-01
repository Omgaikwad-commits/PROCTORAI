document.addEventListener("DOMContentLoaded", function () {

    // ================= DOM ELEMENTS =================
    const video = document.getElementById("webcam");
    const canvas = document.getElementById("proctor-canvas");
    const ctx = canvas ? canvas.getContext("2d") : null;

    const warningInput = document.getElementById("warnings") || document.querySelector('input[name="warnings"]');
    const mobileWarningInput = document.getElementById("mobile_warnings") || document.querySelector('input[name="mobile_warnings"]');
    const eyeWarningInput = document.getElementById("eye_warnings") || document.querySelector('input[name="eye_warnings"]');
    const tabWarningInput = document.getElementById("tab_warnings") || document.querySelector('input[name="tab_warnings"]');
    const faceWarningInput = document.getElementById("face_warnings") || document.querySelector('input[name="face_warnings"]');
    const examForm = document.querySelector("form");

    const hudFaceText = document.getElementById("hud-face-text");
    const hudEyeText = document.getElementById("hud-eye-text");
    const hudMobileText = document.getElementById("hud-mobile-text");
    const hudWarningCount = document.getElementById("hud-warning-count");
    const proctorToast = document.getElementById("proctor-toast");

    // ================= PROCTORING STATE =================
    let warnings = 0;
    let mobileWarnings = 0;
    let eyeWarnings = 0;
    let tabWarnings = 0;
    let faceWarnings = 0;
    const MAX_WARNINGS = 3;
    let isTerminated = false;

    // Cooldown & timer controls
    let multiFaceCooldown = false;
    let noFaceStartTime = null;
    const NO_FACE_LIMIT = 5000; // 5 seconds absence allowed

    let lookingAwayStartTime = null;
    let eyeCooldown = false;
    const LOOKING_AWAY_LIMIT = 2400; // 2.4 seconds continuous look-away
    const EYE_COOLDOWN_MS = 4000; // 4s cooldown after warning

    let cocoModel = null;
    let mobileDetectedStartTime = null;
    let mobileCooldown = false;
    const MOBILE_SUSTAINED_MS = 1000; // 1s continuous presence
    const MOBILE_COOLDOWN_MS = 5000; // 5s cooldown after warning

    let lastDetectedPhoneBox = null;
    let latestFaceLandmarks = null;
    let currentGazeState = "Initializing";

    // ================= AUDIO ALERT (Web Audio API) =================
    let audioCtx = null;
    function playWarningBeep() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            if (!audioCtx) audioCtx = new AudioContext();

            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();

            osc.type = "sine";
            osc.frequency.setValueAtTime(750, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(450, audioCtx.currentTime + 0.25);

            gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.25);

            osc.connect(gain);
            gain.connect(audioCtx.destination);

            osc.start();
            osc.stop(audioCtx.currentTime + 0.28);
        } catch (e) {
            console.log("Audio alert not available:", e);
        }
    }

    // ================= TOAST NOTIFICATION =================
    let toastTimeout = null;
    function showToast(message, isDanger = true) {
        if (!proctorToast) return;
        clearTimeout(toastTimeout);

        proctorToast.innerHTML = `<strong>Warning:</strong> ${message}`;
        proctorToast.className = isDanger ? "proctor-toast toast-danger" : "proctor-toast toast-warn";
        proctorToast.classList.remove("hidden");

        toastTimeout = setTimeout(() => {
            proctorToast.classList.add("hidden");
        }, 4000);
    }

    // ================= WARNING FUNCTION =================
    function giveWarning(reason, type = "general") {
        if (isTerminated) return;

        warnings++;

        if (type === "mobile") {
            mobileWarnings++;
        } else if (type === "eye") {
            eyeWarnings++;
        } else if (type === "tab") {
            tabWarnings++;
        } else if (type === "face") {
            faceWarnings++;
        }

        // Sync hidden input values for server submission
        if (warningInput) warningInput.value = warnings;
        if (mobileWarningInput) mobileWarningInput.value = mobileWarnings;
        if (eyeWarningInput) eyeWarningInput.value = eyeWarnings;
        if (tabWarningInput) tabWarningInput.value = tabWarnings;
        if (faceWarningInput) faceWarningInput.value = faceWarnings;

        // Update HUD
        if (hudWarningCount) {
            hudWarningCount.textContent = `${warnings} / ${MAX_WARNINGS}`;
            if (warnings >= 2) {
                hudWarningCount.className = "hud-status status-danger";
            } else if (warnings === 1) {
                hudWarningCount.className = "hud-status status-warn";
            }
        }

        playWarningBeep();
        showToast(reason);

        // Flash video border
        const vContainer = document.querySelector(".video-container");
        if (vContainer) {
            vContainer.classList.add("flash-warning");
            setTimeout(() => vContainer.classList.remove("flash-warning"), 800);
        }

        if (warnings >= MAX_WARNINGS) {
            terminateExam(`Exam terminated! Maximum allowed warnings (${MAX_WARNINGS}) reached.`);
        } else {
            // Non-blocking browser alert
            setTimeout(() => {
                alert(`Warning #${warnings} / ${MAX_WARNINGS}!\n${reason}\n\nExceeding ${MAX_WARNINGS} warnings will auto-terminate your exam.`);
            }, 50);
        }
    }

    // ================= TERMINATE FUNCTION =================
    function terminateExam(message) {
        if (isTerminated) return;
        isTerminated = true;

        playWarningBeep();

        if (hudFaceText) {
            hudFaceText.textContent = "TERMINATED";
            hudFaceText.className = "hud-status status-danger";
        }

        const vContainer = document.querySelector(".video-container");
        if (vContainer) {
            vContainer.classList.add("flash-terminated");
        }

        alert(message);

        setTimeout(function () {
            if (examForm) {
                // Ensure warning fields are set before submit
                if (warningInput) warningInput.value = warnings;
                if (mobileWarningInput) mobileWarningInput.value = mobileWarnings;
                if (eyeWarningInput) eyeWarningInput.value = eyeWarnings;
                if (tabWarningInput) tabWarningInput.value = tabWarnings;
                if (faceWarningInput) faceWarningInput.value = faceWarnings;
                examForm.submit();
            }
        }, 1200);
    }

    // ================= TAB SWITCH DETECTION =================
    let tabCooldown = false;
    function handleTabSwitch(reason) {
        if (tabCooldown || isTerminated) return;
        tabCooldown = true;
        giveWarning(reason, "tab");
        setTimeout(() => {
            tabCooldown = false;
        }, 2500);
    }

    document.addEventListener("visibilitychange", function () {
        if (document.hidden && !isTerminated) {
            handleTabSwitch("Tab switch detected! Do not navigate away from the exam window.");
        }
    });

    window.addEventListener("blur", function () {
        if (!isTerminated) {
            // Give brief debounce for OS notifications
            setTimeout(() => {
                if (document.hidden && !isTerminated) {
                    handleTabSwitch("Window lost focus / switched! Please stay on the exam screen.");
                }
            }, 300);
        }
    });

    // ================= CAMERA START =================
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: "user"
                },
                audio: false
            });

            video.srcObject = stream;
            await video.play();

            syncCanvas();
            console.log("Webcam started successfully.");

        } catch (error) {
            console.error("Camera access error:", error);
            if (hudFaceText) {
                hudFaceText.textContent = "Cam Error";
                hudFaceText.className = "hud-status status-danger";
            }
            alert("Camera access denied or webcam not found! Please allow camera access to take this exam.");
        }
    }

    function syncCanvas() {
        if (!canvas || !video) return;
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
    }

    video.addEventListener("loadedmetadata", syncCanvas);

    // ================= COCO-SSD MOBILE DETECTION =================
    async function loadCocoModel() {
        if (hudMobileText) {
            hudMobileText.textContent = "Loading AI...";
            hudMobileText.className = "hud-status status-loading";
        }
        try {
            cocoModel = await cocoSsd.load({ base: "lite_mobilenet_v2" });
            console.log("COCO-SSD mobile detection model ready.");
            if (hudMobileText) {
                hudMobileText.textContent = "🟢 None";
                hudMobileText.className = "hud-status status-ok";
            }
            // Start mobile detection loop
            setInterval(runMobileDetection, 400);
        } catch (err) {
            console.warn("Failed to load COCO-SSD lite model, retrying default:", err);
            try {
                cocoModel = await cocoSsd.load();
                if (hudMobileText) {
                    hudMobileText.textContent = "🟢 None";
                    hudMobileText.className = "hud-status status-ok";
                }
                setInterval(runMobileDetection, 400);
            } catch (err2) {
                console.error("COCO-SSD model load error:", err2);
                if (hudMobileText) {
                    hudMobileText.textContent = "Unavailable";
                    hudMobileText.className = "hud-status status-muted";
                }
            }
        }
    }

    async function runMobileDetection() {
        if (!cocoModel || !video || video.readyState < 2 || isTerminated) return;

        try {
            const predictions = await cocoModel.detect(video);
            let phone = null;

            for (const p of predictions) {
                // Check for cell phone class with confidence >= 50%
                if ((p.class === "cell phone" || p.class === "phone") && p.score >= 0.50) {
                    phone = p;
                    break;
                }
            }

            // Check for multiple people in camera view
            let personCount = 0;
            for (const p of predictions) {
                if (p.class === "person" && p.score >= 0.55) {
                    personCount++;
                }
            }
            if (personCount > 1 && !multiFaceCooldown) {
                multiFaceCooldown = true;
                giveWarning("👥 Multiple people detected in camera! Only the candidate may be present.", "face");
                setTimeout(() => {
                    multiFaceCooldown = false;
                }, 5000);
            }

            if (phone) {
                lastDetectedPhoneBox = {
                    bbox: phone.bbox,
                    score: phone.score
                };

                if (hudMobileText) {
                    hudMobileText.textContent = "DETECTED";
                    hudMobileText.className = "hud-status status-danger";
                }

                if (!mobileDetectedStartTime) {
                    mobileDetectedStartTime = Date.now();
                }

                const elapsed = Date.now() - mobileDetectedStartTime;
                if (elapsed >= MOBILE_SUSTAINED_MS && !mobileCooldown) {
                    mobileCooldown = true;
                    giveWarning("Mobile phone detected in camera view! Mobile devices are strictly prohibited.", "mobile");
                    setTimeout(() => {
                        mobileCooldown = false;
                    }, MOBILE_COOLDOWN_MS);
                }

            } else {
                lastDetectedPhoneBox = null;
                mobileDetectedStartTime = null;

                if (hudMobileText && !isTerminated) {
                    hudMobileText.textContent = "None";
                    hudMobileText.className = "hud-status status-ok";
                }
            }

        } catch (e) {
            // Silently recover if frame drop occurs
        }
    }

    // ================= MEDIAPIPE FACE MESH & EYE DETECTION =================
    const faceMesh = new FaceMesh({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
    });

    faceMesh.setOptions({
        maxNumFaces: 2,
        refineLandmarks: true, // Enables iris landmarks (468-477)
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    faceMesh.onResults(onFaceResults);

    function onFaceResults(results) {
        if (isTerminated) return;

        const faces = results.multiFaceLandmarks;

        // ===== 1. NO FACE CHECK =====
        if (!faces || faces.length === 0) {
            latestFaceLandmarks = null;
            currentGazeState = "No Face";

            if (hudFaceText) {
                hudFaceText.textContent = "No Face";
                hudFaceText.className = "hud-status status-danger";
            }
            if (hudEyeText) {
                hudEyeText.textContent = "--";
                hudEyeText.className = "hud-status status-muted";
            }

            if (!noFaceStartTime) {
                noFaceStartTime = Date.now();
            }

            const elapsed = Date.now() - noFaceStartTime;
            if (elapsed > NO_FACE_LIMIT) {
                terminateExam("No face detected in camera view for over 5 seconds. Exam terminated.");
            }

            drawOverlay();
            return;
        }

        // Face detected -> reset absence timer
        noFaceStartTime = null;

        // ===== 2. MULTIPLE FACES CHECK =====
        if (faces.length > 1) {
            latestFaceLandmarks = null;
            currentGazeState = "Multiple Faces";

            if (hudFaceText) {
                hudFaceText.textContent = "Multiple Faces";
                hudFaceText.className = "hud-status status-danger";
            }
            if (hudEyeText) {
                hudEyeText.textContent = "Multiple People";
                hudEyeText.className = "hud-status status-warn";
            }

            if (!multiFaceCooldown) {
                multiFaceCooldown = true;
                giveWarning("Multiple faces detected! Only the registered student is allowed in the frame.", "face");
                setTimeout(() => {
                    multiFaceCooldown = false;
                }, 5000);
            }

            drawOverlay();
            return;
        }

        // ===== 3. SINGLE FACE & EYE GAZE TRACKING =====
        const lm = faces[0];
        latestFaceLandmarks = lm;

        if (hudFaceText) {
            hudFaceText.textContent = "🟢 Present";
            hudFaceText.className = "hud-status status-ok";
        }

        // Helper: Euclidean distance
        const dist = (p1, p2) => Math.hypot(p1.x - p2.x, p1.y - p2.y);

        // --- Right Eye (viewer's left side): outer=33, inner=133, iris=468, top=159, bottom=145 ---
        const rOuter = lm[33];
        const rInner = lm[133];
        const rIris = lm[468] || { x: (rOuter.x + rInner.x) / 2, y: (rOuter.y + rInner.y) / 2 };
        const rWidth = Math.abs(rInner.x - rOuter.x) || 0.001;
        const rIrisRatio = (rIris.x - Math.min(rOuter.x, rInner.x)) / rWidth;
        const rHeight = dist(lm[159], lm[145]);

        // --- Left Eye (viewer's right side): inner=362, outer=263, iris=473, top=386, bottom=374 ---
        const lInner = lm[362];
        const lOuter = lm[263];
        const lIris = lm[473] || { x: (lInner.x + lOuter.x) / 2, y: (lInner.y + lOuter.y) / 2 };
        const lWidth = Math.abs(lOuter.x - lInner.x) || 0.001;
        const lIrisRatio = (lIris.x - Math.min(lInner.x, lOuter.x)) / lWidth;
        const lHeight = dist(lm[386], lm[374]);

        const avgIrisRatio = (rIrisRatio + lIrisRatio) / 2;
        const ear = ((rHeight / rWidth) + (lHeight / lWidth)) / 2; // Eye aspect ratio

        // --- Head Pose Estimation ---
        // Yaw (left / right turn): nose=1, right cheek=234, left cheek=454
        const nose = lm[1];
        const rightCheek = lm[234];
        const leftCheek = lm[454];
        const faceW = Math.abs(leftCheek.x - rightCheek.x) || 0.001;
        const headYaw = (nose.x - Math.min(rightCheek.x, leftCheek.x)) / faceW;

        // Pitch (up / down tilt): forehead=10, chin=152
        const forehead = lm[10];
        const chin = lm[152];
        const faceH = Math.abs(chin.y - forehead.y) || 0.001;
        const headPitch = (nose.y - Math.min(forehead.y, chin.y)) / faceH;

        // Determine Gaze & Orientation State
        let gaze = "Focused";
        let reason = "";

        if (ear < 0.08) {
            gaze = "Eyes Closed / Looking Down";
            reason = "closing eyes or looking completely down away from screen";
        } else if (headYaw < 0.30 || avgIrisRatio < 0.28) {
            gaze = "Looking Right";
            reason = "looking away to the right";
        } else if (headYaw > 0.70 || avgIrisRatio > 0.72) {
            gaze = "Looking Left";
            reason = "looking away to the left";
        } else if (headPitch > 0.75) {
            gaze = "Looking Down";
            reason = "looking down away from screen";
        } else if (headPitch < 0.38) {
            gaze = "Looking Up";
            reason = "looking up away from screen";
        }

        currentGazeState = gaze;

        // Check if looking away persistently
        if (gaze !== "Focused") {
            if (hudEyeText) {
                hudEyeText.textContent = `${gaze}`;
                hudEyeText.className = "hud-status status-danger";
            }

            if (!lookingAwayStartTime) {
                lookingAwayStartTime = Date.now();
            }

            const elapsed = Date.now() - lookingAwayStartTime;
            if (elapsed >= LOOKING_AWAY_LIMIT && !eyeCooldown) {
                eyeCooldown = true;
                giveWarning(`Eye gaze diverted! Student is ${reason}. Please look directly at the exam screen!`, "eye");
                setTimeout(() => {
                    eyeCooldown = false;
                }, EYE_COOLDOWN_MS);
            }

        } else {
            // Student returned gaze to center
            lookingAwayStartTime = null;

            if (hudEyeText && !isTerminated) {
                hudEyeText.textContent = "Focused";
                hudEyeText.className = "hud-status status-ok";
            }
        }

        drawOverlay();
    }

    // ================= CANVAS OVERLAY DRAWING =================
    function drawOverlay() {
        if (!ctx || !canvas || !video || video.readyState < 2) return;

        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            syncCanvas();
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 1. Draw Mobile Phone Bounding Box if detected
        if (lastDetectedPhoneBox) {
            const [bx, by, bw, bh] = lastDetectedPhoneBox.bbox;
            const scorePercent = Math.round(lastDetectedPhoneBox.score * 100);

            // Shaded red box
            ctx.fillStyle = "rgba(255, 51, 102, 0.22)";
            ctx.fillRect(bx, by, bw, bh);

            // Bold animated border
            ctx.strokeStyle = "#ff3366";
            ctx.lineWidth = 3;
            ctx.strokeRect(bx, by, bw, bh);

            // Corner accents
            const cLen = 14;
            ctx.lineWidth = 4;
            ctx.strokeStyle = "#ff0055";

            // Top-left
            ctx.beginPath();
            ctx.moveTo(bx, by + cLen);
            ctx.lineTo(bx, by);
            ctx.lineTo(bx + cLen, by);
            ctx.stroke();

            // Top-right
            ctx.beginPath();
            ctx.moveTo(bx + bw - cLen, by);
            ctx.lineTo(bx + bw, by);
            ctx.lineTo(bx + bw, by + cLen);
            ctx.stroke();

            // Label tag badge
            const labelText = `CELL PHONE (${scorePercent}%)`;
            ctx.font = "bold 13px 'Poppins', sans-serif";
            const textWidth = ctx.measureText(labelText).width;

            ctx.fillStyle = "#ff0055";
            ctx.fillRect(bx, Math.max(0, by - 24), textWidth + 16, 24);

            ctx.fillStyle = "#ffffff";
            ctx.fillText(labelText, bx + 8, Math.max(16, by - 7));
        }

        // 2. Draw Eye Tracking Iris Indicators if face landmarks available
        if (latestFaceLandmarks) {
            const lm = latestFaceLandmarks;
            const rIris = lm[468];
            const lIris = lm[473];

            const isFocused = currentGazeState === "Focused";
            const irisColor = isFocused ? "#00ff99" : "#ff3366";

            // Draw right iris marker
            if (rIris) {
                const rx = rIris.x * canvas.width;
                const ry = rIris.y * canvas.height;
                ctx.beginPath();
                ctx.arc(rx, ry, 4, 0, 2 * Math.PI);
                ctx.fillStyle = irisColor;
                ctx.fill();
                ctx.lineWidth = 1.5;
                ctx.strokeStyle = "#ffffff";
                ctx.stroke();
            }

            // Draw left iris marker
            if (lIris) {
                const lx = lIris.x * canvas.width;
                const ly = lIris.y * canvas.height;
                ctx.beginPath();
                ctx.arc(lx, ly, 4, 0, 2 * Math.PI);
                ctx.fillStyle = irisColor;
                ctx.fill();
                ctx.lineWidth = 1.5;
                ctx.strokeStyle = "#ffffff";
                ctx.stroke();
            }

            // Subdued face boundary guide
            const nose = lm[1];
            if (nose) {
                const nx = nose.x * canvas.width;
                const ny = nose.y * canvas.height;
                ctx.beginPath();
                ctx.arc(nx, ny, 3, 0, 2 * Math.PI);
                ctx.fillStyle = isFocused ? "rgba(0, 255, 153, 0.4)" : "rgba(255, 51, 102, 0.6)";
                ctx.fill();
            }
        }

        // 3. Top-left proctor watermark indicator
        ctx.fillStyle = "rgba(0, 0, 0, 0.55)";
        ctx.fillRect(8, 8, 130, 22);

        // Blinking recording dot
        const now = Date.now();
        const blink = Math.floor(now / 500) % 2 === 0;
        ctx.beginPath();
        ctx.arc(18, 19, 4, 0, 2 * Math.PI);
        ctx.fillStyle = blink ? "#00ff99" : "#00aa66";
        ctx.fill();

        ctx.font = "600 11px 'Poppins', sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.fillText("AI PROCTORING", 27, 23);
    }

    // ================= INITIALIZE PIPELINE =================
    async function initProctoring() {
        if (hudFaceText) {
            hudFaceText.textContent = "Starting Cam...";
            hudFaceText.className = "hud-status status-loading";
        }
        if (hudEyeText) {
            hudEyeText.textContent = "Loading AI...";
            hudEyeText.className = "hud-status status-loading";
        }

        await startCamera();

        // Load COCO-SSD for mobile phone detection
        loadCocoModel();

        // Start MediaPipe Camera loop for FaceMesh
        try {
            const camera = new Camera(video, {
                onFrame: async () => {
                    if (video && video.readyState >= 2 && !isTerminated) {
                        await faceMesh.send({ image: video });
                    }
                },
                width: 640,
                height: 480
            });
            camera.start();
            console.log("MediaPipe Camera initialized.");
        } catch (e) {
            console.error("Camera utility fallback required:", e);
            // Fallback manual frame processing
            function processLoop() {
                if (video && video.readyState >= 2 && !isTerminated) {
                    faceMesh.send({ image: video }).catch(() => {});
                }
                requestAnimationFrame(processLoop);
            }
            requestAnimationFrame(processLoop);
        }
    }

    initProctoring();
});