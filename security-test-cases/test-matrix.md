# Controlled Vulnerability Test Matrix

## Purpose

This matrix defines the controlled vulnerabilities that will be introduced into the Blessings University Student Portal and its supporting deployment files. The vulnerabilities will be used only in the isolated capstone repository to evaluate the detection capabilities of the DevSecOps pipeline.

The project will use Semgrep, Bandit, Gitleaks, Trivy, and Checkov to scan source code, secrets, dependencies, containers, Terraform, and Kubernetes configurations.

## Selected Vulnerabilities

| ID | Category | Controlled vulnerability | Planned location | Detection tool | Planned correction |
|---|---|---|---|---|---|
| VULN-01 | Application | SQL injection in student login | Flask login route | Semgrep and Bandit | Use parameterized SQL queries |
| VULN-02 | Application | Stored cross-site scripting in the student biography | Profile update function | Semgrep | Validate input and escape output |
| VULN-03 | Application | Broken access control allowing access to another student’s grades | Grades route | Semgrep and functional testing | Verify record ownership before displaying grades |
| VULN-04 | Source code | Hard-coded Flask secret key | Application configuration | Bandit and Gitleaks | Load the secret from an environment variable |
| VULN-05 | Source code | Flask debug mode enabled | Application startup file | Bandit | Disable debug mode outside development |
| VULN-06 | Source code | Command injection through unsafe shell execution | Controlled utility function | Semgrep and Bandit | Avoid shell execution and validate input |
| VULN-07 | Source code | Use of the Python `eval()` function | Controlled data-processing function | Semgrep and Bandit | Replace `eval()` with safe parsing |
| VULN-08 | Source code | Weak MD5 password or data hashing | Authentication utility | Bandit | Use a secure password-hashing function |
| VULN-09 | Secret exposure | Fictional cloud access key committed to a test file | Controlled secret fixture | Gitleaks | Remove the key and use repository secrets |
| VULN-10 | Secret exposure | Fictional private key committed to a test file | Controlled secret fixture | Gitleaks | Remove the key and use secure secret storage |
| VULN-11 | Dependency | Python package with a known vulnerability | Controlled requirements file | Trivy | Upgrade to a corrected package version |
| VULN-12 | Container | Container image containing known vulnerable packages | Dockerfile | Trivy | Use an updated minimal base image |
| VULN-13 | Container | Container configured to run as the root user | Dockerfile | Trivy | Create and use a non-root user |
| VULN-14 | Terraform | Publicly accessible cloud storage bucket | Terraform configuration | Checkov | Block public access |
| VULN-15 | Terraform | Cloud storage encryption disabled | Terraform configuration | Checkov | Enable server-side encryption |
| VULN-16 | Terraform | Security group allowing unrestricted SSH access | Terraform configuration | Checkov | Restrict SSH access to an approved network |
| VULN-17 | Kubernetes | Privileged container enabled | Kubernetes deployment manifest | Checkov | Disable privileged mode |
| VULN-18 | Kubernetes | Container allowed to run as root | Kubernetes deployment manifest | Checkov | Require a non-root security context |
| VULN-19 | Kubernetes | CPU and memory limits omitted | Kubernetes deployment manifest | Checkov | Define resource requests and limits |

## Evaluation Approach

Each controlled vulnerability will be introduced individually or in a clearly identified test group. The relevant scanner will be executed through the GitHub Actions pipeline, and the following information will be recorded:

1. Whether the vulnerability was detected.
2. Which tool detected it.
3. The reported severity.
4. The number of false positives or missed findings.
5. The pipeline execution time.
6. The correction applied.
7. Whether the corrected version passed the follow-up scan.

The application and infrastructure will first be maintained as a clean baseline. Controlled vulnerable versions will then be created for testing, followed by corrected versions that demonstrate remediation and pipeline verification.

## Safety Statement

All credentials, student records, cloud resources, and vulnerable configurations used in this project will be fictional or isolated. No real student information, active credentials, or production infrastructure will be used.