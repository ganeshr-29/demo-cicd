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
            post {
                failure {
                    echo "==================================================="
                    echo "[PIPELINE FAILURE] Failed at stage: Clean Workspace"
                    echo "==================================================="
                }
            }
        }

        stage('Checkout SCM') {
            steps {
                echo 'Checking out source code from GitHub...'
                checkout scm
            }
            post {
                failure {
                    echo "============================================================================"
                    echo "[PIPELINE FAILURE] Failed at stage: Checkout SCM (Unable to pull repository)"
                    echo "============================================================================"
                }
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
                // always {
                //     // Publishes test result graphs on the Jenkins build page
                //     junit allowEmptyResults: true, testResults: 'test-results.xml'
                // }
                failure {
                    echo "==========================================================="
                    echo "[PIPELINE FAILURE] Failed at stage: Unit Testing & Coverage"
                    echo "==========================================================="
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
            post {
                failure {
                    echo "=================================================="
                    echo "[PIPELINE FAILURE] Failed at stage: Docker Linting"
                    echo "=================================================="
                }
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
            post {
                failure {
                    echo "========================================================================================"
                    echo "[PIPELINE FAILURE] Failed at stage: SAST - SonarQube Analysis (Scanner execution failed)"
                    echo "========================================================================================"
                }
            }
        }

        stage('Quality Gate Check') {
            steps {
                timeout(time: 3, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        echo "SonarQube Quality Gate Status: ${qg.status}"

                        if (qg.status != 'OK') {
                            error "Pipeline stopped: SonarQube Quality Gate failed with status: ${qg.status}"
                        }
                    }
                }
            }
            post {
                failure {
                    echo "======================================================================================================="
                    echo "[PIPELINE FAILURE] Failed at stage: Quality Gate Check (Project failed to meet Quality Gate conditions)"
                    echo "======================================================================================================="
                }
            }
        }

        stage('Dependency Scan') {
            steps {
                script {
                    echo "Running Trivy Dependency Scan..."
                    sh """
                        docker run --rm \
                        -v \$(pwd):/apps \
                        -w /apps \
                        --entrypoint sh \
                        aquasec/trivy -c "
                            echo '1. Generating combined HTML report for ALL severities...' && \
                            trivy fs --scanners vuln --severity LOW,MEDIUM,HIGH,CRITICAL --format template --template '@/contrib/html.tpl' --output dependency_report_${BUILD_NUMBER}.html requirements.txt && \
                            echo '2. Enforcing pipeline gates for HIGH and CRITICAL vulnerabilities...' && \
                            trivy fs --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 --quiet requirements.txt
                        "
                    """
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'dependency_report_*.html', allowEmptyArchive: true
                }
                failure {
                    echo "======================================================================================================="
                    echo "[PIPELINE FAILURE] Failed at stage: Dependency Scan (High or Critical CVE detected in requirements.txt)"
                    echo "======================================================================================================="
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def images = ['backend', 'success', 'signup', 'login', 'ingress']
                    for (service in images) {
                        echo "Building and tagging ${service} image with Build Number..."
                        sh "docker build -t rganesh7/${service}-1026:${BUILD_NUMBER} -f dockerfiles/${service}.Dockerfile ."
                    }
                }
            }
            post {
                failure {
                    echo "=============================================================================================================="
                    echo "[PIPELINE FAILURE] Failed at stage: Build Docker Image (Docker build step encountered a syntax or layer error)"
                    echo "=============================================================================================================="
                }
            }
        }

        // stage('Build Docker Image') {
        //     steps {
        //         echo "Building and tagging backend image with Build Number..."
        //         sh "docker build -t rganesh7/backend-1026:${BUILD_NUMBER} -f dockerfiles/backend.Dockerfile ."
        //         echo "Building and tagging success image with Build Number..."
        //         sh "docker build -t rganesh7/success-1026:${BUILD_NUMBER} -f dockerfiles/success.Dockerfile ."
        //         echo "Building and tagging signup image with Build Number..."
        //         sh "docker build -t rganesh7/signup-1026:${BUILD_NUMBER} -f dockerfiles/signup.Dockerfile ."
        //         echo "Building and tagging login image with Build Number..."
        //         sh "docker build -t rganesh7/login-1026:${BUILD_NUMBER} -f dockerfiles/login.Dockerfile ."
        //         echo "Building and tagging ingress image with Build Number..."
        //         sh "docker build -t rganesh7/ingress-1026:${BUILD_NUMBER} -f dockerfiles/ingress.Dockerfile ."
        //     }
        // }

        stage('Trivy Image Scanning..') {
            steps {
                script {
                    def services = ['backend', 'success', 'signup', 'login', 'ingress']
                    
                    for (int i = 0; i < services.size(); i++) {
                        String currentService = services[i]
                        
                        echo "Scanning ${currentService} using a shared host cache..."
                        sh """
                            docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock:ro \
                            -v \$(pwd):/apps \
                            -v \$HOME/.cache/trivy:/root/.cache/ \
                            -w /apps \
                            --entrypoint sh \
                            aquasec/trivy -c "
                                trivy image --severity LOW,MEDIUM,HIGH,CRITICAL --format template --template '@/contrib/html.tpl' --output Trivy_Img_Scan-${currentService}-report_${BUILD_NUMBER}.html rganesh7/${currentService}-1026:${BUILD_NUMBER} && \
                                trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 0 --quiet rganesh7/${currentService}-1026:${BUILD_NUMBER}
                            "
                        """
                    }
                }
            }
            post {
                always {
                    // Preserves HTML reports even when Trivy exits with 1
                    archiveArtifacts artifacts: 'Trivy_Img_Scan-*-report_*.html', allowEmptyArchive: true
                }
                failure {
                    echo "======================================================================================================================"
                    echo "[PIPELINE FAILURE] Failed at stage: Trivy Image Scanning (High/Critical unpatched vulnerability found in built images)"
                    echo "======================================================================================================================"
                }
            }
        }

        stage('Promote & Push to Registry') {
            steps {
                script {
                    def services = ['backend', 'success', 'signup', 'login', 'ingress']
                    docker.withRegistry('https://index.docker.io/v1/', 'docker-credentials') {
                        
                        for (int i = 0; i < services.size(); i++) {
                            String currentService = services[i]
                            
                            sh "docker tag rganesh7/${currentService}-1026:${BUILD_NUMBER} rganesh7/${currentService}-1026:latest"
                            sh "docker push rganesh7/${currentService}-1026:${BUILD_NUMBER}"
                            sh "docker push rganesh7/${currentService}-1026:latest"
                        }
                    }
                }
            }
            post {
                failure {
                    echo "============================================================================================"
                    echo "[PIPELINE FAILURE] Failed at stage: Promote & Push to Registry (Docker login or push failed)"
                    echo "============================================================================================"
                }
            }
        }

        stage('Sign Image') {
            steps {
                // Inject the private key and passphrase from Jenkins credentials
                withCredentials([
                    file(credentialsId: 'cosign-private-key', variable: 'COSIGN_KEY'),
                    string(credentialsId: 'cosign-passphrase', variable: 'COSIGN_PASSWORD')
                ]) {
                    script {
                        def services = ['backend', 'success', 'signup', 'login', 'ingress']

                        docker.withRegistry('https://index.docker.io/v1/', 'docker-credentials') {
                            for (int i = 0; i < services.size(); i++) {
                                String currentService = services[i]
                                echo "Signing ${currentService} images (latest and build ${BUILD_NUMBER})..."

                                sh """
                                    cosign sign --key "\$COSIGN_KEY" rganesh7/${currentService}-1026:latest
                                    cosign sign --key "\$COSIGN_KEY" rganesh7/${currentService}-1026:${BUILD_NUMBER}
                                """
                            }
                        }
                    }
                }
            }
            post {
                failure {
                    echo "==================================================================================="
                    echo "[PIPELINE FAILURE] Failed at stage: Sign Image (Cosign signature generation failed)"
                    echo "==================================================================================="
                }
            }
        }

        // stage('Sign Image') {
        //     steps {
        //         // Inject the private key and passphrase from Jenkins credentials
        //         withCredentials([
        //             file(credentialsId: 'cosign-private-key', variable: 'COSIGN_KEY'),
        //             string(credentialsId: 'cosign-passphrase', variable: 'COSIGN_PASSWORD')
        //         ]) {
        //             script {
        //                 docker.withRegistry('https://index.docker.io/v1/', 'docker-credentials') {
        //                     sh "cosign sign --key \$COSIGN_KEY rganesh7/backend-1026:latest"
        //                     sh "cosign sign --key \$COSIGN_KEY rganesh7/backend-1026:${BUILD_NUMBER}"
        //                 }
        //             }
        //         }
        //     }
        //     post {
        //         failure {
        //             echo "==================================================================================="
        //             echo "[PIPELINE FAILURE] Failed at stage: Sign Image (Cosign signature generation failed)"
        //             echo "==================================================================================="
        //         }
        //     }
        // }
    }
    post {
        success {
            echo "======================================================================================="
            echo "SUCCESS: Pipeline completed all security checks, tests, builds, pushes, and signatures."
            echo "======================================================================================="
        }
        failure {
            echo "================================================================================"
            echo "================================================================================"
            echo "BUILD FAILED: Review the stage marked above with [PIPELINE FAILURE] for details."
            echo "================================================================================"
            echo "================================================================================"
        }
    }
}


        // stage('Trivy Image Scanning..') {
        //     steps {
        //         script {
        //             echo "Running both Trivy actions inside a single container instance..."
                    
        //             sh """
        //                 docker run --rm \
        //                 -v /var/run/docker.sock:/var/run/docker.sock:ro \
        //                 -v \$(pwd):/apps \
        //                 -w /apps \
        //                 --entrypoint sh \
        //                 aquasec/trivy -c "
        //                     echo '1. Generating HTML report...' && \
        //                     trivy image --severity LOW,MEDIUM,HIGH,CRITICAL --format template --template '@/contrib/html.tpl' --output image-scan_report.html rganesh7/backend-1026:109 && \
        //                     echo '2. Enforcing pipeline validation gate...' && \
        //                     trivy image --severity HIGH,CRITICAL --exit-code 0 --quiet rganesh7/backend-1026:109
        //                 "
        //             """
        //         }
        //     }
        // }