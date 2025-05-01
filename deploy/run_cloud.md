# AIContentGuard - Cloud Deployment Guide (Example: AWS EC2)

This guide provides example steps for deploying the AIContentGuard service to an AWS EC2 instance using Docker. Adapt these steps for other cloud providers (GCP, Azure) or deployment methods (Kubernetes, Fargate, etc.) as needed.

**Target Audience:** Engineers familiar with AWS, Linux, and Docker.

**Prerequisites:**

- AWS Account with permissions to create EC2 instances, Security Groups, and potentially IAM roles.
- AWS CLI configured locally (optional, can use AWS Console).
- Docker installed on your local machine for building the image (or use a CI/CD pipeline).
- A way to securely transfer files (like `.env`) to the EC2 instance (e.g., `scp`, Systems Manager).

## 1. Prepare the Application Package

- Ensure your project includes a `Dockerfile` and `requirements.txt`.
- Create a `.env` file with production-ready settings (e.g., `LOG_LEVEL=INFO`, appropriate model IDs, thresholds, rate limits). **Do not commit this file to Git.**
- Consider building the Docker image locally or using a CI/CD pipeline that pushes the image to a container registry (like AWS ECR).

## 2. Launch an EC2 Instance

1.  **Choose an AMI:** Select a suitable Linux AMI (e.g., Amazon Linux 2, Ubuntu Server).
2.  **Choose an Instance Type:** Select an instance type with sufficient CPU, RAM, and potentially GPU if using GPU-accelerated models. Consider instance types optimized for compute or memory depending on your models. Start with a general-purpose type (e.g., `t3.large`, `m5.large`) and monitor performance.
3.  **Configure Instance Details:**
    - Network/VPC: Choose your desired VPC and subnet.
    - IAM Role (Recommended): Create or assign an IAM role with necessary permissions if the application needs to interact with other AWS services (e.g., S3 for models, CloudWatch for logs).
4.  **Add Storage:** Ensure sufficient disk space for the OS, Docker, container images, and potentially cached models (especially if not using a shared cache volume).
5.  **Add Tags:** Tag your instance appropriately (e.g., `Name: aicontentguard-prod`, `Project: AIContentGuard`).
6.  **Configure Security Group:**
    - Create a new security group or use an existing one.
    - Allow inbound traffic on the port your application listens on (default: `8000`) from necessary sources (e.g., your application load balancer, specific IPs, or `0.0.0.0/0` if publicly accessible - use with caution).
    - Allow inbound traffic on port `22` (SSH) from your IP address for management.
7.  **Review and Launch:** Select or create an SSH key pair to access the instance.

## 3. Connect to the Instance and Install Docker

1.  **SSH into the instance:**
    ```bash
    ssh -i /path/to/your-key.pem <user>@<ec2-instance-public-ip>
    # Replace <user> with ec2-user (Amazon Linux) or ubuntu (Ubuntu)
    ```
2.  **Update the package manager and install Docker:**
    - **Amazon Linux 2:**
      ```bash
      sudo yum update -y
      sudo amazon-linux-extras install docker -y
      sudo systemctl start docker
      sudo systemctl enable docker
      sudo usermod -a -G docker ec2-user
      # Log out and log back in to apply group changes
      logout
      ```
    - **Ubuntu:**
      ```bash
      sudo apt-get update -y
      sudo apt-get install -y docker.io
      sudo systemctl start docker
      sudo systemctl enable docker
      sudo usermod -aG docker ubuntu
      # Log out and log back in to apply group changes
      logout
      ```
3.  **Verify Docker installation:**
    ```bash
    docker --version
    ```

## 4. Deploy the Application Container

Choose one of the following methods:

**Method A: Build Image on EC2 (Simpler for single instances)**

1.  **Transfer Project Files:** Copy your project directory (excluding sensitive files like `.env` initially) to the EC2 instance using `scp` or another method.
    ```bash
    # Example using scp (run from your local machine)
    scp -i /path/to/your-key.pem -r /path/to/local/ai-content-guard <user>@<ec2-instance-public-ip>:~/
    ```
2.  **Transfer `.env` File Securely:** Copy your production `.env` file to the project directory on the EC2 instance.
    ```bash
    # Example using scp
    scp -i /path/to/your-key.pem /path/to/local/.env <user>@<ec2-instance-public-ip>:~/ai-content-guard/
    ```
3.  **Build the Docker Image:** SSH back into the instance and navigate to the project directory.
    ```bash
    cd ~/ai-content-guard
    docker build -t ai-content-guard .
    ```
4.  **Run the Container:**
    ```bash
    docker run -d --name aicontentguard-app --restart always \
      --env-file .env \
      -p 8000:8000 \
      -v $(pwd)/logs:/app/logs \
      # Optional: Mount a volume for HuggingFace cache if needed
      # -v /path/on/host/hf_cache:/root/.cache/huggingface \
      ai-content-guard
    # -d: Run in detached mode
    # --name: Assign a name to the container
    # --restart always: Automatically restart the container if it stops
    # --env-file: Load environment variables from the .env file
    # -p: Map host port 8000 to container port 8000
    # -v: Mount the host logs directory to the container's log directory (for persistence)
    ```

**Method B: Use a Container Registry (Recommended for scalability/CI/CD)**

1.  **Build and Push Image:** Build the Docker image locally or in your CI/CD pipeline and push it to a registry (e.g., AWS ECR, Docker Hub).
    ```bash
    # Example for AWS ECR (replace placeholders)
    aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com
    docker build -t <your-ecr-repo-name> .
    docker tag <your-ecr-repo-name>:latest <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/<your-ecr-repo-name>:latest
    docker push <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/<your-ecr-repo-name>:latest
    ```
2.  **Transfer `.env` File Securely:** Copy your production `.env` file to a location on the EC2 instance (e.g., `~/aicontentguard.env`).
3.  **Pull and Run the Container:** SSH into the instance.

    ```bash
    # Example for AWS ECR
    aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com
    docker pull <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/<your-ecr-repo-name>:latest

    # Create logs directory on host
    mkdir -p ~/logs

    docker run -d --name aicontentguard-app --restart always \
      --env-file ~/aicontentguard.env \
      -p 8000:8000 \
      -v ~/logs:/app/logs \
      # Optional: Mount cache volume
      # -v /path/on/host/hf_cache:/root/.cache/huggingface \
      <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com/<your-ecr-repo-name>:latest
    ```

## 5. Verify Deployment

1.  **Check Container Logs:**
    ```bash
    docker logs aicontentguard-app -f
    ```
    Look for messages indicating the server has started and agents are ready.
2.  **Test the API:** Access the API endpoint from your local machine or another server (ensure the security group allows it).
    ```bash
    curl http://<ec2-instance-public-ip>:8000/health
    curl -X POST -H "Content-Type: application/json" \
         -d '{"text": "This is a test message."}' \
         http://<ec2-instance-public-ip>:8000/analyze
    ```

## 6. Optional: Systemd Service

For better management (start, stop, restart, auto-start on boot) without relying solely on Docker's `--restart always`, you can create a systemd service unit.

1.  **Create a service file:**
    ```bash
    sudo nano /etc/systemd/system/aicontentguard.service
    ```
2.  **Add the following content (adjust paths and image name as needed):**

    ```ini
    [Unit]
    Description=AIContentGuard Docker Container
    Requires=docker.service
    After=docker.service

    [Service]
    Restart=always
    User=<your-user> # e.g., ec2-user or ubuntu
    Group=docker
    WorkingDirectory=/home/<your-user>/ai-content-guard # Or wherever your .env file is

    # Stop existing container (if any)
    ExecStartPre=-/usr/bin/docker stop aicontentguard-app
    ExecStartPre=-/usr/bin/docker rm aicontentguard-app
    # Pull latest image (if using registry)
    # ExecStartPre=/usr/bin/docker pull <your-image-name>:latest

    # Start the container
    ExecStart=/usr/bin/docker run --name aicontentguard-app \
      --env-file .env \
      -p 8000:8000 \
      -v /home/<your-user>/logs:/app/logs \
      # Optional: Mount cache volume
      # -v /path/on/host/hf_cache:/root/.cache/huggingface \
      <your-image-name>:latest # Replace with your image name/tag

    # Stop the container
    ExecStop=/usr/bin/docker stop aicontentguard-app

    [Install]
    WantedBy=multi-user.target
    ```

3.  **Enable and start the service:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable aicontentguard.service
    sudo systemctl start aicontentguard.service
    sudo systemctl status aicontentguard.service
    ```

## 7. Further Considerations

- **Load Balancing:** For high availability and scalability, deploy multiple instances behind an AWS Application Load Balancer (ALB).
- **HTTPS:** Configure the ALB or a reverse proxy (like Nginx/Caddy) on the instance to handle TLS termination.
- **Centralized Logging:** Configure the application or Docker daemon to send logs to CloudWatch Logs or another logging service.
- **Monitoring:** Use CloudWatch Metrics, Prometheus (scraping the `/metrics` endpoint), or other monitoring tools to track performance and health.
- **Secrets Management:** Use AWS Secrets Manager or Parameter Store for managing sensitive configuration instead of `.env` files.
- **Model Storage:** For large models or shared access, consider storing models in S3 and downloading them on instance startup, or using EFS for a shared filesystem.
- **CI/CD:** Implement a pipeline (e.g., GitHub Actions, AWS CodePipeline) to automate building, testing, and deploying new versions.
