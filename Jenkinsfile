pipeline {

  agent {
     node {
        label 'CentOS8_x86_64'
        }
  }

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

  stages {
    // stage('Checkout Scm') {
    //   steps {
    //     git 'https://github.com/NCAR/eol_scons'
    //   }
    // }

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