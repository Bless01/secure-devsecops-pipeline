# VULN-12: configuration scanning example only.
resource "aws_security_group" "ssh_demo" {
  name_prefix = "portal-ssh-demo-"
  description = "Demonstrate unrestricted SSH access"
  
  ingress {
    description = "SSH restricted to example administrator address"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["192.0.2.10/32"]
  }

  tags = {
    Name    = "Portal SSH demonstration"
    Project = "Secure DevSecOps Pipeline"
  }
}