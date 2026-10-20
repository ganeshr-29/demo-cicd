pipeline {
    agent any

    options {
        timeout(time: 10, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DEPLOY_HOST = '13.233.111.36'
        DEPLOY_USER = 'ubuntu'
        DEPLOY_DIR  = '/home/ubuntu/demo-proj'
    }

    stages {
        stage('Verify Image Signatures (Cosign)') {
            steps {
                withCredentials([
                    file(credentialsId: 'cosign-public-key', variable: 'COSIGN_PUB_KEY')
                ]) {
                    script {
                        def services = ['backend', 'success', 'signup', 'login', 'ingress']

                        for (int i = 0; i < services.size(); i++) {
                            String currentService = services[i]
                            echo "Verifying Cosign signature for rganesh7/${currentService}-1026:latest..."

                            sh """
                                cosign verify --key "\$COSIGN_PUB_KEY" rganesh7/${currentService}-1026:latest
                            """
                        }
                    }
                }
            }
            post {
                failure {
                    echo "=========================================================================================================="
                    echo "[PIPELINE FAILURE] Failed at stage: Verify Image Signatures (Untrusted, modified, or unsigned image detected)"
                    echo "=========================================================================================================="
                }
            }
        }

        stage('Deploy via Docker Compose') {
            steps {
                echo "Triggering deployment on remote host: ${DEPLOY_HOST}..."
                sshagent(['Deployment_Server']) {
                    sh """
                        # Automate host key verification
                        mkdir -p ~/.ssh
                        chmod 700 ~/.ssh
                        touch ~/.ssh/known_hosts
                        chmod 600 ~/.ssh/known_hosts
                        ssh-keyscan -H ${DEPLOY_HOST} >> ~/.ssh/known_hosts

                        # Execute Docker Compose directly inside the deployment directory
                        ssh ${DEPLOY_USER}@${DEPLOY_HOST} << 'EOF'
                            cd ${DEPLOY_DIR}

                            echo "Pulling latest signed images..."
                            docker compose pull

                            echo "Recreating running containers..."
                            docker compose up -d --remove-orphans

                            echo "Pruning older dangling images..."
                            docker image prune -f
EOF
                    """
                }

                echo "Waiting 2 minutes for containers and database initialization to complete..."
                sleep time: 2, unit: 'MINUTES'

                echo "Inspecting running status for all containers on ${DEPLOY_HOST}..."
                sshagent(['Deployment_Server']) {
                    sh """
                        ssh ${DEPLOY_USER}@${DEPLOY_HOST} << 'EOF'
                            cd ${DEPLOY_DIR}

                            echo "================ Current Container Status ================"
                            docker compose ps --all --format "table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.State}}"
                            echo "=========================================================="

                            # Count defined services vs containers actively running
                            TOTAL_SERVICES=\$(docker compose config --services | wc -l)
                            RUNNING_SERVICES=\$(docker compose ps --status running -q | wc -l)

                            echo "Total expected services : \${TOTAL_SERVICES}"
                            echo "Currently running       : \${RUNNING_SERVICES}"

                            if [ "\${RUNNING_SERVICES}" -ne "\${TOTAL_SERVICES}" ]; then
                                echo "=========================================================="
                                echo "ERROR: Not all containers are in 'running' state!"
                                echo "Non-running container details:"
                                docker compose ps --all --filter "status=exited" --filter "status=dead" --filter "status=restarting" --filter "status=created"
                                echo "---------------------- Error Logs ------------------------"
                                docker compose logs --tail=40
                                echo "=========================================================="
                                exit 1
                            fi

                            echo "SUCCESS: All \${TOTAL_SERVICES} containers are confirmed running!"
EOF
                    """
                }
            }
            post {
                failure {
                    echo "========================================================================================================"
                    echo "[PIPELINE FAILURE] Failed at stage: Deploy via Docker Compose (Deployment or Container Status Check Failed)"
                    echo "========================================================================================================"
                }
            }
        }
    }

    post {
        success {
            echo "=========================================================================="
            echo "SUCCESS: Verified signatures, deployed, and confirmed all containers are running."
            echo "=========================================================================="
        }
        failure {
            echo "=========================================================================="
            echo "CD PIPELINE FAILED: Check the failing stage above for details."
            echo "=========================================================================="
        }
    }
}