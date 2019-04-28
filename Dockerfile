# Use an official Python runtime as a parent image
FROM python:2.7-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

#include the config mount point in pythonpath
ENV PYTHONPATH="/config:$PYTHONPATH"

# Run app.py when the container launches
CMD ["python", "sungrow_monitor.py"]