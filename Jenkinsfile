pipeline {
    agent any

    triggers {
        githubPush()
        pollSCM('H/5 * * * *')
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
                    bat '''
                        python -m venv venv
                        call venv\\Scripts\\activate.bat
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Backend: Lint') {
            steps {
                dir('backend') {
                    bat '''
                        call venv\\Scripts\\activate.bat
                        flake8 --max-line-length=120 --exit-zero simulation.py main.py
                    '''
                }
            }
        }

        stage('Backend: Test') {
            steps {
                dir('backend') {
                    bat '''
                        call venv\\Scripts\\activate.bat
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
                    bat 'npm install --no-audit --no-fund'
                }
            }
        }

        stage('Frontend: Test') {
            steps {
                dir('frontend') {
                    bat 'npx vitest run --reporter=junit --outputFile=test-results.xml'
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
                    bat 'npm run build'
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
            script {
                def status = currentBuild.currentResult
                writeFile file: 'build-status.json', text: """{"build": "${BUILD_NUMBER}", "status": "${status}", "branch": "${env.GIT_BRANCH}"}"""
                archiveArtifacts artifacts: 'build-status.json', allowEmptyArchive: true
            }
        }
    }
}
