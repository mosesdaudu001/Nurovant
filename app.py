import os
import base64
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import PyPDF2
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
import pandas as pd
import re
import uuid


# Import neccessary dependencies
from google.cloud import storage
from dotenv import load_dotenv
import pymysql
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes

# SQL Initiator and query functions

load_dotenv()
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")  # e.g. 'my-db-password'
db_name = os.getenv("DB_NAME")  # e.g. 'my-database'
instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./development-416403-b306695feb67.json"

def connect_with_db() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of MySQL.

    Uses the Cloud SQL Python Connector package.
    """
    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    connector = Connector(ip_type)

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        return conn

    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        # ...
    )
    return pool


# Function to generate a unique identifier for each question
def generate_question_id():
    return str(uuid.uuid4())


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./development-416403-b306695feb67.json"


app = Flask(__name__)

# Folder to store uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf'}

# Check if file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize Vertex AI
vertexai.init(project="development-416403", location="us-central1")
model = GenerativeModel("gemini-1.5-flash-001")

# Read uploaded file
def read_file(file_path, file_extension):
    content = ""
    if file_extension == 'pdf':
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            content = ''.join([page.extract_text() for page in reader.pages])
    elif file_extension == 'txt':
        with open(file_path, 'r') as file:
            content = file.read()
    return content

def push_df_db(df, engine):
    for index, row in df.iterrows():
        Question_ID = row['Question_ID']
        Bullet_Points = row['Bullet_Points']
        Questions = row['Questions']
        Answers = row['Answers']
                
        with engine.connect() as connection:
            stmt = sqlalchemy.text(
                "INSERT INTO QuestionsTable (Question_ID, Bullet_Points, Questions, Answers) VALUES (:Question_ID, :Bullet_Points, :Questions, :Answers)"
            )
            connection.execute(stmt, parameters={"Question_ID": Question_ID, "Bullet_Points": Bullet_Points, "Questions": Questions, "Answers": Answers})
            connection.commit()


def retrieve_from_db(question_id, engine):
    with engine.connect() as connection:
        user = connection.execute(
            sqlalchemy.text(
                "SELECT Bullet_Points, Questions, Answers FROM QuestionsTable WHERE Question_ID = :question_id"
            ),
            {"question_id":question_id}
        ).fetchall()
    return user[0]
            
# Process document using Vertex AI Generative Model
def process_document(base64_content, file_extension):
    # document_part = Part.from_data(mime_type="text/plain", data=content.encode())
    # document_part = Part.from_data(mime_type="application/pdf", data=base64.b64decode(content))
    if file_extension == 'pdf':
        # Assuming the PDF content is in base64
        document_part = Part.from_data(mime_type="application/pdf", data=base64.b64decode(base64_content))
    elif file_extension == 'txt':
        # If it's a text file, directly pass the encoded content
        document_part = Part.from_data(mime_type="text/plain", data=base64_content.encode())


    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }

    safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
    ]

    responses = model.generate_content(
        [f"""I am a teacher trying to generate possible questions and answers for my students. 
         Based on the attached document, kindly generate bullet points (emphasizing key details in the answer to improve understanding), questions, and answers in a structured format for my students. 
         An example of the format that I want is:
         **Bullet Point 1: The meeting began at 10:20am and addressed the upcoming end-of-year unit thanksgiving, dressing regulations, and scarf/tie guidelines for the ushering unit ** * **Question:** What was the main focus of the meeting held on September 1st, 2024? * **Answer:** The meeting focused on preparations for the upcoming end-of-year unit thanksgiving, including contributions, budget planning, and the unit's dress code and uniform guidelines. **Bullet Point 2: Members were encouraged to contribute their monthly love seed for the thanksgiving celebration. A unit budget was discussed for catering, with suggestions of Semo and Afang Soup. Contributions were encouraged but not mandated.** * **Question:** What was the significance of the "love seed" contribution mentioned during the meeting? * **Answer:** The love seed contributions were to be used for the upcoming end-of-year unit thanksgiving celebration, which was to be a unit-wide event.
         Each bullet point should be properly numbered as shown in the above example and there should be only one respective question and answer for each bullet point""", 
         document_part],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    response = "".join([response.text for response in responses])
    
    
    # print("response: ", response)
    # Splitting the response to extract bullet points
    
    
    # Regex patterns
    bullet_point_pattern = r'\*\*Bullet Point \d+: (.*?)\*\*'
    question_pattern = r'\* \*\*Question:\*\* (.*?)\?'
    answer_pattern = r'\* \*\*Answer:\*\* (.*?)\n'

    # Extracting lists
    bullet_points = re.findall(bullet_point_pattern, response)
    questions = re.findall(question_pattern, response)
    answers = re.findall(answer_pattern, response)
    Question_id = [generate_question_id() for _ in range(len(answers))]

    data = {
        'Question_ID': Question_id,
        'Bullet_Points': bullet_points,
        'Questions': questions,
        'Answers': answers
    }
    
    # print("Dict: ", data)
    df = pd.DataFrame(data)
    
    # data = df.to_dict()
    

    engine = connect_with_db()
    push_df_db(df, engine)
    
    # # # Display the DataFrame
    # df.to_csv('sample.csv', index=False)
    # print(df.head())

    # return jsonify({
    #     'Question_ID': Question_id,
    #     'Bullet_Points': bullet_points,
    #     'Questions': questions,
    #     'Answers': answers
    # })
    return data #jsonify({'response': data})


# Process document using Vertex AI Generative Model
def process_student_response(Bullet_Points, Questions, Answers, student_answer):
   
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }

    safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
    ]

    responses = model.generate_content(
        [f"""As a teacher, based on the bullet point: {Bullet_Points}, I gave my student the question: {Questions} which should have the answer: {Answers}. 
         But the student's response was : {student_answer}. I want you to tell me if the student 
         understood the bullet point based on the students answer and I want you to tell me a scale 1 - 10 how confident you are that 
         the student has understood the bullet point. You response should be like the below example:
         An example of the format that I want is:
         **knowledge_understood : True**
         **knowledge_confidence : 8**
         
         **Explanation:** The student's answer demonstrates he understands the bullet point quite well.
         """],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    response = "".join([response.text for response in responses])
    
    # print("Response: ", response)
    
    # print("response: ", response)
    # Splitting the response to extract bullet points
    
    
    # Regular expressions to extract the values
    knowledge_understood = re.search(r'\*\*knowledge_understood\s*:\s*(\w+)\*\*', response).group(1)
    knowledge_confidence = re.search(r'\*\*knowledge_confidence\s*:\s*(\d+)\*\*', response).group(1)
    explanation = re.search(r'\*\*Explanation:\*\*(.*)', response, re.DOTALL).group(1).strip()


    # Print the extracted variables
    # print(f"knowledge_understood: {knowledge_understood}")
    # print(f"knowledge_confidence: {knowledge_confidence}")
    # print(f"Explanation: {explanation}")
    # # Output the results
    # print(f"knowledge_understood: {knowledge_understood}")
    # print(f"knowledge_confidence: {knowledge_confidence}")
    # print(f"Explanation: {Explanation}")

    data = {
        'knowledge_understood': knowledge_understood,
        'knowledge_confidence': knowledge_confidence,
        'Explanation': explanation,
        # 'Answers': answers
    }
    # print("Data: ", data)
    # df = pd.DataFrame(data)
    

    # engine = connect_with_db()
    # push_df_db(df, engine)
    

    return data #jsonify({'response': data})


# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

# API to handle file upload and process document
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # file.save(file_path)
        
        # # Read file content
        # file_extension = file.filename.rsplit('.', 1)[1].lower()
        # content = read_file(file_path, file_extension)
        
        file_content = file.read()

        # Determine the file extension
        file_extension = file.filename.rsplit('.', 1)[1].lower()

        # Convert file content to base64 string
        base64_content = base64.b64encode(file_content).decode('utf-8')

        # Process document with the base64 content
        response = process_document(base64_content, file_extension)
        # Process document with Vertex AI
        # response = process_document(content)
        # print("response: ", response)
        # return jsonify({'response': response})
        return jsonify(response)

    return jsonify({'error': 'File type not allowed'})

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    
    question_id = data.get('question_id')
    student_answer = data.get('answer')
    
    if not question_id or not student_answer:
        return jsonify({'error': 'Both question_id and answer are required'}), 400

    engine = connect_with_db()
    output = retrieve_from_db(question_id, engine)
    
    Bullet_Points, Questions, Answers = output[0], output[1], output[2]
    
    # print("question_id: ", question_id)
    # print("student_answer: ", student_answer)
    
    data = process_student_response(Bullet_Points, Questions, Answers, student_answer)

    # # Call to LLM for evaluation
    # model_response = generate_llm_response(question_id, answer)

    # return jsonify({'model_response': data})
    return jsonify(data)

if __name__ == '__main__':
    # Create upload folder if not exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(debug=True)
