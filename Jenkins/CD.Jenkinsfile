
def runCD() {

    def DEPLOY_HOST = '43.205.113.174'
    def DEPLOY_USER = 'ubuntu'
    def DEPLOY_DIR  = '/home/ubuntu/demo-proj'

    try {

        // ==========================================================
        // Stage 1: Verify Image Signatures
        // ==========================================================
        stage('Verify Image Signatures (Cosign)') {

            try {

                withCredentials([
                    file(credentialsId: 'cosign-public-key',
                         variable: 'COSIGN_PUB_KEY')
                ]) {

                    def services = [
                        'backend',
                        'success',
                        'signup',
                        'login',
                        'ingress'
                    ]

                    for (String currentService : services) {

                        echo "Verifying Cosign signature for rganesh7/${currentService}-1026:latest..."

                        sh """
                            cosign verify --key "\$COSIGN_PUB_KEY" rganesh7/${currentService}-1026:latest
                        """
                    }
                }

            } catch (Exception e) {

                echo "=========================================================================================================="
                echo "[PIPELINE FAILURE] Failed at stage: Verify Image Signatures (Untrusted, modified, or unsigned image detected)"
                echo "=========================================================================================================="

                throw e
            }
        }


        // ==========================================================
        // Stage 2: Deploy via Docker Compose
        // ==========================================================
        stage('Deploy via Docker Compose') {

            try {

                echo "Triggering deployment on remote host: ${DEPLOY_HOST}..."

                sshagent(['Deployment_Server']) {

                    sh """
                        set -e

                        mkdir -p ~/.ssh
                        chmod 700 ~/.ssh
                        touch ~/.ssh/known_hosts
                        chmod 600 ~/.ssh/known_hosts

                        ssh-keyscan -H ${DEPLOY_HOST} >> ~/.ssh/known_hosts

                        ssh ${DEPLOY_USER}@${DEPLOY_HOST} << 'EOF'
                            set -e

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


                // Wait for application and database initialization
                echo "Waiting 1 minute for containers and database initialization..."
                sleep(time: 1, unit: 'MINUTES')


                // ==================================================
                // Stage 3: Verify Container Status
                // ==================================================
                echo "Inspecting running status for containers on ${DEPLOY_HOST}..."

                sshagent(['Deployment_Server']) {

                    sh """
                        ssh ${DEPLOY_USER}@${DEPLOY_HOST} << 'EOF'
                            set -e

                            cd ${DEPLOY_DIR}

                            echo "================ Current Container Status ================"
                            docker compose ps --all
                            echo "=========================================================="

                            TOTAL_SERVICES=\$(docker compose config --services | sort -u | wc -l)

                            RUNNING_SERVICES=\$(docker compose ps --services --filter status=running | sort -u | wc -l)

                            echo "Total expected services : \${TOTAL_SERVICES}"
                            echo "Currently running       : \${RUNNING_SERVICES}"

                            if [ "\${RUNNING_SERVICES}" -ne "\${TOTAL_SERVICES}" ]; then

                                echo "=========================================================="
                                echo "ERROR: Not all services are running!"

                                echo "Container details:"
                                docker compose ps --all

                                echo "---------------------- Error Logs ------------------------"
                                docker compose logs --tail=40

                                echo "=========================================================="

                                exit 1
                            fi

                            echo "SUCCESS: All \${TOTAL_SERVICES} services are confirmed running!"
EOF
                    """
                }

            } catch (Exception e) {

                echo "========================================================================================================"
                echo "[PIPELINE FAILURE] Failed at stage: Deploy via Docker Compose (Deployment or Container Status Check Failed)"
                echo "========================================================================================================"

                throw e
            }
        }


        // ==========================================================
        // Pipeline Success
        // ==========================================================
        echo "=========================================================================="
        echo "SUCCESS: Verified signatures, deployed, and confirmed all containers are running."
        echo "=========================================================================="

    } catch (Exception e) {

        echo "=========================================================================="
        echo "CD PIPELINE FAILED: Check the failing stage above for details."
        echo "=========================================================================="

        throw e
    }
}

return this
