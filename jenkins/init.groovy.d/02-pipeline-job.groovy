import hudson.plugins.git.GitSCM
import hudson.plugins.git.UserRemoteConfig
import hudson.plugins.git.BranchSpec
import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition

def jenkins = Jenkins.get()
def jobName = 'UrbanBank-Pipeline'
def repositoryUrl = 'https://github.com/bhavik2258/UrbanBank_ServerCrashs-Devops_Solution.git'
def job = jenkins.getItemByFullName(jobName)

if (job == null) {
    job = jenkins.createProject(WorkflowJob, jobName)
}

def scm = new GitSCM(
    [new UserRemoteConfig(repositoryUrl, null, null, null)],
    [new BranchSpec('*/main')],
    false,
    [],
    null,
    null,
    []
)
job.definition = new CpsScmFlowDefinition(scm, 'Jenkinsfile')
job.save()
jenkins.save()
println "Configured Jenkins pipeline job '${jobName}'."
