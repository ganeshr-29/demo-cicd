pipeline {
    agent any 
    options {
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }

    stages {

        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Checkout SCM') {
            steps {
                echo 'Checking out source code from GitHub...'
                checkout scm
            }
        }

        stage('Unit Testing & Coverage') {
            steps {
                echo 'Setting up Python environment and running unit tests...'
                sh '''
                    # Create and activate virtual environment
                    sudo apt update
                    sudo apt install -y python3.14-venv python3-pip
                    python3 -m venv venv
                    . venv/bin/activate

                    # Install project dependencies and test tools
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-cov

                    # Run tests with JUnit and Cobertura XML outputs for Jenkins and SonarQube
                    pytest test/ \
                        --junitxml=test-results.xml \
                        --cov=Application-Source-Code \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing
                '''
            }
            post {
                always {
                    // Publishes test result graphs on the Jenkins build page
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                    // Clean up virtual environment directory to save agent disk space
                }
            }
        }

        stage('Docker Linting') {
            steps {
                echo 'Running Hadolint on all Dockerfiles...'
                sh '''
                    # Run hadolint over the entire dockerfiles directory and write valid sonarqube json
                    docker run --rm \
                      -v "${WORKSPACE}:/workspace" \
                      -w /workspace \
                      hadolint/hadolint hadolint --format sonarqube dockerfiles/* > hadolint-report.json || true
                '''
            }
        }

        stage('SAST - SonarQube Analysis') {
            steps {
                echo 'Starting SonarQube SAST scan...'
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('demo_sonarqube') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Quality Gate Check') {
            steps {
                timeout(time: 3, unit: 'MINUTES') {
                    script {
                        // Pauses pipeline until SonarQube finishes computing and sends the webhook callback
                        def qg = waitForQualityGate()
                        echo "SonarQube Quality Gate Status: ${qg.status}"

                        if (qg.status != 'OK') {
                            error "Pipeline stopped: SonarQube Quality Gate failed with status: ${qg.status}"
                        }
                    }
                }
            }
        }


        



    }
}

