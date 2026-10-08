pipeline {
    agent any 
    options {
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitHub...'
                // Jenkins automatically clones your repo if this file is run via "Pipeline from SCM"
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

                    # Display the report contents in Jenkins console logs
                    cat hadolint-report.json
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

        // stage('Quality Gate Check') {
        //     steps {
        //         timeout(time: 3, unit: 'MINUTES') {
        //             script {
        //                 // Pauses pipeline until SonarQube finishes computing and sends the webhook callback
        //                 def qg = waitForQualityGate()
        //                 echo "SonarQube Quality Gate Status: ${qg.status}"

        //                 if (qg.status != 'OK') {
        //                     error "Pipeline stopped: SonarQube Quality Gate failed with status: ${qg.status}"
        //                 }
        //             }
        //         }
        //     }
        // }


        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }
    }
}

