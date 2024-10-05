# Nurovant

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
