def runCI() {

    // 1. Clean Workspace
    stage('Clean Workspace') {
        try {
            cleanWs()
        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: Clean Workspace'
            throw e
        }
    }

    // 2. Checkout SCM
    stage('Checkout SCM') {
        try {
            echo 'Checking out source code from GitHub...'
            checkout scm
        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: Checkout SCM'
            throw e
        }
    }

    // 3. Unit Testing & Coverage
    stage('Unit Testing & Coverage') {
        try {
            echo 'Setting up Python environment and running unit tests...'

            sh '''
                set -e

                python3 -m venv venv
                . venv/bin/activate

                python -m pip install --upgrade pip
                pip install -r requirements.txt
                pip install pytest pytest-cov

                pytest test/ \
                    --junitxml=test-results.xml \
                    --cov=Application-Source-Code \
                    --cov-report=xml:coverage.xml \
                    --cov-report=term-missing
            '''

        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: Unit Testing & Coverage'
            throw e
        } finally {
            junit allowEmptyResults: true,
                  testResults: 'test-results.xml'
        }
    }

    // 4. Docker Linting

    
    stage('Docker Linting') {
        try {
            echo 'Running Hadolint on all Dockerfiles...'
    
            sh '''
                docker run --rm \
                    --entrypoint hadolint \
                    -v "$WORKSPACE:/workspace" \
                    -w /workspace \
                    hadolint/hadolint \
                    --format sonarqube \
                    dockerfiles/*.Dockerfile \
                    > hadolint-report.json 2>&1 || true
            '''
    
        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: Docker Linting'
            throw e
    
        } finally {
            archiveArtifacts artifacts: 'hadolint-report.json',
                             allowEmptyArchive: true
        }
    }

    
    

    // 5. SonarQube SAST
    stage('SAST - SonarQube Analysis') {
        try {
            echo 'Starting SonarQube SAST scan...'

            def scannerHome = tool 'SonarScanner'

            withSonarQubeEnv('demo_sonarqube') {
                sh "${scannerHome}/bin/sonar-scanner"
            }

        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: SAST - SonarQube Analysis'
            throw e
        }
    }

    // 6. Quality Gate
    stage('Quality Gate Check') {
        try {
            timeout(time: 3, unit: 'MINUTES') {

                def qg = waitForQualityGate()

                echo "SonarQube Quality Gate Status: ${qg.status}"

                if (qg.status != 'OK') {
                    error "Pipeline stopped: SonarQube Quality Gate failed: ${qg.status}"
                }
            }

        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: Quality Gate Check'
            throw e
        }
    }

    // 7. Dependency Scan
    stage('Dependency Scan') {
        try {
            echo 'Running Trivy Dependency Scan...'

            sh """
                set -e

                docker run --rm \
                    -v "\${WORKSPACE}:/apps" \
                    -w /apps \
                    aquasec/trivy fs \
                    --scanners vuln \
                    --severity LOW,MEDIUM,HIGH,CRITICAL \
                    --format template \
                    --template '@/contrib/html.tpl' \
                    --output dependency_report_${BUILD_NUMBER}.html \
                    requirements.txt

                docker run --rm \
                    -v "\${WORKSPACE}:/apps" \
                    -w /apps \
                    aquasec/trivy fs \
                    --scanners vuln \
                    --severity HIGH,CRITICAL \
                    --ignore-unfixed \
                    --exit-code 1 \
                    --quiet \
                    requirements.txt
            """

        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: Dependency Scan'
            throw e
        } finally {
            archiveArtifacts artifacts: 'dependency_report_*.html',
                             allowEmptyArchive: true
        }
    }

    // 8. Build Docker Images
    stage('Build Docker Image') {
        try {
            def services = [
                'backend',
                'success',
                'signup',
                'login',
                'ingress'
            ]

            for (String service : services) {
                echo "Building ${service} image..."

                sh """
                    docker build \
                        -t rganesh7/${service}-1026:${BUILD_NUMBER} \
                        -f dockerfiles/${service}.Dockerfile .
                """
            }

        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: Build Docker Image'
            throw e
        }
    }

    // 9. Trivy Image Scanning
    stage('Trivy Image Scanning..') {
        try {
            def services = [
                'backend',
                'success',
                'signup',
                'login',
                'ingress'
            ]

            for (String service : services) {
                echo "Scanning ${service} image..."

                sh """
                    set -e

                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v "\${WORKSPACE}:/apps" \
                        -v "\$HOME/.cache/trivy:/root/.cache/" \
                        -w /apps \
                        aquasec/trivy image \
                        --severity LOW,MEDIUM,HIGH,CRITICAL \
                        --format template \
                        --template '@/contrib/html.tpl' \
                        --output Trivy_Img_Scan-${service}-report_${BUILD_NUMBER}.html \
                        rganesh7/${service}-1026:${BUILD_NUMBER}

                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v "\$HOME/.cache/trivy:/root/.cache/" \
                        aquasec/trivy image \
                        --severity HIGH,CRITICAL \
                        --ignore-unfixed \
                        --exit-code 0 \
                        --quiet \
                        rganesh7/${service}-1026:${BUILD_NUMBER}
                """
            }

        } catch (Exception e) {
            echo '[PIPELINE FAILURE] Failed at stage: Trivy Image Scanning'
            throw e
        } finally {
            archiveArtifacts artifacts: 'Trivy_Img_Scan-*-report_*.html',
                             allowEmptyArchive: true
        }
    }

    // 10. Promote & Push
    // Skip publishing from PR builds for credential safety.
    if (!env.CHANGE_ID) {

        stage('Promote & Push to Registry') {
            try {
                def services = [
                    'backend',
                    'success',
                    'signup',
                    'login',
                    'ingress'
                ]

                docker.withRegistry(
                    'https://index.docker.io/v1/',
                    'docker-credentials'
                ) {
                    for (String service : services) {

                        sh """
                            docker tag \
                                rganesh7/${service}-1026:${BUILD_NUMBER} \
                                rganesh7/${service}-1026:latest

                            docker push \
                                rganesh7/${service}-1026:${BUILD_NUMBER}

                            docker push \
                                rganesh7/${service}-1026:latest
                        """
                    }
                }

            } catch (Exception e) {
                echo '[PIPELINE FAILURE] Failed at stage: Promote & Push'
                throw e
            }
        }

        // 11. Cosign Image Signing
        stage('Sign Image') {
            try {
                withCredentials([
                    file(
                        credentialsId: 'cosign-private-key',
                        variable: 'COSIGN_KEY'
                    ),
                    string(
                        credentialsId: 'cosign-passphrase',
                        variable: 'COSIGN_PASSWORD'
                    )
                ]) {

                    def services = [
                        'backend',
                        'success',
                        'signup',
                        'login',
                        'ingress'
                    ]

                    for (String service : services) {

                        echo "Signing ${service} images..."

                        sh """
                            cosign sign --key "\$COSIGN_KEY" \
                                rganesh7/${service}-1026:latest

                            cosign sign --key "\$COSIGN_KEY" \
                                rganesh7/${service}-1026:${BUILD_NUMBER}
                        """
                    }
                }

            } catch (Exception e) {
                echo '[PIPELINE FAILURE] Failed at stage: Sign Image'
                throw e
            }
        }

    } else {
        echo 'PR build: skipping Docker push and Cosign signing.'
    }

    echo 'CI pipeline completed.'
}

return this
