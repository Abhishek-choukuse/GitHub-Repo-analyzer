# official Python base image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory in container
WORKDIR /app

# Copy dependency file and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . /app/

# Expose the port Django will run on
EXPOSE 5000

# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:5000"]
