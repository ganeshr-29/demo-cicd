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
                        // def qg = waitForQualityGate()
                        // echo "SonarQube Quality Gate Status: ${qg.status}"

                        // if (qg.status != 'OK') {
                        //     error "Pipeline stopped: SonarQube Quality Gate failed with status: ${qg.status}"
                        // }

                        def qg = waitForQualityGate()

                        if (qg.status != 'OK') {
                            updateGithubStatus('failure', 'Quality Gate failed - click Details to view errors')
                            error "Quality Gate failed: ${qg.status}"
                        } else {
                            updateGithubStatus('success', 'Quality Gate passed cleanly')
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
    post {
        always {
            echo 'Pipeline has finished executing.'
            }
        success {
            echo 'Build completed successfully! 🎉'
        }
        failure {                
            echo 'Build failed. Please check the logs. ❌'
        }
    }
}


def updateGithubStatus(String state, String description) {
    def commitSha = env.GIT_COMMIT ?: sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
    def remoteUrl = sh(returnStdout: true, script: 'git config --get remote.origin.url').trim()
    def repoSlug  = (remoteUrl =~ /github\.com[:\/]([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+?)(?:\.git)?$/)[0][1]

    sh """
        curl -s -X POST \
            -H "Authorization: token ${GITHUB_TOKEN}" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/${repoSlug}/statuses/${commitSha}" \
            -d '{
                "state": "${state}",
                "target_url": "${env.SONAR_URL}",
                "description": "${description}",
                "context": "SonarQube Quality Gate"
            }'
    """
}