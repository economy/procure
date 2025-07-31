# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv, the Python package installer
RUN pip install uv

# Copy the dependency files to the working directory
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --no-cache

# Copy the rest of the application's code to the working directory
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Use 'uv run' to execute the command in the correct environment
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
