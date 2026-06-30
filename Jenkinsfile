pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        BACKEND_DIR = 'Backend'
        FRONTEND_DIR = 'Frontend'
        REPORT_DIR = 'build-reports'
        SONAR_HOST_URL = 'http://sonarqube:9000'
        SONAR_PROJECT_KEY = 'urbanbank'
        SONAR_SCANNER_NPM_PACKAGE = '@sonar/scan@4.3.5'
        VENV_DIR = '.venv'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Project Snapshot') {
            steps {
                sh '''
                    set -eux
                    mkdir -p "$REPORT_DIR"

                    python3 --version | tee "$REPORT_DIR/tool-versions.txt"
                    node --version | tee -a "$REPORT_DIR/tool-versions.txt"
                    npm --version | tee -a "$REPORT_DIR/tool-versions.txt"
                    git --version | tee -a "$REPORT_DIR/tool-versions.txt"

                    test -f "$BACKEND_DIR/requirements.txt"
                    test -f "$FRONTEND_DIR/package.json"

                    {
                        echo "Build number: ${BUILD_NUMBER}"
                        echo "Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
                        echo "Backend Python files: $(find "$BACKEND_DIR" -name '*.py' | wc -l)"
                        echo "Frontend source files: $(find "$FRONTEND_DIR/src" -type f | wc -l)"
                    } | tee "$REPORT_DIR/pipeline-summary.txt"
                '''
            }
        }

        stage('Backend Dependencies') {
            steps {
                sh '''
                    set -eux
                    rm -rf "$VENV_DIR"
                    python3 -m venv "$VENV_DIR"
                    . "$VENV_DIR/bin/activate"
                    python -m pip install --upgrade pip
                    python -m pip install -r "$BACKEND_DIR/requirements.txt"
                '''
            }
        }

        stage('Backend Verify') {
            steps {
                sh '''
                    set -eux
                    . "$VENV_DIR/bin/activate"
                    cd "$BACKEND_DIR"
                    python -m compileall .
                    python -c "from main import app; print(app.title)"
                '''
            }
        }

        stage('Frontend Dependencies') {
            steps {
                sh '''
                    set -eux
                    cd "$FRONTEND_DIR"
                    if [ -f package-lock.json ]; then
                        npm ci --no-audit --no-fund
                    else
                        npm install --no-audit --no-fund
                    fi
                '''
            }
        }

        stage('Frontend Build') {
            steps {
                sh '''
                    set -eux
                    cd "$FRONTEND_DIR"
                    npm run build
                '''
            }
        }

        stage('Quality Notes') {
            steps {
                sh '''
                    set +e
                    cd "$FRONTEND_DIR"
                    npm run lint > "../$REPORT_DIR/frontend-lint.txt" 2>&1
                    lint_status=$?
                    cd ..

                    if [ "$lint_status" -eq 0 ]; then
                        echo "Frontend lint: passed" | tee -a "$REPORT_DIR/pipeline-summary.txt"
                    else
                        echo "Frontend lint: warnings found; build kept green for this lightweight pipeline" | tee -a "$REPORT_DIR/pipeline-summary.txt"
                    fi

                    exit 0
                '''
            }
        }

        stage('SonarQube Scan') {
            steps {
                sh '''
                    set +e
                    mkdir -p "$REPORT_DIR"

                    if [ -z "${SONAR_TOKEN:-}" ]; then
                        echo "SonarQube scan: skipped because SONAR_TOKEN is not configured" | tee "$REPORT_DIR/sonarqube-scan.txt"
                        echo "SonarQube scan: skipped" >> "$REPORT_DIR/pipeline-summary.txt"
                        exit 0
                    fi

                    if ! curl -fsS --max-time 10 "$SONAR_HOST_URL/api/system/status" > "$REPORT_DIR/sonarqube-status.json"; then
                        echo "SonarQube scan: skipped because $SONAR_HOST_URL is not reachable yet" | tee "$REPORT_DIR/sonarqube-scan.txt"
                        echo "SonarQube scan: SonarQube not reachable" >> "$REPORT_DIR/pipeline-summary.txt"
                        exit 0
                    fi

                    if [ ! -f sonar-project.properties ]; then
                        {
                            echo "sonar.projectKey=$SONAR_PROJECT_KEY"
                            echo "sonar.projectName=UrbanBank"
                            echo "sonar.sources=$BACKEND_DIR,$FRONTEND_DIR/src"
                            echo "sonar.exclusions=$FRONTEND_DIR/node_modules/**,$FRONTEND_DIR/dist/**,**/__pycache__/**,**/.venv/**,**/.pytest_cache/**,**/.ruff_cache/**"
                            echo "sonar.sourceEncoding=UTF-8"
                        } > sonar-project.properties
                    fi

                    npx --yes --package "$SONAR_SCANNER_NPM_PACKAGE" sonar-scanner > "$REPORT_DIR/sonarqube-scan.txt" 2>&1
                    scan_status=$?

                    if [ "$scan_status" -eq 0 ]; then
                        echo "SonarQube scan: completed" | tee -a "$REPORT_DIR/pipeline-summary.txt"
                    else
                        echo "SonarQube scan: failed; build kept green for this lightweight pipeline" | tee -a "$REPORT_DIR/pipeline-summary.txt"
                    fi

                    exit 0
                '''
            }
        }

        stage('Package Report') {
            steps {
                sh '''
                    set -eux
                    {
                        echo ""
                        echo "Frontend dist files:"
                        find "$FRONTEND_DIR/dist" -maxdepth 2 -type f | sort
                        echo ""
                        echo "Frontend dist size:"
                        du -sh "$FRONTEND_DIR/dist"
                    } | tee -a "$REPORT_DIR/pipeline-summary.txt"
                '''
            }
        }
    }

    post {
        success {
            echo "SUCCESS: UrbanBank lightweight CI #${BUILD_NUMBER}"
        }
        failure {
            echo "FAILURE: UrbanBank lightweight CI #${BUILD_NUMBER}"
        }
        always {
            archiveArtifacts artifacts: 'build-reports/**,Frontend/dist/**,.scannerwork/report-task.txt', allowEmptyArchive: true, fingerprint: true
        }
    }
}
