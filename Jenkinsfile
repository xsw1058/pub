pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'echo "hello world"'
                sh '''
                    echo "m shell steps works too"
                    ls -lah
                    pwd
                    sleep 10
                '''
            }
        }
    }
}