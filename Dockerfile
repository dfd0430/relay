FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy pyproject.toml and poetry.lock first to leverage Docker cache
COPY pyproject.toml .

# Install Poetry
RUN pip install poetry

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code
COPY . .

# Copy templates folder explicitly if not caught by .
COPY templates ./templates

# Expose the Flask port
EXPOSE 8080

# Set the command to run the application
CMD ["poetry", "run", "python", "app.py"]
