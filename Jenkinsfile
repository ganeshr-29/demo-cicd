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
        sh '''
            # Initialize an empty SonarQube generic issues JSON
            echo '{"issues": []}' > hadolint-report.json

            # Loop through all files inside dockerfiles/ directory
            for df in dockerfiles/*; do
                if [ -f "$df" ]; then
                    echo "Linting $df..."
                    docker run --rm -i hadolint/hadolint hadolint --format sonarqube - < "$df" > "${df}.json" || true
                fi
            done

            # Combine all issue JSON files using jq if installed, or lint each directly
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


        // stage('Clean Workspace') {
        //     steps {
        //         cleanWs()
        //     }
        // }
    }
}

