# VULN-12: configuration scanning example only.
resource "aws_security_group" "ssh_demo" {
  name_prefix = "portal-ssh-demo-"
  description = "Demonstrate unrestricted SSH access"

  ingress {
    description = "SSH open to all IPv4 addresses"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "Portal SSH demonstration"
    Project = "Secure DevSecOps Pipeline"
  }
}