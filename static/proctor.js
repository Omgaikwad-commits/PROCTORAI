document.addEventListener("DOMContentLoaded", function () {

    const video = document.getElementById("webcam");
    const warningInput = document.querySelector('input[name="warnings"]');
    const examForm = document.querySelector("form");

    let warnings = 0;
    const MAX_WARNINGS = 3;

    // ================= CAMERA START =================
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });

            video.srcObject = stream;
            video.play();

        } catch (error) {
            console.error("Camera error:", error);
            alert("Camera access denied or not working!");
        }
    }

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        startCamera();
    } else {
        alert("Camera not supported in this browser.");
    }

    // ================= WARNING FUNCTION =================
    function giveWarning(reason) {

        warnings++;

        if (warningInput) {
            warningInput.value = warnings;
        }

        if (warnings <= MAX_WARNINGS) {
            alert("⚠ Warning!\n" + reason +
                  "\nWarnings: " + warnings + "/" + MAX_WARNINGS);
        }

        if (warnings >= MAX_WARNINGS) {
            terminateExam("🚫 Exam terminated due to multiple violations!");
        }
    }

    // ================= TERMINATE FUNCTION =================
    function terminateExam(message) {
        alert(message);

        setTimeout(function () {
            if (examForm) {
                examForm.submit();
            }
        }, 1500);
    }

    // ================= TAB SWITCH DETECTION =================
    document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
            giveWarning("Do not switch tabs.");
        }
    });

    // ================= FACE DETECTION =================

    const faceDetection = new FaceDetection({
        locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`;
        }
    });

    faceDetection.setOptions({
        model: 'short',
        minDetectionConfidence: 0.7
    });

    let multiFaceCooldown = false;

    let noFaceStartTime = null;
    const NO_FACE_LIMIT = 5000; // 5 seconds

    faceDetection.onResults(results => {

        if (!results.detections) return;

        const faceCount = results.detections.length;

        // ===== MULTIPLE FACE CHECK (3 warnings allowed) =====
        if (faceCount > 1 && !multiFaceCooldown) {

            multiFaceCooldown = true;

            giveWarning("Multiple faces detected!");

            setTimeout(() => {
                multiFaceCooldown = false;
            }, 5000);
        }

        // ===== NO FACE CHECK (DIRECT TERMINATION) =====
        if (faceCount === 0) {

            if (!noFaceStartTime) {
                noFaceStartTime = Date.now();
            }

            const elapsed = Date.now() - noFaceStartTime;

            if (elapsed > NO_FACE_LIMIT) {
                terminateExam("🚫 No face detected for 5 seconds. Exam terminated.");
            }

        } else {
            // Reset timer if face appears again
            noFaceStartTime = null;
        }
    });

    const camera = new Camera(video, {
        onFrame: async () => {
            await faceDetection.send({ image: video });
        },
        width: 640,
        height: 480
    });

    camera.start();
});