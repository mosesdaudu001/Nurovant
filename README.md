# Nurovant
## Overview

Nurovant is a web-based application designed to assist teachers in generating questions and evaluating student responses based on document content. Using Vertex AI's generative models, it processes uploaded PDF or text files to generate questions, question IDs, answers, and key bullet points. Teachers can then provide these questions to students, collect responses, and evaluate the students' understanding using the system.

### Key Features:
- **Document Upload**: Supports PDF and TXT formats for uploading instructional materials.
- **Question Generation**: Automatically generates structured questions, answers, and bullet points from the document.
- **Student Response Evaluation**: Evaluates student responses and provides a score (confidence level) along with an explanation.
- **Database Integration**: Stores generated questions and answers with unique question IDs for further use.

## How it Works:
1. **Document Upload**: The teacher uploads a document, which is processed by Vertex AI to generate bullet points, questions, and answers.
2. **Question Storage**: Generated questions, along with answers and bullet points, are stored in a database with a unique question ID.
3. **Student Response Submission**: Teachers can later input student responses, which are evaluated based on the stored questions and answers.
4. **Scoring & Feedback**: The system returns a score and explanation of the student's understanding of the question.


### Deploy locally
```
# Create a virtual environment
virtualenv vnenv

# Activate virtual environment
source vnenv/bin/activate

# Install all requirements
pip install -r requirements.txt

# Run server
python app.py
```

### Deploy in docker
```
"""Go to the Dockerfile and uncomment the section on deploying to docker, 
   and also comment the section for deploying to GCP """ 

# Build the image
sudo docker build -t mosesdaudu001/nurovant .

# Deploy the image
sudo docker run -it --rm -p 8000:8000 mosesdaudu001/nurovant

```


## API Endpoints
**POST /upload**: This endpoint allows teachers to upload a document (PDF or TXT). The app processes the document and returns the generated questions, answers, and bullet points along with their unique question IDs.

**POST /evaluate**: After receiving student responses, the teacher can submit the question ID and the student’s response to this endpoint. The system then evaluates the response, providing a confidence score and feedback.

## How to Use
Start the app by following the Deploy Locally or Deploy with Docker instructions.
Open the application in your browser.
Upload a document (PDF or TXT) to generate questions and answers.
Provide the questions to students and collect their responses.
Submit the question ID and student’s answer to evaluate their understanding and receive a score with feedback.
