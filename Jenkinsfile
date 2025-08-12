pipeline {
  agent any
  environment {
    REGISTRY = "ghcr.io/your/repo"
    IMAGE_TAG = "latest"
    KUBE_NAMESPACE = "ml-demo"
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Unit Tests') {
      steps {
        sh 'python -m pip install -r requirements.txt'
        // place for pytest 
      }
    }
    stage('Build Images') {
      steps {
        sh 'docker build -t $REGISTRY/orchestrator:$IMAGE_TAG orchestrator'
        sh 'docker build -t $REGISTRY/model_a:$IMAGE_TAG model_a'
        sh 'docker build -t $REGISTRY/model_b:$IMAGE_TAG model_b'
      }
    }
    stage('Push Images') {
      steps {
        sh 'docker push $REGISTRY/orchestrator:$IMAGE_TAG'
        sh 'docker push $REGISTRY/model_a:$IMAGE_TAG'
        sh 'docker push $REGISTRY/model_b:$IMAGE_TAG'
      }
    }
    stage('Deploy to K8s') {
      steps {
        sh 'kubectl apply -f k8s/manifests.yaml'
      }
    }
  }
}