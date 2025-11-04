FROM python:3.11-slim
WORKDIR /app
COPY extract_bus_routes.py .
RUN mkdir -p /app/input /app/output
ENV PYTHONUNBUFFERED=1
CMD ["python", "extract_bus_routes.py"]
