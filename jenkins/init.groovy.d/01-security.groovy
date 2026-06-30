import jenkins.model.Jenkins
import hudson.security.HudsonPrivateSecurityRealm
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.model.User

def jenkins = Jenkins.get()
def username = System.getenv('JENKINS_ADMIN_USERNAME') ?: 'urbanbank-admin'
def password = System.getenv('JENKINS_ADMIN_PASSWORD') ?: 'UrbanBankJenkins2026!'
def securityRealm = jenkins.getSecurityRealm()

if (!(securityRealm instanceof HudsonPrivateSecurityRealm)) {
    securityRealm = new HudsonPrivateSecurityRealm(false)
    jenkins.setSecurityRealm(securityRealm)
}

def existingUser = User.getById(username, false)
if (existingUser != null) {
    existingUser.delete()
}

securityRealm.createAccount(username, password)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
jenkins.setAuthorizationStrategy(strategy)

jenkins.save()
println "Configured Jenkins admin user '${username}'."