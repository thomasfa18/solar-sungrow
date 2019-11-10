# Use an official Python runtime as a parent image
FROM python:3.7-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

#include the config mount point in pythonpath
ENV PYTHONPATH="/config:$PYTHONPATH"

#TODO:
# would be better to Add ENV and ENTRYPOINTs for the files rather than rely on pythonpath. could just pass mounth point directories such as config and logs

# Run app.py when the container launches
CMD ["python", "sungrow_monitor.py"]