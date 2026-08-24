pipeline {
    agent any

    // Auto-trigger on every commit push (needs GitHub webhook -> Jenkins configured,
    // see docs/JENKINS_SETUP.md). pollSCM is a fallback if webhook isn't reachable
    // (e.g. Jenkins running on localhost without a public URL).
    triggers {
        githubPush()
        pollSCM('H/5 * * * *')
    }

    environment {
        PYTHON = 'python3'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend: Install') {
            steps {
                dir('backend') {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Backend: Lint') {
            steps {
                dir('backend') {
                    sh '''
                        . venv/bin/activate
                        flake8 --max-line-length=120 --exit-zero simulation.py main.py
                    '''
                }
            }
        }

        stage('Backend: Test') {
            steps {
                dir('backend') {
                    sh '''
                        . venv/bin/activate
                        python -m pytest tests/ -v --junitxml=test-results.xml
                    '''
                }
            }
            post {
                always {
                    junit 'backend/test-results.xml'
                }
            }
        }

        stage('Frontend: Install') {
            steps {
                dir('frontend') {
                    sh 'npm install --no-audit --no-fund'
                }
            }
        }

        stage('Frontend: Test') {
            steps {
                dir('frontend') {
                    sh 'npx vitest run --reporter=junit --outputFile=test-results.xml'
                }
            }
            post {
                always {
                    junit 'frontend/test-results.xml'
                }
            }
        }

        stage('Frontend: Build') {
            steps {
                dir('frontend') {
                    sh 'npm run build'
                }
            }
        }

        stage('Archive Artifacts') {
            steps {
                archiveArtifacts artifacts: 'frontend/dist/**', allowEmptyArchive: true
            }
        }
    }

    post {
        success {
            echo 'Build passed: backend + frontend tests green, frontend build produced.'
        }
        failure {
            echo 'Build failed — check the stage logs above.'
        }
        always {
            // Drop a small JSON status file the dashboard can optionally read
            // if you wire Jenkins to publish it (see docs/JENKINS_SETUP.md).
            script {
                def status = currentBuild.currentResult
                writeFile file: 'build-status.json', text: """{"build": "${BUILD_NUMBER}", "status": "${status}", "branch": "${env.GIT_BRANCH}"}"""
                archiveArtifacts artifacts: 'build-status.json', allowEmptyArchive: true
            }
        }
    }
}
