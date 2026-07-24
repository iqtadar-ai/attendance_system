// Initialize the Lucide icons library
lucide.createIcons();

// ==========================================
// 1. GET HTML ELEMENTS
// ==========================================
// Grab the elements from the page so we can read their values or change them
const imageUpload = document.getElementById('imageUpload');
const imagePreview = document.getElementById('imagePreview');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const registerBtn = document.getElementById('registerBtn');
const statusCard = document.getElementById('statusCard');
const statusText = document.getElementById('statusText');
const statusIcon = document.getElementById('statusIcon');

// This variable will hold the image data once the user uploads a photo
let base64Image = "";


// ==========================================
// 2. HANDLE IMAGE UPLOADS (The Preview)
// ==========================================
// Listen for when a user selects a file from their computer
imageUpload.addEventListener('change', function(event) {
    const file = event.target.files[0];
    
    if (file) {
        // FileReader allows the browser to read the file locally 
        const reader = new FileReader();
        
        // What to do once the file is fully read:
        reader.onload = function(e) {
            // 1. Save the image as a Base64 text string
            base64Image = e.target.result;
            
            // 2. Put that image into our <img> tag to show a preview
            imagePreview.src = base64Image;
            imagePreview.style.display = "block";
            
            // 3. Hide the "Click or drag image to upload" text
            uploadPlaceholder.style.display = "none";
        }
        
        // Start reading the file
        reader.readAsDataURL(file);
    }
});


// ==========================================
// 3. HELPER FUNCTION: SHOW MESSAGES
// ==========================================
function showStatus(message, type) {
    // Update the card's style (success = green, error = red) and make it visible
    statusCard.className = `status-card ${type}`;
    statusCard.style.display = 'flex';
    statusText.innerText = message;
    
    // Dynamically choose the right icon
    statusIcon.setAttribute('data-lucide', type === 'success' ? 'check-circle' : 'alert-triangle');
    
    // Refresh the icons to render the new one we just set
    lucide.createIcons();
}


// ==========================================
// 4. THE MAIN EVENT: CLICKING "REGISTER"
// ==========================================
registerBtn.addEventListener('click', async () => {
    
    // Step A: Read what the user typed in the text boxes
    const name = document.getElementById('name').value;
    const student_id = document.getElementById('student_id').value;

    // Step B: Basic Validation (Make sure nothing is empty)
    if (!name || !student_id || !base64Image) {
        showStatus("Please fill all fields and upload an image.", "error");
        return; // Stop the function here if they missed something
    }

    // Step C: Put the button in a "Loading" state
    const originalText = registerBtn.innerHTML;
    registerBtn.innerHTML = `<i data-lucide="loader" class="spin"></i> Processing...`;
    registerBtn.disabled = true;
    
    // Make the loader icon spin infinitely
    document.querySelector('.spin').animate(
        [{transform: 'rotate(0deg)'}, {transform: 'rotate(360deg)'}], 
        {duration: 1000, iterations: Infinity}
    );

    // Step D: Send the data to our Python backend
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name: name, 
                student_id: student_id, 
                image: base64Image 
            })
        });
        
        const result = await response.json();
        
        // Step E: Handle the Server Response
        if (response.ok) {
            // Success! Show a message and clear out the form for the next person
            showStatus(result.message, "success");
            document.getElementById('name').value = '';
            document.getElementById('student_id').value = '';
            imageUpload.value = '';
            imagePreview.style.display = 'none';
            uploadPlaceholder.style.display = 'flex';
            base64Image = "";
            
        } else {
            // Backend rejected it (e.g., no face detected, or ID already exists)
            showStatus(result.error || "Failed to register.", "error");
        }
        
    } catch (error) {
        // Triggers if the server is down
        showStatus("Server error. Please try again.", "error");
        
    } finally {
        // Step F: Reset the button back to normal
        registerBtn.innerHTML = originalText;
        registerBtn.disabled = false;
        lucide.createIcons();
    }
});