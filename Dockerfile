# Start from an official Python image (slim = smaller file size)
FROM python:3.11-slim

# Set the working directory inside the container
# Think of this as "cd /app" — all commands run from here
WORKDIR /app

# Copy requirements first (before the rest of the code)
# This is a Docker best practice — it means if only your code changes
# but not your requirements, Docker skips reinstalling packages (faster)
COPY requirements.txt .

# Install all the Python packages listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your FastAPI project files into the container
COPY . .

# Tell Docker that this container listens on port 8001
# (we use 8001 so it doesn't clash with Django on 8000)
EXPOSE 8001

# The command that runs when the container starts
# uvicorn is the server that runs FastAPI (like daphne runs Django)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]