# Initial Security Scan Baseline

Date: October 8, 2026
Repository: Bless01/secure-devsecops-pipeline

## Purpose

Record the initial scan results before introducing the planned
controlled vulnerabilities into the student portal.

## Results

| Check | Workflow run | Result | Coverage |
|---|---|---|---|
| Application tests | #17 | 21 tests passed | Application functionality and authentication checks |
| Bandit | #19 | 0 findings | 286 lines of Python code |
| Semgrep | #20 | 0 findings | 151 rules applied to 5 Python files |
| Gitleaks | #22, manual run | 0 leaks found | 30 commits scanned |

The initial automatic Gitleaks scan in run #21 checked one commit.
The manual scan in run #22 checked the available repository history.
Gitleaks version 8.24.3 was used, and its SARIF report was uploaded
as a workflow artifact.

All four jobs also completed successfully in manual run #22.
That workflow completed in 53 seconds.

## Interpretation

The configured scanners reported no findings in the code and history
they checked. This establishes our starting point; it does not prove
that the application has no vulnerabilities.

## Next Step

Introduce selected controlled vulnerabilities, record which tools
detect them, apply corrections, and compare the results with this baseline.