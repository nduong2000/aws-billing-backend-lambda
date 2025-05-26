# Use the official AWS Lambda Python runtime
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements file first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install -r requirements.txt --target . --no-cache-dir

# Copy all application files
COPY lambda_function.py ./
COPY routes/ ./routes/
COPY config/ ./config/

# Create __init__.py files to make directories proper Python packages
RUN touch ./routes/__init__.py
RUN touch ./config/__init__.py

# Verify the platform and architecture
RUN echo "Platform: $(uname -m)" && echo "Architecture: $(arch)"

# Set the CMD to your handler (this is the entry point)
CMD [ "lambda_function.lambda_handler" ]