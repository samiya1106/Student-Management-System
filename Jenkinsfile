
pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        VENV_DIR = '.venv'
        DEPLOY_DIR = 'deploy'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh 'python3 --version'
                sh 'python3 -m venv "$VENV_DIR"'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '"$VENV_DIR/bin/python" -m pip install -r requirements.txt'
            }
        }

        stage('Run Automated Tests') {
            steps {
                sh '"$VENV_DIR/bin/python" -m unittest discover -s . -p "test_*.py" -v'
            }
        }

        stage('Deployment Preparation') {
            steps {
                sh 'mkdir -p "$DEPLOY_DIR"'
                sh 'cp -r app.py student_management.py requirements.txt templates static "$DEPLOY_DIR"/'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: All tests passed and deployment folder was prepared.'
        }
        failure {
            echo 'FAILURE: A stage failed. Check the Console Output for the first error.'
        }
        always {
            echo "Pipeline finished. Result: ${currentBuild.currentResult}"
        }
    }
}
