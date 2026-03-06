# Application Load Balancer and SSL certificate for chat.tersona.terpedia.com

# ACM Certificate (requires DNS validation)
resource "aws_acm_certificate" "librechat" {
  domain_name       = var.domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "librechat-cert"
  }
}

# Application Load Balancer
resource "aws_lb" "librechat" {
  name               = "librechat-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = {
    Name = "librechat-alb"
  }
}

# Target group
resource "aws_lb_target_group" "librechat" {
  name     = "librechat-tg"
  port     = 3080
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "librechat-tg"
  }
}

# Register EC2 instance with target group
resource "aws_lb_target_group_attachment" "librechat" {
  target_group_arn = aws_lb_target_group.librechat.arn
  target_id        = aws_instance.librechat.id
  port             = 3080
}

# HTTP listener (redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.librechat.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.librechat.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.librechat.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.librechat.arn
  }
}

output "alb_dns_name" {
  value       = aws_lb.librechat.dns_name
  description = "ALB DNS name - create CNAME chat.tersona.terpedia.com pointing here"
}

output "certificate_arn" {
  value = aws_acm_certificate.librechat.arn
}

output "certificate_validation_options" {
  value       = aws_acm_certificate.librechat.domain_validation_options
  description = "DNS records needed for certificate validation"
}
