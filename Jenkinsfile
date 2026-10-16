// Declarative Jenkins pipeline for the Student Management System.
// Target: Windows (uses 'bat' steps). One command per bat step so that
// a failing command always fails the stage.

pipeline {
    agent any

    options {
        skipDefaultCheckout(true)                       // we checkout in our own stage
        buildDiscarder(logRotator(numToKeepStr: '10'))  // keep the last 10 builds
    }

    environment {
        VENV_DIR   = '.venv'
        DEPLOY_DIR = 'C:\\StudentManagementSystem_Deploy'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                bat 'dir /b'
            }
        }

        stage('Setup Python Environment') {
            steps {
                bat 'python --version'
                bat 'python -m venv %VENV_DIR%'
            }
        }

        stage('Install Dependencies') {
            steps {
                // Installs Flask (needed for the website tests). Needs internet access.
                bat '%VENV_DIR%\\Scripts\\python -m pip install -r requirements.txt'
            }
        }

        stage('Run Automated Tests') {
            steps {
                // If any test fails, unittest exits with an error code,
                // this stage fails, and the Deployment Preparation stage is skipped.
                bat '%VENV_DIR%\\Scripts\\python -m unittest discover -s . -p "test_*.py" -v'
            }
        }

        stage('Deployment Preparation') {
            steps {
                // Copies application files to DEPLOY_DIR. Never touches student data.
                bat 'call deploy.bat "%DEPLOY_DIR%"'
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
