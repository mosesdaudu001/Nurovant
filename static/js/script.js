document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const progressBar = document.getElementById('progress-fill');
    const uploadStatus = document.getElementById('upload-status');
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');

    // Handle file upload with progress
    uploadForm.addEventListener('submit', function (event) {
        event.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            uploadStatus.textContent = 'Please select a file.';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);

        // Update progress bar
        xhr.upload.onprogress = function (event) {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                progressBar.style.width = percentComplete + '%';
            }
        };

        xhr.onload = function () {
            if (xhr.status === 200) {
                uploadStatus.textContent = 'File uploaded successfully.';
            } else {
                uploadStatus.textContent = 'File upload failed.';
            }
            progressBar.style.width = '0%';
        };

        xhr.send(formData);
    });

    // Handle chat messages
    chatForm.addEventListener('submit', function (event) {
        event.preventDefault();
        
        const question = chatInput.value.trim();
        if (!question) return;

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question }),
        })
        .then(response => response.json())
        .then(data => {
            chatInput.value = '';
            updateChatBox(data.history);
        });
    });

    function updateChatBox(history) {
        chatBox.innerHTML = '';
        history.forEach(item => {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.innerHTML = `<strong>You:</strong> ${item.question}<br><strong>Response:</strong> ${item.response}`;
            chatBox.appendChild(messageDiv);
        });
    }
});
