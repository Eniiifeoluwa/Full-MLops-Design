.PHONY: help install train run docker-build docker-run test clean

help:
	@echo "ML Inference Service - Available Commands"
	@echo "=========================================="
	@echo "install       - Install Python dependencies"
	@echo "train         - Train the ML model"
	@echo "run           - Run the service locally"
	@echo "docker-build  - Build Docker image"
	@echo "docker-run    - Run Docker container"
	@echo "test          - Run API tests"
	@echo "k8s-deploy    - Deploy to Kubernetes"
	@echo "k8s-delete    - Delete from Kubernetes"
	@echo "clean         - Clean up generated files"

install:
	pip install -r requirements.txt

train:
	python train_model.py

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t ml-inference-service:1.0.0 .

docker-run:
	docker run -p 8000:8000 ml-inference-service:1.0.0

test:
	@echo "Running API tests..."
	@chmod +x examples/test_requests.sh
	@./examples/test_requests.sh

k8s-deploy:
	kubectl apply -f k8s/

k8s-delete:
	kubectl delete -f k8s/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true