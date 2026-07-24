// Initialize the Lucide icons library
lucide.createIcons();

// ==========================================
// 1. GET HTML ELEMENTS
// ==========================================
// We grab the elements from the page so we can control them with JavaScript
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const markBtn = document.getElementById('markBtn');
const statusCard = document.getElementById('statusCard');
const statusText = document.getElementById('statusText');
const statusIcon = document.getElementById('statusIcon');


// ==========================================
// 2. TURN ON THE WEBCAM
// ==========================================
// Ask the browser for permission to use the camera
navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
    .then(stream => { 
        // If allowed, stream the live video to our <video> tag
        video.srcObject = stream; 
    })
    .catch(err => {
        // If denied or broken, show an error message on the screen
        showStatus("Webcam access denied. Please allow camera permissions.", "error");
    });


// ==========================================
// 3. HELPER FUNCTION: SHOW MESSAGES
// ==========================================
function showStatus(message, type) {
    // Update the card's style (success = green, error = red) and make it visible
    statusCard.className = `status-card ${type}`;
    statusCard.style.display = 'flex';
    statusText.innerText = message;
    
    // Dynamically choose the right icon based on the message content
    if (type === 'success') {
        statusIcon.setAttribute('data-lucide', 'check-circle');
    } else if (message.toLowerCase().includes('spoof')) {
        statusIcon.setAttribute('data-lucide', 'shield-alert'); // Shield icon for security alerts
    } else {
        statusIcon.setAttribute('data-lucide', 'alert-triangle'); // General error icon
    }
    
    // Refresh the icons to render the new one we just set
    lucide.createIcons();
}


// ==========================================
// 4. THE MAIN EVENT: CLICKING "VERIFY"
// ==========================================
markBtn.addEventListener('click', async () => {
    
    // Step A: Put the button in a "Loading" state so they don't click it twice
    const originalText = markBtn.innerHTML;
    markBtn.innerHTML = `<i data-lucide="loader" class="spin"></i> Scanning...`;
    markBtn.disabled = true;
    statusCard.style.display = 'none'; // Hide any old messages
    lucide.createIcons();
    
    // Make the loader icon spin infinitely
    document.querySelector('.spin').animate(
        [{transform: 'rotate(0deg)'}, {transform: 'rotate(360deg)'}], 
        {duration: 1000, iterations: Infinity}
    );

    // Step B: Take a picture! 
    // We do this by secretly drawing the current video frame onto a hidden <canvas>
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    // Convert that picture into a Base64 text string so it can be sent over the internet
    const base64Image = canvas.toDataURL('image/jpeg');

    // Step C: Send the picture to our Python backend
    try {
        const response = await fetch('/mark_attendance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: base64Image })
        });
        
        const result = await response.json();
        
        // Step D: Show the result to the user
        if (response.ok) {
            showStatus(result.message, "success"); // Recognized!
        } else {
            showStatus(result.error || "Verification failed.", "error"); // Spoof or Unknown
        }
        
    } catch (error) {
        // This triggers if the server crashes or the internet drops
        showStatus("Server error. Please try again.", "error");
        
    } finally {
        // Step E: Reset the button back to normal, no matter what happened
        markBtn.innerHTML = originalText;
        markBtn.disabled = false;
        lucide.createIcons();
    }
});