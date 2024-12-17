pipeline {

  agent none

  options {
    buildDiscarder(
      logRotator(
        artifactDaysToKeepStr: '7',
        daysToKeepStr: '14',
        numToKeepStr: '2',
        artifactNumToKeepStr: '2'
      )
    )
  }

  triggers {
    pollSCM('H/30 * * * *')
  }

  // this smight be better done as a matrix, but I can't tell if matrix cells
  // run in parallel.

  stages {

    stage('Running CentOS8, CentOS9, Fedora') {

    parallel {

      stage('CentOS8_x86_64') {
        agent {
          node {
            label 'CentOS8_x86_64'
          }
        }
        stages {
          stage('Testing') {
            steps {
              sh 'scons test'
            }
          }
          stage('Build RPM packages') {
            steps {
              sh './jenkins.sh build_rpms'
            }
          }
          stage('Sign RPM packages') {
            steps {
              sh './jenkins.sh sign_rpms'
            }
          }
          stage('Push RPM packages to EOL repository') {
            steps {
              sh './jenkins.sh push_rpms'
            }
          }
        }
      }

      stage('CentOS9_x86_64') {
        agent {
          node {
            label 'CentOS9_x86_64'
          }
        }
        stages {
          stage('Testing') {
            steps {
              sh 'scons test'
            }
          }
          stage('Build RPM packages') {
            steps {
              sh './jenkins.sh build_rpms'
            }
          }
          stage('Sign RPM packages') {
            steps {
              sh './jenkins.sh sign_rpms'
            }
          }
          stage('Push RPM packages to EOL repository') {
            steps {
              sh './jenkins.sh push_rpms'
            }
          }
        }
      }

      stage('Fedora') {
        agent {
          node {
            label 'fedora'
          }
        }
        stages {
          stage('Testing') {
            steps {
              sh 'scons test'
            }
          }
          stage('Build RPM packages') {
            steps {
              sh './jenkins.sh build_rpms'
            }
          }
          // Don't bother signing or pushing rpms on Fedora, just test rpm
          // build.
        }
      }

    }
  }
  }

  post {
    changed
    {
      emailext to: "granger@ucar.edu",
      from: "granger@ucar.edu",
      subject: "Jenkins build ${env.JOB_NAME}: ${currentBuild.currentResult}",
      body: "Job ${env.JOB_NAME}: ${currentBuild.currentResult}\n${env.BUILD_URL}"
    }
  }

}
