# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variables (these should be set at runtime, not in the Dockerfile)
# ENV SUPABASE_URL=your_supabase_url
# ENV SUPABASE_KEY=your_supabase_key
# ENV OPENAI_API_KEY=your_openai_api_key
# ENV REDDIT_CLIENT_ID=your_reddit_client_id
# ENV REDDIT_SECRET_KEY=your_reddit_secret_key
# ENV NEWSAPI_CLIENT_ID=your_newsapi_client_id

# Run app.py when the container launches
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
