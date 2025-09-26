FROM public.ecr.aws/lambda/python:3.12

# Copy requirements and install dependencies
COPY services/ingest-svc/pyproject.toml ${LAMBDA_TASK_ROOT}/
RUN pip install --upgrade pip && pip install fastapi uvicorn boto3 opensearch-py pydantic-settings jsonschema opentelemetry-api opentelemetry-sdk structlog

# Copy application code
COPY services/ingest-svc/app ${LAMBDA_TASK_ROOT}/app
COPY shared ${LAMBDA_TASK_ROOT}/shared
COPY contracts ${LAMBDA_TASK_ROOT}/contracts

# Set the CMD to your handler
CMD ["app.lambda_handler.handler"]


