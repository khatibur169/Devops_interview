# DevOps & Cloud Engineering Interview Study Guide

**Comprehensive Preparation Guide**
Version 1.0 | 2026

---

## Table of Contents

1. [Kubernetes / EKS / Containers](#kubernetes-eks-containers)
2. [Docker / Containers](#docker-containers)
3. [AWS / Cloud / Architecture](#aws-cloud-architecture)
4. [GCP](#gcp)
5. [Terraform / IaC](#terraform-iac)
6. [CI/CD / DevOps](#cicd-devops)
7. [Linux / Systems](#linux-systems)
8. [Networking](#networking)
9. [Git / Deployment](#git-deployment)
10. [Monitoring / Troubleshooting / SRE](#monitoring-troubleshooting-sre)
11. [Python / Automation / API](#python-automation-api)
12. [SQL / Database Design](#sql-database-design)
13. [JavaScript / Promises](#javascript-promises)
14. [Java Concurrency](#java-concurrency)
15. [System Design / Architecture](#system-design-architecture)
16. [Security](#security)
17. [DSA / Algorithmic Problems](#dsa-algorithmic-problems)
18. [Deployment / Hosting](#deployment-hosting)

---

## Kubernetes / EKS / Containers

### How would you deploy and manage a Python-based data processing application in an EKS cluster?

**Detailed Explanation:**

Deploying a Python data processing application on EKS involves several key steps:

**1. Containerization:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "process_data.py"]
```

**2. Build and Push to ECR:**
```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t data-processor:v1 .

# Tag and push
docker tag data-processor:v1 <account-id>.dkr.ecr.us-east-1.amazonaws.com/data-processor:v1
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/data-processor:v1
```

**3. Kubernetes Deployment Manifest:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-processor
  namespace: data-processing
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-processor
  template:
    metadata:
      labels:
        app: data-processor
    spec:
      serviceAccountName: data-processor-sa
      containers:
      - name: processor
        image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/data-processor:v1
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: S3_BUCKET
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: s3_bucket
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

**4. ConfigMap and Secrets:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  s3_bucket: "my-data-bucket"
  log_level: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  password: <base64-encoded-password>
```

**5. Service Account with IAM Role (IRSA):**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: data-processor-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<account-id>:role/data-processor-role
```

**Management Best Practices:**

- **Horizontal Pod Autoscaling (HPA):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: data-processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: data-processor
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

- **Monitoring with Prometheus/CloudWatch:**
  - Use CloudWatch Container Insights
  - Deploy Prometheus + Grafana for metrics
  - Implement custom metrics via StatsD or Prometheus client

- **Logging:**
  - Use Fluent Bit or Fluentd to ship logs to CloudWatch Logs
  - Implement structured JSON logging
  - Add correlation IDs for request tracing

- **CI/CD Integration:**
  - Use GitOps (ArgoCD/Flux) for deployment automation
  - Implement blue-green or canary deployments
  - Use Helm charts for package management

---

### How do you deploy a three-tier web application on Amazon EKS?

**Detailed Explanation:**

A three-tier architecture consists of:
1. **Presentation Tier** (Frontend - React/Angular)
2. **Application Tier** (Backend API - Node.js/Python/Java)
3. **Data Tier** (Database - RDS/Aurora)

**Architecture Overview:**
```
Internet → ALB → Frontend Service → Frontend Pods
                 ↓
                 Backend Service → Backend Pods
                 ↓
                 RDS (outside cluster)
```

**1. Frontend Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
      tier: presentation
  template:
    metadata:
      labels:
        app: frontend
        tier: presentation
    spec:
      containers:
      - name: nginx
        image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"

---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
```

**2. Backend Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: backend
      tier: application
  template:
    metadata:
      labels:
        app: backend
        tier: application
    spec:
      serviceAccountName: backend-sa
      containers:
      - name: api
        image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/backend:latest
        ports:
        - containerPort: 8080
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-config
              key: host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-config
              key: password
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
```

**3. Ingress Configuration (AWS Load Balancer Controller):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: application-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:xxx:certificate/xxx
    alb.ingress.kubernetes.io/ssl-redirect: '443'
spec:
  rules:
  - host: www.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8080
```

**4. Database Configuration (RDS):**

- Create RDS instance in private subnet
- Configure security group to allow traffic from EKS worker nodes
- Store credentials in AWS Secrets Manager
- Use External Secrets Operator to sync secrets to K8s

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-config
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: db-config
  data:
  - secretKey: host
    remoteRef:
      key: prod/database
      property: host
  - secretKey: password
    remoteRef:
      key: prod/database
      property: password
```

**5. Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: data
    ports:
    - protocol: TCP
      port: 5432
```

**Deployment Steps:**

1. **Create EKS Cluster:**
```bash
eksctl create cluster \
  --name three-tier-app \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed
```

2. **Install AWS Load Balancer Controller:**
```bash
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=three-tier-app
```

3. **Deploy Application:**
```bash
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmaps.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

4. **Verify Deployment:**
```bash
kubectl get pods -n production
kubectl get svc -n production
kubectl get ingress -n production
```

---

### What is an EKS cluster, and how does it work?

**Detailed Explanation:**

**Amazon Elastic Kubernetes Service (EKS)** is a managed Kubernetes service that makes it easy to run Kubernetes on AWS without needing to install, operate, and maintain your own Kubernetes control plane.

**Key Components:**

**1. Control Plane (Managed by AWS):**
- **API Server:** Entry point for all REST commands used to control the cluster
- **etcd:** Distributed key-value store for cluster data
- **Scheduler:** Assigns pods to nodes based on resource requirements
- **Controller Manager:** Runs controller processes (node, replication, endpoints, service account controllers)
- **Cloud Controller Manager:** Integrates with AWS services

**2. Data Plane (Managed by You):**
- **Worker Nodes:** EC2 instances that run your containerized applications
- **Node Groups:** Collections of EC2 instances with similar configurations
- **Fargate Profiles:** Serverless compute for pods (no node management)

**How EKS Works:**

```
┌─────────────────────────────────────────────────┐
│           AWS Managed Control Plane             │
│  ┌──────────┐  ┌──────┐  ┌───────────┐        │
│  │API Server│←→│ etcd │←→│ Scheduler │         │
│  └──────────┘  └──────┘  └───────────┘        │
│       ↑                                         │
│       │  (Highly Available across 3 AZs)      │
└───────┼─────────────────────────────────────────┘
        │
        │ (kubectl commands)
        ↓
┌─────────────────────────────────────────────────┐
│              Your VPC                           │
│  ┌─────────────┐  ┌─────────────┐             │
│  │  Worker     │  │  Worker     │             │
│  │  Node 1     │  │  Node 2     │             │
│  │             │  │             │             │
│  │ ┌────┐┌────┐│  │┌────┐┌────┐│             │
│  │ │Pod1││Pod2││  ││Pod3││Pod4││             │
│  │ └────┘└────┘│  │└────┘└────┘│             │
│  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────┘
```

**EKS Cluster Creation Process:**

1. **Create VPC with proper networking:**
   - Public subnets for load balancers
   - Private subnets for worker nodes
   - NAT Gateway for outbound internet access

2. **Create IAM Roles:**
   - Cluster Role: Allows EKS to manage resources
   - Node Role: Allows worker nodes to interact with EKS
   - Pod Execution Role: For Fargate

3. **Create EKS Cluster:**
```bash
eksctl create cluster \
  --name my-cluster \
  --region us-east-1 \
  --version 1.28 \
  --vpc-private-subnets subnet-xxx,subnet-yyy \
  --vpc-public-subnets subnet-zzz,subnet-www \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3
```

4. **Configure kubectl:**
```bash
aws eks update-kubeconfig --region us-east-1 --name my-cluster
```

**Key Features:**

- **Managed Control Plane:** AWS handles control plane upgrades, patching, and high availability
- **Integration with AWS Services:**
  - IAM for authentication (IAM Roles for Service Accounts - IRSA)
  - VPC for networking
  - ELB for load balancing
  - ECR for container registry
  - CloudWatch for logging and monitoring
  - Secrets Manager for secrets

- **Security:**
  - Encryption at rest using AWS KMS
  - Encryption in transit
  - VPC isolation
  - Security groups and network policies
  - Pod Security Policies/Pod Security Standards

- **Scalability:**
  - Cluster Autoscaler
  - Horizontal Pod Autoscaler
  - Vertical Pod Autoscaler
  - Fargate for serverless scaling

**EKS vs Self-Managed Kubernetes:**

| Feature | EKS | Self-Managed |
|---------|-----|--------------|
| Control Plane | AWS Managed | You Manage |
| HA Setup | Automatic (3 AZs) | Manual |
| Upgrades | Managed | Manual |
| Cost | Cluster fee + EC2 | EC2 only |
| AWS Integration | Native | Manual setup |
| Responsibility | Shared | Full |

---

### What is Kubernetes, and what is its purpose?

**Detailed Explanation:**

**Kubernetes (K8s)** is an open-source container orchestration platform originally developed by Google, now maintained by the Cloud Native Computing Foundation (CNCF).

**Purpose:**

Kubernetes automates the deployment, scaling, and management of containerized applications. It solves the operational challenges of running containers at scale.

**Key Problems Kubernetes Solves:**

**1. Container Orchestration:**
- **Before K8s:** Manually starting/stopping containers on servers
- **With K8s:** Declaratively specify desired state, K8s maintains it

**2. High Availability:**
- Automatically restarts failed containers
- Reschedules containers when nodes die
- Kills containers that don't respond to health checks
- Distributes containers across multiple nodes

**3. Scaling:**
- **Horizontal Scaling:** Add/remove pod replicas based on load
- **Vertical Scaling:** Adjust resource limits
- **Cluster Autoscaling:** Add/remove nodes automatically

**4. Service Discovery & Load Balancing:**
- Assigns unique IP addresses to pods
- Provides DNS names for services
- Load balances traffic across pod replicas

**5. Self-Healing:**
- Restarts failed containers
- Replaces and reschedules containers
- Kills containers that don't pass health checks

**6. Automated Rollouts and Rollbacks:**
```yaml
# Rolling update strategy
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```
- Zero-downtime deployments
- Automatic rollback on failures
- Progressive rollouts (canary/blue-green)

**7. Configuration & Secret Management:**
- ConfigMaps for configuration data
- Secrets for sensitive data
- Environment variable injection
- Volume mounting

**8. Storage Orchestration:**
- Automatically mount storage systems (local, cloud, network)
- Persistent Volumes (PV) and Persistent Volume Claims (PVC)
- StorageClasses for dynamic provisioning

**Core Concepts:**

**Desired State Management:**
```yaml
# You declare: "I want 3 nginx pods"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3  # Desired state
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
```

Kubernetes continuously works to maintain this desired state:
- If a pod crashes → K8s creates a new one
- If you scale to 5 → K8s creates 2 more pods
- If you update the image → K8s performs rolling update

**Declarative vs Imperative:**

**Imperative (How to do it):**
```bash
kubectl run nginx --image=nginx
kubectl scale deployment nginx --replicas=3
kubectl expose deployment nginx --port=80
```

**Declarative (What you want):**
```yaml
# nginx-deployment.yaml - describe entire desired state
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
  # ... full specification
```
```bash
kubectl apply -f nginx-deployment.yaml  # K8s figures out how to achieve it
```

**Use Cases:**

1. **Microservices Architecture:**
   - Deploy and manage hundreds of microservices
   - Service-to-service communication
   - Independent scaling of services

2. **CI/CD Pipelines:**
   - Automated testing environments
   - Blue-green deployments
   - Canary releases

3. **Batch Processing:**
   - Jobs and CronJobs for scheduled tasks
   - Data processing pipelines
   - ETL workflows

4. **Multi-Cloud & Hybrid Cloud:**
   - Run same workloads across AWS, GCP, Azure
   - On-premises to cloud migration
   - Cloud portability

5. **Machine Learning:**
   - Model training at scale
   - Model serving/inference
   - Jupyter notebook environments

**Kubernetes Ecosystem:**

- **Package Management:** Helm, Kustomize
- **GitOps:** ArgoCD, Flux
- **Service Mesh:** Istio, Linkerd
- **Monitoring:** Prometheus, Grafana
- **Logging:** ELK Stack, Loki
- **Security:** OPA, Falco, Aqua
- **Networking:** Calico, Cilium, Weave

---

### What is Kubernetes architecture, and what are the roles of Pods, Nodes, Services, and the Control Plane?

**Detailed Explanation:**

Kubernetes follows a master-worker architecture with a declarative API.

**Architecture Overview:**

```
┌───────────────────────────────────────────────────────────┐
│                   CONTROL PLANE (Master)                  │
│  ┌────────────┐  ┌──────┐  ┌──────────┐  ┌─────────────┐│
│  │ API Server │←→│ etcd │←→│Scheduler │←→│Controller   ││
│  │            │  │      │  │          │  │Manager      ││
│  └────────────┘  └──────┘  └──────────┘  └─────────────┘│
│         ↑                                                 │
└─────────┼─────────────────────────────────────────────────┘
          │ (API calls)
          ↓
┌─────────────────────────────────────────────────────────┐
│                    WORKER NODES                         │
│  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │  Node 1              │  │  Node 2              │   │
│  │  ┌────────────────┐  │  │  ┌────────────────┐  │   │
│  │  │   kubelet      │  │  │  │   kubelet      │  │   │
│  │  │   kube-proxy   │  │  │  │   kube-proxy   │  │   │
│  │  │   Container    │  │  │  │   Container    │  │   │
│  │  │   Runtime      │  │  │  │   Runtime      │  │   │
│  │  └────────────────┘  │  │  └────────────────┘  │   │
│  │                      │  │                      │   │
│  │  ┌────┐  ┌────┐     │  │  ┌────┐  ┌────┐     │   │
│  │  │Pod1│  │Pod2│     │  │  │Pod3│  │Pod4│     │   │
│  │  │    │  │    │     │  │  │    │  │    │     │   │
│  │  └────┘  └────┘     │  │  └────┘  └────┘     │   │
│  └──────────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## **1. CONTROL PLANE Components**

### **API Server (kube-apiserver)**

**Role:** Front-end for the Kubernetes control plane

**Functions:**
- Exposes Kubernetes API (REST interface)
- Authenticates and authorizes requests
- Validates and processes API objects
- Gateway to etcd (only component that talks to etcd)
- Horizontal scaling support (can run multiple instances)

**Example Interaction:**
```bash
kubectl get pods  # → API Server → etcd → returns pod list
```

### **etcd**

**Role:** Distributed key-value store for cluster data

**Functions:**
- Stores entire cluster state
- Stores configuration data
- Provides watch mechanism for changes
- Implements leader election using Raft consensus
- Source of truth for cluster state

**Data Stored:**
- Nodes, Pods, ConfigMaps, Secrets
- Service accounts, roles, bindings
- Deployments, ReplicaSets

**Critical:** Regular backups essential for disaster recovery

```bash
# Backup etcd
etcdctl snapshot save snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

### **Scheduler (kube-scheduler)**

**Role:** Assigns pods to nodes

**Functions:**
- Watches for newly created pods with no assigned node
- Selects optimal node for pod based on:
  - Resource requirements (CPU, memory)
  - Hardware/software constraints
  - Affinity/anti-affinity rules
  - Taints and tolerations
  - Data locality
  - Inter-workload interference

**Scheduling Process:**
1. **Filtering:** Find nodes that meet pod requirements
2. **Scoring:** Rank feasible nodes
3. **Binding:** Assign pod to highest-scored node

**Example:**
```yaml
# Pod with resource requirements
spec:
  containers:
  - name: app
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
  nodeSelector:
    disktype: ssd  # Scheduler ensures node has this label
```

### **Controller Manager (kube-controller-manager)**

**Role:** Runs controller processes

**Functions:**
- Watches cluster state via API server
- Makes changes to move current state → desired state

**Key Controllers:**

**Node Controller:**
- Monitors node health
- Responds when nodes go down
- Evicts pods from failed nodes

**Replication Controller:**
- Maintains correct number of pod replicas
```yaml
spec:
  replicas: 3  # Controller ensures exactly 3 pods run
```

**Endpoints Controller:**
- Populates Endpoints objects (joins Services & Pods)

**Service Account & Token Controllers:**
- Create default accounts and API access tokens for namespaces

**Example Scenario:**
```
Desired: 3 replicas of nginx
Current: 2 replicas running (1 pod crashed)

Replication Controller:
1. Detects: 2 < 3
2. Action: Creates 1 new pod
3. Result: 3 pods running ✓
```

### **Cloud Controller Manager (optional)**

**Role:** Integrates with cloud provider APIs

**Functions:**
- Node Controller: Checks cloud provider to determine if node was deleted
- Route Controller: Sets up routes in cloud infrastructure
- Service Controller: Creates/manages cloud load balancers
- Volume Controller: Creates/attaches/mounts cloud volumes

---

## **2. WORKER NODE Components**

### **Kubelet**

**Role:** Agent running on each node

**Functions:**
- Registers node with API server
- Watches API server for pods assigned to its node
- Ensures containers in pods are running and healthy
- Reports pod and node status to API server
- Executes liveness/readiness probes

**Process:**
```
API Server assigns Pod to Node
        ↓
Kubelet sees new pod assignment
        ↓
Kubelet pulls container image
        ↓
Kubelet starts container via container runtime
        ↓
Kubelet monitors container health
        ↓
Kubelet reports status to API Server
```

### **Kube-Proxy**

**Role:** Network proxy running on each node

**Functions:**
- Maintains network rules (iptables/IPVS)
- Enables Service abstraction
- Routes traffic to appropriate pods
- Performs connection forwarding and load balancing

**How Services Work with Kube-Proxy:**
```yaml
# Service definition
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

```
Client → my-service:80 (Virtual IP)
              ↓
        kube-proxy (iptables rules)
              ↓
    Load balance across pods:
    → Pod1:8080 (10.1.1.1)
    → Pod2:8080 (10.1.1.2)
    → Pod3:8080 (10.1.1.3)
```

### **Container Runtime**

**Role:** Software responsible for running containers

**Options:**
- **containerd:** Most common (Docker uses this)
- **CRI-O:** Lightweight alternative
- **Docker:** (Deprecated, use containerd directly)

**Functions:**
- Pull container images
- Run containers
- Manage container lifecycle
- Provide container isolation

---

## **3. PODS**

**Role:** Smallest deployable unit in Kubernetes

**Definition:** A pod is a group of one or more containers with shared storage and network resources.

**Characteristics:**

**Shared Network:**
- Single IP address per pod
- Containers in pod communicate via localhost
- Share port space

**Shared Storage:**
- Volumes mounted in pod accessible to all containers

**Lifecycle:**
- Ephemeral (not designed to persist)
- Scheduled together on same node
- Created/destroyed as unit

**Pod Example:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
  labels:
    app: web
spec:
  containers:
  - name: nginx
    image: nginx:1.21
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html

  - name: content-updater
    image: busybox
    command: ["/bin/sh"]
    args: ["-c", "while true; do date > /data/index.html; sleep 60; done"]
    volumeMounts:
    - name: shared-data
      mountPath: /data

  volumes:
  - name: shared-data
    emptyDir: {}
```

**Multi-Container Patterns:**

1. **Sidecar:** Helper container (logging, monitoring)
2. **Ambassador:** Proxy container for external connections
3. **Adapter:** Transforms output to standard format

**Pod Lifecycle Phases:**
- **Pending:** Accepted but not yet running
- **Running:** At least one container running
- **Succeeded:** All containers terminated successfully
- **Failed:** At least one container failed
- **Unknown:** Cannot determine state

---

## **4. SERVICES**

**Role:** Stable network endpoint for accessing pods

**Problem Services Solve:**
- Pods are ephemeral (IP addresses change)
- Multiple pod replicas need load balancing
- Need stable DNS name and IP

**Service Types:**

### **ClusterIP (Default)**
- Internal-only access
- Stable internal IP
- Use for internal microservices

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8080
```

### **NodePort**
- Exposes service on each node's IP at static port
- Accessible from outside cluster: `<NodeIP>:<NodePort>`
- Port range: 30000-32767

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: NodePort
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
```

### **LoadBalancer**
- Creates external load balancer (AWS ELB, GCP LB)
- Automatically assigns external IP
- Best for production workloads

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

### **ExternalName**
- Maps service to DNS name
- No proxying, just DNS CNAME record

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: db.example.com
```

**Service Discovery:**

**DNS:**
```
<service-name>.<namespace>.svc.cluster.local
```

**Example:**
```yaml
# backend service in production namespace
# Accessible as: backend.production.svc.cluster.local
# Or shorthand: backend (from same namespace)
```

**Endpoints:**
```bash
kubectl get endpoints backend
# Shows actual pod IPs service routes to
```

---

## **Putting It All Together: Request Flow Example**

**Scenario:** User accesses web application

```
1. User → http://example.com
        ↓
2. Load Balancer (AWS ELB)
        ↓
3. Service (LoadBalancer type)
        ↓
4. kube-proxy (selects pod based on load balancing)
        ↓
5. Pod (nginx container)
        ↓
6. Pod makes API call to backend service
        ↓
7. Service (ClusterIP) resolves via DNS
        ↓
8. kube-proxy routes to backend pod
        ↓
9. Backend pod processes request
        ↓
10. Response flows back through chain
```

**Behind the Scenes:**

**Control Plane:**
- API Server receives all kubectl commands
- Scheduler assigns new pods to nodes
- Controllers monitor and maintain desired state
- etcd stores all configuration

**Worker Nodes:**
- Kubelet ensures containers run correctly
- Kube-proxy maintains network routing
- Container runtime executes containers

**Networking:**
- Each pod gets unique IP (pod network)
- Services provide stable virtual IPs
- kube-proxy manages iptables/IPVS rules
- CNI plugin handles pod-to-pod communication

---

### What are the core components of Kubernetes and how do they interact?

**Detailed Explanation:**

This builds on the architecture question. Let's examine component interactions through specific scenarios.

**Component Interaction Map:**

```
┌──────────────────────────────────────────────────────┐
│               kubectl (CLI)                          │
└─────────────────┬────────────────────────────────────┘
                  │ HTTPS/REST API
                  ↓
┌──────────────────────────────────────────────────────┐
│           API Server (Authentication)                │
│      ┌────────────────────────────────┐             │
│      │  RBAC, Admission Controllers   │             │
│      └────────────────────────────────┘             │
└──┬───────────────┬───────────────┬───────────────┬───┘
   │               │               │               │
   │               │               │               │
   ↓               ↓               ↓               ↓
┌──────┐    ┌──────────┐   ┌─────────────┐  ┌────────┐
│ etcd │←──→│Scheduler │   │Controllers  │  │kubectl │
└──────┘    └──────────┘   └─────────────┘  └────────┘
   ↑               │               │
   │               │               │
   │               ↓               ↓
   │        ┌────────────────────────┐
   │        │    Kubelet (Node)      │
   │        └────────────────────────┘
   │               ↑       ↑
   └───────────────┘       │
                    ┌──────┴──────┐
                    │ kube-proxy  │
                    └─────────────┘
```

---

**Scenario 1: Creating a Deployment**

```bash
kubectl create deployment nginx --image=nginx:latest --replicas=3
```

**Step-by-Step Interaction:**

**1. kubectl → API Server**
```
kubectl:
- Constructs API request (JSON/YAML)
- Authenticates using kubeconfig credentials
- Sends POST request to API server
```

**2. API Server Processing**
```
API Server:
├─ Authentication: Verifies user identity
├─ Authorization (RBAC): Checks user permissions
├─ Admission Control: Validates request
│   ├─ MutatingAdmissionWebhook: Modifies object
│   └─ ValidatingAdmissionWebhook: Validates object
├─ Schema Validation: Ensures proper format
└─ Persists to etcd
```

**3. API Server → etcd**
```
etcd:
- Stores Deployment object
- Returns success to API Server
- Triggers watch notifications
```

**4. Deployment Controller (in Controller Manager)**
```
Deployment Controller:
├─ Watches for Deployment events
├─ Sees new Deployment created
├─ Creates ReplicaSet object
└─ Sends ReplicaSet creation to API Server
```

**5. ReplicaSet Controller**
```
ReplicaSet Controller:
├─ Watches for ReplicaSet events
├─ Sees new ReplicaSet (desired: 3 replicas, current: 0)
├─ Creates 3 Pod objects
└─ Sends Pod creation requests to API Server
```

**6. Scheduler**
```
Scheduler:
├─ Watches for Pods with nodeName=""
├─ Sees 3 unscheduled Pods
├─ For each Pod:
│   ├─ Filters nodes (predicates)
│   │   ├─ Has enough CPU/memory?
│   │   ├─ Matches nodeSelector?
│   │   └─ Passes taints/tolerations?
│   ├─ Scores nodes (priorities)
│   │   ├─ Resource balance
│   │   ├─ Spreading pods
│   │   └─ Node affinity
│   └─ Binds Pod to best node (updates nodeName)
└─ Sends binding to API Server
```

**7. Kubelet (on selected node)**
```
Kubelet:
├─ Watches for Pods assigned to its node
├─ Sees new Pod assignment
├─ Pulls container image from registry
├─ Calls Container Runtime Interface (CRI)
│   └─ Container Runtime (containerd) creates container
├─ Monitors container status
└─ Reports status back to API Server
```

**8. Kube-Proxy**
```
Kube-Proxy:
├─ Watches for Service and Endpoints changes
├─ Updates iptables/IPVS rules
└─ Enables network routing to pods
```

**Final State:**
```
etcd contains:
├─ Deployment: nginx (replicas: 3)
├─ ReplicaSet: nginx-xxxxxxxxx (replicas: 3)
└─ Pods:
    ├─ nginx-xxxxxxxxx-aaaaa (node: worker-1, status: Running)
    ├─ nginx-xxxxxxxxx-bbbbb (node: worker-2, status: Running)
    └─ nginx-xxxxxxxxx-ccccc (node: worker-3, status: Running)
```

---

**Scenario 2: Scaling a Deployment**

```bash
kubectl scale deployment nginx --replicas=5
```

**Component Interactions:**

**1. kubectl → API Server**
- Updates Deployment spec.replicas to 5

**2. API Server → etcd**
- Stores updated Deployment

**3. Deployment Controller**
```
Deployment Controller:
├─ Detects Deployment change
├─ Updates ReplicaSet replicas to 5
└─ API Server persists change
```

**4. ReplicaSet Controller**
```
ReplicaSet Controller:
├─ Detects desired: 5, current: 3
├─ Creates 2 new Pod objects
└─ API Server persists Pods
```

**5. Scheduler → Kubelet**
- Assigns new pods to nodes
- Kubelets start new containers

---

**Scenario 3: Pod Failure and Self-Healing**

**Event:** Container crashes on worker-1

**1. Kubelet (worker-1)**
```
Kubelet:
├─ Detects container exit (crash)
├─ Restarts container (if restartPolicy allows)
├─ If restart fails repeatedly:
│   └─ Marks Pod as CrashLoopBackOff
└─ Reports status to API Server
```

**2. API Server → etcd**
- Updates Pod status

**3. ReplicaSet Controller**
```
ReplicaSet Controller:
├─ Watches Pod status
├─ Detects: desired: 5, ready: 4
├─ If Pod unrecoverable:
│   └─ Creates new replacement Pod
└─ API Server persists new Pod
```

**4. Scheduler**
- Assigns new Pod to healthy node

**5. Kubelet (new node)**
- Starts new container

---

**Scenario 4: Exposing Deployment with Service**

```bash
kubectl expose deployment nginx --port=80 --type=LoadBalancer
```

**1. kubectl → API Server**
- Creates Service object

**2. API Server → etcd**
- Stores Service

**3. Endpoints Controller**
```
Endpoints Controller:
├─ Watches for Service creation
├─ Finds Pods matching Service selector
├─ Creates Endpoints object with Pod IPs
└─ API Server persists Endpoints
```

**4. Kube-Proxy (all nodes)**
```
Kube-Proxy:
├─ Watches Service and Endpoints
├─ Creates iptables/IPVS rules:
│   Service ClusterIP → Pod IPs
└─ Enables load balancing
```

**5. Cloud Controller Manager**
```
Cloud Controller (for LoadBalancer type):
├─ Detects new LoadBalancer Service
├─ Calls cloud provider API (AWS, GCP, Azure)
├─ Creates external load balancer
├─ Updates Service with external IP
└─ API Server persists external IP
```

---

**Scenario 5: Node Failure**

**Event:** worker-2 becomes unreachable

**1. Kubelet (worker-2)**
- Stops sending heartbeats to API Server

**2. Node Controller**
```
Node Controller:
├─ Monitors node heartbeats
├─ Detects missed heartbeats
├─ Marks node as NotReady after 40s
├─ Waits 5 minutes (pod-eviction-timeout)
└─ Marks pods for eviction
```

**3. API Server → etcd**
- Updates node status: NotReady
- Marks pods for deletion

**4. ReplicaSet Controller**
```
ReplicaSet Controller:
├─ Detects pods on failed node
├─ Desired: 5, Ready: 3 (2 on failed node)
├─ Creates 2 replacement Pods
└─ API Server persists new Pods
```

**5. Scheduler**
- Assigns replacement pods to healthy nodes

**6. Kubelets (healthy nodes)**
- Start replacement containers

---

**Component Communication Protocols:**

**API Server ↔ etcd:**
- gRPC
- Watch mechanism for real-time updates

**kubectl/Controllers/Scheduler ↔ API Server:**
- HTTPS REST API
- Watch API for event streaming

**API Server ↔ Kubelet:**
- HTTPS (API server → kubelet for logs, exec)
- Kubelet → API Server for status updates

**Kube-Proxy:**
- Watches API Server
- Modifies local iptables/IPVS (doesn't communicate with other components)

---

**Data Flow Summary:**

```
┌────────────────────────────────────────────┐
│  All state changes go through API Server   │
│  API Server is the ONLY component that     │
│  directly communicates with etcd           │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│  Controllers watch API Server for events   │
│  Controllers are level-triggered:          │
│  - Continuously reconcile desired vs actual│
│  - Handle events asynchronously            │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│  Kubelet is the agent of API Server        │
│  - Executes pod specifications             │
│  - Reports node and pod status             │
│  - Only component that talks to container  │
│    runtime                                 │
└────────────────────────────────────────────┘
```

---

### What is Kubernetes DNS, and how does it handle service discovery?

**Detailed Explanation:**

**Kubernetes DNS** is a cluster add-on that provides name resolution for services and pods within the cluster. It enables service discovery through DNS rather than hardcoding IP addresses.

**DNS Implementation:**

Kubernetes uses **CoreDNS** (formerly kube-dns) as the default DNS server.

**CoreDNS Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coredns
  namespace: kube-system
spec:
  replicas: 2
  selector:
    matchLabels:
      k8s-app: kube-dns
  template:
    metadata:
      labels:
        k8s-app: kube-dns
    spec:
      containers:
      - name: coredns
        image: coredns/coredns:1.10.1
        args: [ "-conf", "/etc/coredns/Corefile" ]
        volumeMounts:
        - name: config-volume
          mountPath: /etc/coredns
---
apiVersion: v1
kind: Service
metadata:
  name: kube-dns
  namespace: kube-system
spec:
  clusterIP: 10.96.0.10  # Configured in kubelet
  selector:
    k8s-app: kube-dns
  ports:
  - name: dns
    port: 53
    protocol: UDP
  - name: dns-tcp
    port: 53
    protocol: TCP
```

---

**DNS Records Created by Kubernetes:**

### **1. Service DNS Records**

**Format:**
```
<service-name>.<namespace>.svc.cluster.local
```

**Example:**
```yaml
# Service in default namespace
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: default
spec:
  clusterIP: 10.96.10.50
  selector:
    app: backend
  ports:
  - port: 80
```

**DNS Records Created:**
```
backend.default.svc.cluster.local     → 10.96.10.50  (A record)
backend.default.svc                    → 10.96.10.50  (A record)
backend.default                        → 10.96.10.50  (A record)
backend                                → 10.96.10.50  (A record, from same namespace)

# SRV record for named ports
_http._tcp.backend.default.svc.cluster.local  → backend.default.svc.cluster.local:80
```

**From Another Pod in Same Namespace:**
```bash
# All of these work:
curl http://backend:80
curl http://backend.default:80
curl http://backend.default.svc:80
curl http://backend.default.svc.cluster.local:80
```

**From Another Namespace:**
```bash
# Must include namespace:
curl http://backend.default:80
curl http://backend.default.svc.cluster.local:80
```

### **2. Headless Service DNS Records**

Headless services (ClusterIP: None) return pod IPs directly instead of service IP.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: database
  namespace: production
spec:
  clusterIP: None  # Headless
  selector:
    app: postgres
  ports:
  - port: 5432
```

**DNS Records:**
```
database.production.svc.cluster.local  → 10.244.1.5, 10.244.2.8, 10.244.3.12
                                          (Returns all pod IPs)

# Individual pod DNS
postgres-0.database.production.svc.cluster.local  → 10.244.1.5
postgres-1.database.production.svc.cluster.local  → 10.244.2.8
postgres-2.database.production.svc.cluster.local  → 10.244.3.12
```

**Use Case:** StatefulSets, databases with direct pod addressing

### **3. Pod DNS Records**

Pods get DNS records if they belong to a service.

**Format:**
```
<pod-ip-with-dashes>.<namespace>.pod.cluster.local
```

**Example:**
Pod with IP 10.244.1.5:
```
10-244-1-5.default.pod.cluster.local  → 10.244.1.5
```

**For StatefulSets with Headless Service:**
```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
```

**Example:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: nginx
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
```

**DNS Records:**
```
web-0.nginx.default.svc.cluster.local  → Pod 0 IP
web-1.nginx.default.svc.cluster.local  → Pod 1 IP
web-2.nginx.default.svc.cluster.local  → Pod 2 IP
```

---

**How DNS Resolution Works:**

### **Pod DNS Configuration**

Every pod gets DNS configuration injected:

```bash
# Inside a pod:
cat /etc/resolv.conf
```

```
nameserver 10.96.0.10           # CoreDNS service IP
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

**Search Domains Explanation:**

When you query `backend`, DNS tries in order:
1. `backend.default.svc.cluster.local`
2. `backend.svc.cluster.local`
3. `backend.cluster.local`
4. `backend` (external DNS)

**ndots:5** means if query has < 5 dots, try search domains first.

---

### **Service Discovery Flow**

**Scenario:** Pod in `frontend` namespace calls `backend.production`

```
┌─────────────────────────────────────────────┐
│  1. App makes request                       │
│     GET http://backend.production/api       │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│  2. Pod's /etc/resolv.conf consulted        │
│     Search domain: frontend.svc.cluster.local│
│     Nameserver: 10.96.0.10 (CoreDNS)       │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│  3. DNS Query sent to CoreDNS               │
│     backend.production.svc.cluster.local    │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│  4. CoreDNS queries Kubernetes API          │
│     Looks up Service "backend" in namespace │
│     "production"                            │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│  5. CoreDNS returns Service ClusterIP       │
│     10.96.20.100                            │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│  6. App connects to 10.96.20.100            │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────┐
│  7. kube-proxy (iptables) routes to pod     │
│     DNAT: 10.96.20.100:80 → 10.244.2.15:8080│
└─────────────────────────────────────────────┘
```

---

**CoreDNS Configuration:**

```yaml
# CoreDNS Corefile
.:53 {
    errors
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
       max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

**Key Plugins:**

- **kubernetes:** Resolves cluster.local DNS
- **forward:** Forwards external DNS queries to upstream
- **cache:** Caches DNS responses (30s TTL)
- **errors:** Error logging
- **ready/health:** Health check endpoints

---

**External DNS Resolution:**

For queries not in `cluster.local` (e.g., `google.com`):

```
Pod → CoreDNS → Forward plugin → Upstream DNS (e.g., 8.8.8.8)
```

CoreDNS uses node's `/etc/resolv.conf` for upstream servers.

---

**Advanced DNS Features:**

### **1. Custom DNS Configuration**

Override pod DNS settings:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-dns
spec:
  dnsPolicy: "None"
  dnsConfig:
    nameservers:
      - 8.8.8.8
      - 8.8.4.4
    searches:
      - my-custom-domain.com
    options:
      - name: ndots
        value: "2"
  containers:
  - name: app
    image: nginx
```

**DNS Policies:**
- **ClusterFirst** (default): Use cluster DNS, fallback to node DNS
- **Default**: Use node's DNS settings
- **ClusterFirstWithHostNet**: For pods using hostNetwork
- **None**: Use custom dnsConfig

### **2. ExternalName Services**

Create DNS CNAME record:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-database
spec:
  type: ExternalName
  externalName: database.example.com
```

**DNS Resolution:**
```
external-database.default.svc.cluster.local  → CNAME database.example.com
                                             → Resolves to external IP
```

**Use Case:** Migrate external service to Kubernetes without code changes

---

**Troubleshooting DNS:**

### **1. Test DNS Resolution from Pod**

```bash
# Start debug pod
kubectl run -it --rm debug --image=busybox --restart=Never -- sh

# Inside pod:
nslookup kubernetes.default
nslookup backend.production

# Check resolv.conf
cat /etc/resolv.conf

# Test CoreDNS directly
nslookup kubernetes.default.svc.cluster.local 10.96.0.10
```

### **2. Check CoreDNS Status**

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

### **3. Common Issues**

**DNS Resolution Fails:**
- CoreDNS pods not running
- Network policy blocking DNS traffic (port 53)
- CoreDNS ConfigMap misconfigured

**Slow DNS:**
- ndots:5 causes unnecessary queries
- Reduce ndots or use FQDN with trailing dot:
  ```bash
  curl http://backend.default.svc.cluster.local.
  #                                            ^ prevents search domain expansion
  ```

**Service Not Found:**
- Service doesn't exist in specified namespace
- Wrong service name
- Check: `kubectl get svc -A | grep <service-name>`

---

**Performance Optimization:**

### **1. Use Shorter Names**

```bash
# Same namespace: Use short name
curl http://backend

# Cross-namespace: Use FQDN
curl http://backend.production.svc.cluster.local.
```

### **2. DNS Caching**

CoreDNS caches for 30s by default. For high-traffic services, this is sufficient.

### **3. NodeLocal DNSCache**

Deploy local DNS cache on each node:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-local-dns
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: node-local-dns
  template:
    spec:
      containers:
      - name: node-cache
        image: k8s.gcr.io/dns/k8s-dns-node-cache:1.22.20
        # Caches on link-local IP: 169.254.20.10
```

**Benefits:**
- Reduces latency
- Reduces load on CoreDNS
- Improves reliability

---

**Service Discovery Patterns:**

### **1. Environment Variables (Legacy)**

Kubernetes injects service info as env vars:

```bash
# For service "backend" in same namespace:
BACKEND_SERVICE_HOST=10.96.10.50
BACKEND_SERVICE_PORT=80
```

**Limitation:** Only for services created before pod

### **2. DNS (Recommended)**

Always use DNS for flexibility and dynamic discovery.

### **3. Service Mesh (Advanced)**

Istio/Linkerd provide advanced service discovery with:
- Automatic mTLS
- Traffic management
- Observability

---

This covers comprehensive DNS and service discovery mechanics in Kubernetes. The key takeaway is that DNS provides a stable abstraction over dynamic pod IPs, enabling microservices to discover and communicate with each other reliably.

---

### How do Kubernetes pods detect and recover from health issues?

**Detailed Explanation:**

Kubernetes provides three types of health checks (probes) to monitor and recover from pod failures:

1. **Liveness Probe** - Is the container alive?
2. **Readiness Probe** - Is the container ready to serve traffic?
3. **Startup Probe** - Has the container finished starting?

---

## **1. Liveness Probe**

**Purpose:** Detect if container is in a broken state and needs restart.

**When to use:**
- Application deadlocks (process runs but doesn't respond)
- Memory leaks causing crashes
- Infinite loops or hung threads

**Actions on Failure:**
- Kubelet restarts the container
- Follows pod's `restartPolicy`

**Example:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: liveness-example
spec:
  containers:
  - name: app
    image: myapp:1.0
    ports:
    - containerPort: 8080

    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
        httpHeaders:
        - name: Custom-Header
          value: Awesome
      initialDelaySeconds: 15  # Wait before first probe
      periodSeconds: 10        # Check every 10 seconds
      timeoutSeconds: 5        # Probe timeout
      successThreshold: 1      # 1 success = healthy
      failureThreshold: 3      # 3 failures = restart
```

**How it Works:**

```
Container starts
        ↓
Wait 15s (initialDelaySeconds)
        ↓
Probe every 10s (periodSeconds)
        ↓
┌─────────────────────────────────┐
│ Is GET /healthz returning 200?  │
│ Within 5s? (timeoutSeconds)     │
└─────────────────────────────────┘
        │
        ├─ Yes (1 success) → Container healthy
        │
        └─ No (3 failures) → Kubelet kills container
                            → Starts new container
```

**Probe Types:**

### **HTTP GET**
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
    scheme: HTTP  # or HTTPS
  initialDelaySeconds: 10
  periodSeconds: 5
```

**Application Implementation:**
```python
# Python Flask example
from flask import Flask
app = Flask(__name__)

@app.route('/healthz')
def health():
    # Check critical components
    if database_connection_ok() and cache_available():
        return "OK", 200
    else:
        return "Unhealthy", 500
```

### **TCP Socket**
```yaml
livenessProbe:
  tcpSocket:
    port: 3306
  initialDelaySeconds: 15
  periodSeconds: 20
```

**Use case:** Databases, Redis, services without HTTP endpoints

### **Exec Command**
```yaml
livenessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

**Use case:** Custom health logic, file-based checks

---

## **2. Readiness Probe**

**Purpose:** Detect if container is ready to accept traffic.

**Difference from Liveness:**
- **Liveness**: Is app alive? → Restart if not
- **Readiness**: Is app ready to serve requests? → Remove from service if not

**When to use:**
- Warming up caches
- Loading large datasets
- Waiting for dependencies
- Graceful shutdown/startup
- Temporary overload

**Actions on Failure:**
- Pod removed from Service endpoints
- No traffic routed to pod
- Container NOT restarted

**Example:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readiness-example
spec:
  containers:
  - name: app
    image: myapp:1.0
    ports:
    - containerPort: 8080

    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 3
      failureThreshold: 1  # Immediately remove from service
```

**How it Works:**

```
Container starts
        ↓
Kubelet starts readiness probes
        ↓
┌─────────────────────────────────┐
│ Is GET /ready returning 200?    │
└─────────────────────────────────┘
        │
        ├─ Yes → Add pod to Service endpoints
        │       → Traffic routed to pod
        │
        └─ No  → Remove pod from Service endpoints
                → No traffic sent to pod
                → Keep checking
```

**Real-World Scenario:**

```yaml
# Application needs 30s to warm up cache
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: api:v1
        ports:
        - containerPort: 8080

        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5

        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60  # Give time to start
          periodSeconds: 10
```

**Application Implementation:**

```python
from flask import Flask
import time

app = Flask(__name__)
start_time = time.time()

@app.route('/ready')
def readiness():
    # Check if cache is warmed up
    if cache.is_ready() and time.time() - start_time > 30:
        return "Ready", 200
    else:
        return "Not Ready", 503

@app.route('/health')
def liveness():
    # Check if app is alive
    if app.is_running():
        return "Alive", 200
    else:
        return "Dead", 500
```

**Service Endpoint Impact:**

```bash
# Check service endpoints
kubectl get endpoints my-service

NAME         ENDPOINTS                           AGE
my-service   10.244.1.5:8080,10.244.2.8:8080    5m

# If one pod fails readiness probe:
kubectl get endpoints my-service

NAME         ENDPOINTS           AGE
my-service   10.244.2.8:8080    5m
```

---

## **3. Startup Probe**

**Purpose:** Handle slow-starting containers without affecting liveness probe.

**Problem it Solves:**

Before startup probes, you had to set high `initialDelaySeconds` on liveness probes for slow-starting apps, which delayed failure detection.

**When to use:**
- Legacy applications with long startup times
- Applications loading large datasets
- Cold starts in serverless

**Example:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: startup-example
spec:
  containers:
  - name: slow-app
    image: legacy-app:1.0
    ports:
    - containerPort: 8080

    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      failureThreshold: 30   # 30 * 10 = 300s (5 min) to start
      periodSeconds: 10

    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      periodSeconds: 10      # Can be aggressive since startup probe handles slow start

    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      periodSeconds: 5
```

**How it Works:**

```
Container starts
        ↓
Startup probe runs (liveness/readiness disabled)
        ↓
Probe every 10s, up to 30 times (5 minutes)
        ↓
┌─────────────────────────────────┐
│ Did startup probe succeed?       │
└─────────────────────────────────┘
        │
        ├─ Yes → Enable liveness/readiness probes
        │       → Container considered started
        │
        └─ No (after 30 failures) → Kill container
                                   → Restart
```

---

## **Probe Parameters:**

```yaml
probe:
  httpGet | tcpSocket | exec: ...

  initialDelaySeconds: 0    # Wait before first probe (default: 0)
  periodSeconds: 10         # How often to probe (default: 10)
  timeoutSeconds: 1         # Probe timeout (default: 1)
  successThreshold: 1       # Successes needed to mark healthy (default: 1)
                           # Must be 1 for liveness/startup
  failureThreshold: 3       # Failures before action (default: 3)
```

**Calculations:**

Maximum startup time before kill:
```
initialDelaySeconds + (failureThreshold × periodSeconds)
```

Example:
```yaml
startupProbe:
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 30

# Max startup time: 10 + (30 × 5) = 160 seconds
```

---

## **Best Practices:**

### **1. Separate Liveness and Readiness Logic**

```python
# GOOD
@app.route('/health')
def liveness():
    # Simple check - is process alive?
    return "OK", 200

@app.route('/ready')
def readiness():
    # Complex checks - can I serve traffic?
    if db.ping() and cache.connected() and not overloaded():
        return "Ready", 200
    return "Not Ready", 503
```

### **2. Avoid Heavy Checks in Liveness**

```python
# BAD - Liveness probe too complex
@app.route('/health')
def liveness():
    # Complex database query
    if database.query("SELECT COUNT(*) FROM users") > 0:
        return "OK", 200
    return "Error", 500

# GOOD - Liveness probe lightweight
@app.route('/health')
def liveness():
    # Simple check
    return "OK", 200
```

### **3. Set Appropriate Timeouts**

```yaml
# For fast services:
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 3
  timeoutSeconds: 2
  failureThreshold: 1  # Remove from service immediately

# For slow services:
readinessProbe:
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### **4. Use Startup Probe for Slow Starts**

```yaml
# BEFORE (without startup probe):
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 180  # Wait 3 minutes - delays failure detection

# AFTER (with startup probe):
startupProbe:
  httpGet:
    path: /startup
    port: 8080
  failureThreshold: 30
  periodSeconds: 10

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 10  # Can check frequently after startup
```

---

## **Recovery Scenarios:**

### **Scenario 1: Application Deadlock**

```
Application deadlocks (no crash, but not responding)
                    ↓
Liveness probe fails (3 consecutive failures)
                    ↓
Kubelet kills container
                    ↓
Container restarts
                    ↓
Startup probe succeeds
                    ↓
Liveness probe succeeds
                    ↓
Readiness probe succeeds
                    ↓
Pod added back to Service endpoints
                    ↓
Application healthy
```

### **Scenario 2: Temporary Overload**

```
Application overloaded (too many requests)
                    ↓
Readiness probe returns 503
                    ↓
Pod removed from Service endpoints
                    ↓
No new traffic routed to pod
                    ↓
Application recovers (processes backlog)
                    ↓
Readiness probe returns 200
                    ↓
Pod added back to Service endpoints
                    ↓
Gradual traffic restoration
```

### **Scenario 3: Database Connection Lost**

```
Application loses database connection
                    ↓
Readiness probe fails (can't serve traffic)
                    ↓
Pod removed from Service (traffic goes to healthy pods)
                    ↓
Liveness probe still passes (app is alive)
                    ↓
App reconnects to database
                    ↓
Readiness probe passes
                    ↓
Pod added back to Service
```

---

## **Monitoring and Debugging:**

### **Check Probe Status:**

```bash
# View pod events
kubectl describe pod <pod-name>

# Look for:
Events:
  Type     Reason     Message
  ----     ------     -------
  Warning  Unhealthy  Liveness probe failed: Get http://10.244.1.5:8080/health: dial tcp 10.244.1.5:8080: connect: connection refused
  Normal   Killing    Container app failed liveness probe, will be restarted
```

### **View Probe Configuration:**

```bash
kubectl get pod <pod-name> -o yaml | grep -A 10 "livenessProbe"
```

### **Check Restart Count:**

```bash
kubectl get pods

NAME        READY   STATUS    RESTARTS   AGE
my-app-xyz  1/1     Running   15         1h  # High restarts = probe issue
```

### **Test Probe Manually:**

```bash
# HTTP probe
kubectl exec <pod-name> -- curl -f http://localhost:8080/health

# TCP probe
kubectl exec <pod-name> -- nc -zv localhost 3306

# Exec probe
kubectl exec <pod-name> -- cat /tmp/healthy
```

---

## **Common Pitfalls:**

### **1. Liveness Probe Too Aggressive**

```yaml
# BAD - Will kill healthy pods
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5   # Too short
  periodSeconds: 5
  failureThreshold: 1      # Too aggressive
  timeoutSeconds: 1
```

### **2. Readiness Probe Not Configured**

Without readiness probe, traffic sent to pod immediately on start:
- Errors for clients
- Increased latency
- Failed requests during startup

### **3. Probe Endpoint Too Slow**

```python
# BAD - Slow probe
@app.route('/health')
def health():
    # Complex query taking 10 seconds
    result = database.execute("SELECT * FROM large_table")
    return "OK", 200

# GOOD - Fast probe
@app.route('/health')
def health():
    # Simple check
    return "OK", 200
```

### **4. Not Handling Graceful Shutdown**

```python
# GOOD - Return not ready during shutdown
import signal

shutting_down = False

def handle_sigterm(signum, frame):
    global shutting_down
    shutting_down = True

signal.signal(signal.SIGTERM, handle_sigterm)

@app.route('/ready')
def readiness():
    if shutting_down:
        return "Shutting down", 503
    return "Ready", 200
```

---

This comprehensive coverage shows how Kubernetes uses probes for self-healing and maintaining application health. Proper probe configuration is critical for production reliability.

---

### What are StatefulSets in Kubernetes?

**Detailed Explanation:**

**StatefulSet** is a Kubernetes workload resource used for managing stateful applications that require:
- Stable, unique network identifiers
- Stable, persistent storage
- Ordered, graceful deployment and scaling
- Ordered, automated rolling updates

---

## **StatefulSet vs Deployment:**

| Feature | Deployment | StatefulSet |
|---------|-----------|-------------|
| Pod Names | Random (nginx-7d8b49c-xyz) | Ordered (nginx-0, nginx-1, nginx-2) |
| Pod Identity | Ephemeral | Persistent (survives rescheduling) |
| Network Identity | Changes on restart | Stable hostname |
| Storage | Shared or ephemeral | Persistent per pod |
| Scaling | Parallel | Sequential (0→1→2) |
| Updates | Rolling (any order) | Ordered (reverse: 2→1→0) |
| Use Case | Stateless apps | Databases, queues, clustered apps |

---

## **StatefulSet Basics:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None  # Headless service (required for StatefulSet)
  selector:
    app: nginx
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: "nginx"  # Must match headless service
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: www
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:  # Persistent storage per pod
  - metadata:
      name: www
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "standard"
      resources:
        requests:
          storage: 1Gi
```

---

## **Key Features:**

### **1. Stable Network Identity**

**Pods get predictable names:**
```
<statefulset-name>-<ordinal>
web-0
web-1
web-2
```

**Each pod gets stable DNS hostname:**
```
<pod-name>.<service-name>.<namespace>.svc.cluster.local

web-0.nginx.default.svc.cluster.local
web-1.nginx.default.svc.cluster.local
web-2.nginx.default.svc.cluster.local
```

**DNS remains same even if pod is rescheduled to different node.**

**Example: MongoDB Replica Set**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
spec:
  serviceName: "mongodb"
  replicas: 3
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongo
        image: mongo:5.0
        command:
        - mongod
        - "--replSet"
        - rs0
        - "--bind_ip_all"
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: mongo-data
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: mongo-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

**Initialize replica set:**
```javascript
// Connect to mongodb-0
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongodb-0.mongodb.default.svc.cluster.local:27017" },
    { _id: 1, host: "mongodb-1.mongodb.default.svc.cluster.local:27017" },
    { _id: 2, host: "mongodb-2.mongodb.default.svc.cluster.local:27017" }
  ]
});
```

Hostnames remain stable even if pods restart.

---

### **2. Stable, Persistent Storage**

**Each pod gets dedicated PersistentVolumeClaim:**

```
StatefulSet: web (3 replicas)
VolumeClaimTemplate: www (1Gi)

Creates:
├─ PVC: www-web-0 → PV-1 → Pod web-0
├─ PVC: www-web-1 → PV-2 → Pod web-1
└─ PVC: www-web-2 → PV-3 → Pod web-2
```

**PVCs persist even when pods are deleted:**

```bash
kubectl delete pod web-0

# New pod web-0 created
# Binds to SAME PVC www-web-0
# Data persists across pod restarts
```

**Verify:**
```bash
kubectl get pvc

NAME        STATUS   VOLUME                                     CAPACITY
www-web-0   Bound    pvc-xxx-xxx-xxx                           1Gi
www-web-1   Bound    pvc-yyy-yyy-yyy                           1Gi
www-web-2   Bound    pvc-zzz-zzz-zzz                           1Gi
```

---

### **3. Ordered Deployment and Scaling**

**Deployment Order:**

```
Scale up (0 → 3):
1. Create web-0
2. Wait for web-0 to be Running and Ready
3. Create web-1
4. Wait for web-1 to be Running and Ready
5. Create web-2
```

**Scale Down Order:**

```
Scale down (3 → 1):
1. Delete web-2
2. Wait for web-2 to be fully terminated
3. Delete web-1
4. Wait for web-1 to be fully terminated
5. web-0 remains
```

**Observe scaling:**

```bash
# Scale up
kubectl scale statefulset web --replicas=5

kubectl get pods -w  # Watch mode

NAME    READY   STATUS    AGE
web-0   1/1     Running   10m
web-1   0/1     Pending   0s   # Creating in order
web-1   0/1     ContainerCreating   1s
web-1   1/1     Running   15s
web-2   0/1     Pending   0s   # Next one starts
web-2   0/1     ContainerCreating   1s
web-2   1/1     Running   15s
# ... continues sequentially
```

---

### **4. Ordered Rolling Updates**

**Update Strategy:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0  # Update pods >= partition
```

**Update process (reverse ordinal order):**

```bash
kubectl set image statefulset/web nginx=nginx:1.22

# Updates in order:
1. Delete and recreate web-2
2. Wait for web-2 to be Running and Ready
3. Delete and recreate web-1
4. Wait for web-1 to be Running and Ready
5. Delete and recreate web-0
```

**Phased Rollout using partition:**

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2  # Only update pods with ordinal >= 2
```

```bash
# Update image
kubectl set image statefulset/web nginx=nginx:1.22

# Only web-2 gets updated (ordinal 2 >= partition 2)
# web-0 and web-1 remain on old version

# After testing web-2:
kubectl patch statefulset web -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":0}}}}'

# Now web-1 and web-0 get updated
```

---

## **Use Cases:**

### **1. Databases**

**MySQL Cluster:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      initContainers:
      - name: init-mysql
        image: mysql:8.0
        command:
        - bash
        - "-c"
        - |
          set -ex
          # Generate server-id from pod ordinal
          [[ `hostname` =~ -([0-9]+)$ ]] || exit 1
          ordinal=${BASH_REMATCH[1]}
          echo [mysqld] > /mnt/conf.d/server-id.cnf
          echo server-id=$((100 + $ordinal)) >> /mnt/conf.d/server-id.cnf
        volumeMounts:
        - name: conf
          mountPath: /mnt/conf.d
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        ports:
        - containerPort: 3306
          name: mysql
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
        - name: conf
          mountPath: /etc/mysql/conf.d
      volumes:
      - name: conf
        emptyDir: {}
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

### **2. Message Queues**

**Kafka Cluster:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
spec:
  serviceName: kafka
  replicas: 3
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:7.0.0
        ports:
        - containerPort: 9092
          name: kafka
        env:
        - name: KAFKA_BROKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: KAFKA_ZOOKEEPER_CONNECT
          value: "zookeeper:2181"
        - name: KAFKA_ADVERTISED_LISTENERS
          value: PLAINTEXT://$(POD_NAME).kafka.default.svc.cluster.local:9092
        volumeMounts:
        - name: kafka-data
          mountPath: /var/lib/kafka/data
  volumeClaimTemplates:
  - metadata:
      name: kafka-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 20Gi
```

### **3. Distributed Caches**

**Redis Cluster:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 6
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.0
        command:
        - redis-server
        - "--cluster-enabled"
        - "yes"
        - "--cluster-config-file"
        - "/data/nodes.conf"
        ports:
        - containerPort: 6379
          name: client
        - containerPort: 16379
          name: gossip
        volumeMounts:
        - name: redis-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 1Gi
```

---

## **Headless Service (Required)**

StatefulSets require a headless service (clusterIP: None) to provide network identity.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  clusterIP: None  # Headless
  selector:
    app: nginx
  ports:
  - port: 80
```

**Headless service creates:**
- DNS A records for each pod
- No load balancing (connects directly to pod IP)

**Regular service (for external access):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-public
spec:
  type: LoadBalancer  # Regular service for load balancing
  selector:
    app: nginx
  ports:
  - port: 80
```

---

## **StatefulSet Lifecycle:**

### **Pod Management Policy:**

```yaml
spec:
  podManagementPolicy: OrderedReady  # Default
  # OR
  podManagementPolicy: Parallel
```

**OrderedReady (Default):**
- Pods created sequentially
- Waits for previous pod to be ready
- Guarantees ordering

**Parallel:**
- Creates all pods simultaneously
- No ordering guarantee
- Faster startup
- Use when pods don't depend on each other

---

## **Deleting StatefulSets:**

### **Cascade Delete (Default):**

```bash
kubectl delete statefulset web

# Deletes StatefulSet and all pods
# PVCs remain (must delete manually)
```

### **Non-Cascade Delete:**

```bash
kubectl delete statefulset web --cascade=orphan

# Deletes StatefulSet only
# Pods remain running
# Can recreate StatefulSet with same name - pods rejoin
```

### **Delete PVCs:**

```bash
kubectl delete pvc -l app=nginx

# Or delete individually:
kubectl delete pvc www-web-0 www-web-1 www-web-2
```

---

## **Best Practices:**

### **1. Always Use Headless Service**

```yaml
# Required for StatefulSet
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  clusterIP: None
  selector:
    app: mysql
  ports:
  - port: 3306
```

### **2. Set Resource Limits**

```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### **3. Use ReadinessProbe**

Ensures sequential startup waits for pod readiness:

```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

### **4. Configure PodDisruptionBudget**

Prevent too many pods from being down during voluntary disruptions:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: nginx
```

### **5. Use Init Containers for Setup**

```yaml
spec:
  template:
    spec:
      initContainers:
      - name: setup
        image: busybox
        command: ['/bin/sh', '-c']
        args:
        - |
          # Extract ordinal from hostname
          ordinal=${HOSTNAME##*-}
          echo "Pod ordinal: $ordinal"
          # Perform setup based on ordinal
        volumeMounts:
        - name: config
          mountPath: /config
```

---

## **Troubleshooting:**

### **Pod Stuck in Pending:**

```bash
kubectl describe pod web-0

# Check:
# - PVC bound?
# - Node has storage available?
# - StorageClass exists?

kubectl get pvc www-web-0
kubectl describe pvc www-web-0
```

### **Pod Not Starting in Order:**

```bash
# Check previous pod is ready
kubectl get pods

NAME    READY   STATUS    AGE
web-0   0/1     Running   2m   # Not ready - web-1 won't start

# Check readiness probe
kubectl describe pod web-0
```

### **Rolling Update Stuck:**

```bash
# Check if pods are becoming ready
kubectl rollout status statefulset/web

# Check pod logs
kubectl logs web-2

# Check for failed health checks
kubectl describe pod web-2
```

### **Data Loss After Scale Down:**

PVCs persist even after scale down:

```bash
# Scale down from 5 to 3
kubectl scale statefulset web --replicas=3

# web-3 and web-4 deleted, but PVCs remain:
kubectl get pvc

NAME        STATUS   VOLUME
www-web-0   Bound    pvc-xxx
www-web-1   Bound    pvc-yyy
www-web-2   Bound    pvc-zzz
www-web-3   Bound    pvc-aaa  # Still exists!
www-web-4   Bound    pvc-bbb  # Still exists!

# Scale up again - pods reattach to same PVCs
kubectl scale statefulset web --replicas=5

# web-3 gets www-web-3 (data preserved)
# web-4 gets www-web-4 (data preserved)
```

---

StatefulSets are essential for running stateful workloads in Kubernetes, providing guarantees that Deployments cannot offer. They're the foundation for running databases, queues, and other clustered applications in Kubernetes.

---

### What is the difference between a Service and a Deployment in Kubernetes?

**Detailed Explanation:**

Services and Deployments are two fundamental but completely different Kubernetes objects that serve distinct purposes in your cluster architecture. Understanding the relationship between them is crucial for building reliable applications.

**Deployment - Application Lifecycle Management:**

A Deployment is a controller that manages the lifecycle of your application Pods. It's responsible for:

1. **Creating and Managing Pods**: Deployments create ReplicaSets, which in turn create Pods
2. **Scaling**: Increasing or decreasing the number of Pod replicas
3. **Rolling Updates**: Deploying new versions without downtime
4. **Rollbacks**: Reverting to previous versions when issues occur
5. **Self-Healing**: Replacing failed Pods automatically

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
```

When you create this Deployment:
- Kubernetes creates a ReplicaSet
- The ReplicaSet creates 3 Pods
- Each Pod gets a unique IP address (e.g., 10.244.1.5, 10.244.2.8, 10.244.3.12)
- If a Pod dies, the ReplicaSet creates a new one with a NEW IP address

**The Problem Deployments Don't Solve:**

Pod IPs are ephemeral - they change when Pods are recreated. How do clients connect to your application when IPs keep changing?

**Service - Network Abstraction Layer:**

A Service provides a stable network endpoint for accessing a set of Pods. It solves the dynamic IP problem by:

1. **Stable IP Address**: Services get a ClusterIP that never changes
2. **DNS Name**: Each Service gets a DNS entry (e.g., `web-app.default.svc.cluster.local`)
3. **Load Balancing**: Distributes traffic across healthy Pods
4. **Service Discovery**: Other applications can find your Pods using the Service name

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
spec:
  selector:
    app: web-app  # Matches Pods with this label
  ports:
  - protocol: TCP
    port: 80        # Service port
    targetPort: 80  # Pod port
  type: ClusterIP   # Internal only
```

**How They Work Together:**

```
Client Request
    |
    v
Service (stable IP: 10.96.0.10)
    |
    |-- Load Balances -->
    |
    +---> Pod 1 (10.244.1.5) \
    +---> Pod 2 (10.244.2.8)  } Managed by Deployment
    +---> Pod 3 (10.244.3.12)/
```

**Service Types:**

1. **ClusterIP (Default):**
```yaml
spec:
  type: ClusterIP
  # Accessible only within cluster
  # Gets internal IP: 10.96.0.10
```

2. **NodePort:**
```yaml
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080  # Accessible on every Node at <NodeIP>:30080
```

3. **LoadBalancer:**
```yaml
spec:
  type: LoadBalancer
  # Creates external load balancer (AWS ELB, GCP LB)
  # Gets external IP: 52.10.20.30
```

4. **ExternalName:**
```yaml
spec:
  type: ExternalName
  externalName: external-database.example.com
  # Returns CNAME record for external service
```

**Label Selector Mechanism:**

The Service finds Pods using label selectors:

```yaml
# Deployment creates Pods with labels
metadata:
  labels:
    app: web-app
    version: v1
    tier: frontend

# Service selects Pods
spec:
  selector:
    app: web-app  # All Pods with app=web-app
```

**Real-World Example:**

```bash
# Create Deployment
kubectl apply -f deployment.yaml

# Check Pods and their IPs
kubectl get pods -o wide
NAME                       READY   STATUS    IP
web-app-7d4b8c9f4d-abc12   1/1     Running   10.244.1.5
web-app-7d4b8c9f4d-def34   1/1     Running   10.244.2.8
web-app-7d4b8c9f4d-ghi56   1/1     Running   10.244.3.12

# Create Service
kubectl apply -f service.yaml

# Check Service
kubectl get svc
NAME              TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)
web-app-service   ClusterIP   10.96.0.10    <none>        80/TCP

# Service endpoints (Pods it routes to)
kubectl get endpoints web-app-service
NAME              ENDPOINTS
web-app-service   10.244.1.5:80,10.244.2.8:80,10.244.3.12:80

# Test connectivity
kubectl run test --rm -it --image=busybox -- /bin/sh
/ # wget -O- http://web-app-service
# Successfully connects to one of the Pods
```

**What Happens When a Pod Dies:**

```bash
# Delete a Pod
kubectl delete pod web-app-7d4b8c9f4d-abc12

# Deployment creates new Pod with NEW IP
kubectl get pods -o wide
NAME                       READY   STATUS    IP
web-app-7d4b8c9f4d-def34   1/1     Running   10.244.2.8
web-app-7d4b8c9f4d-ghi56   1/1     Running   10.244.3.12
web-app-7d4b8c9f4d-jkl78   1/1     Running   10.244.4.20  # NEW IP!

# Service automatically updates its endpoints
kubectl get endpoints web-app-service
NAME              ENDPOINTS
web-app-service   10.244.2.8:80,10.244.3.12:80,10.244.4.20:80

# Clients still connect using the same Service IP
# No configuration changes needed!
```

**Key Differences Summary:**

| Aspect | Deployment | Service |
|--------|-----------|---------|
| Purpose | Manage application lifecycle | Provide network access |
| Creates | Pods via ReplicaSets | Endpoints to Pods |
| IP Address | Pods get dynamic IPs | Service gets stable ClusterIP |
| Scaling | Controls number of replicas | Routes to all matching Pods |
| Updates | Rolling updates, rollbacks | No updates needed |
| Load Balancing | No | Yes |
| DNS Entry | No | Yes |

**Common Patterns:**

1. **Microservices Communication:**
```yaml
# Frontend Deployment + Service
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: frontend:v1
        env:
        - name: BACKEND_URL
          value: "http://backend-service:8080"  # Uses Service DNS
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer  # External access

# Backend Deployment + Service
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 5
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: backend:v1
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP  # Internal only
```

2. **Headless Service (No Load Balancing):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: database-headless
spec:
  clusterIP: None  # Headless
  selector:
    app: database
  ports:
  - port: 5432
```
Used when you need direct Pod-to-Pod communication (e.g., StatefulSets).

**Troubleshooting:**

```bash
# Service not routing traffic
kubectl get svc web-app-service
kubectl get endpoints web-app-service  # Check if Pods are listed

# No endpoints? Check label selectors
kubectl get pods --show-labels
kubectl describe svc web-app-service  # See selector

# Test Service connectivity
kubectl run debug --rm -it --image=busybox -- /bin/sh
/ # nslookup web-app-service  # DNS working?
/ # wget -O- http://web-app-service:80  # Can connect?

# Check Service from specific namespace
kubectl run debug -n other-namespace --rm -it --image=busybox -- /bin/sh
/ # wget -O- http://web-app-service.default.svc.cluster.local:80
```

**Best Practices:**

1. Always create a Service for Deployments that need network access
2. Use meaningful, consistent naming (e.g., `app-name` and `app-name-service`)
3. Match Service selectors exactly with Pod labels
4. Use ClusterIP for internal services, LoadBalancer for external
5. Set appropriate targetPort to match container port
6. Use readiness probes so Service only routes to healthy Pods
7. Consider using Ingress for HTTP/HTTPS routing instead of multiple LoadBalancers

---

## Docker / Containers

### What is Docker and how does it differ from virtual machines?

**Detailed Explanation:**

Docker is a containerization platform that packages applications and their dependencies into lightweight, portable containers. Understanding how it differs from virtual machines is fundamental to modern infrastructure.

**Docker Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    Host Operating System                 │
│                        (Linux/Windows)                   │
├─────────────────────────────────────────────────────────┤
│                      Docker Engine                       │
├──────────────┬──────────────┬──────────────┬────────────┤
│  Container 1 │  Container 2 │  Container 3 │Container 4 │
│              │              │              │            │
│  App A       │  App B       │  App C       │  App D     │
│  + Libs      │  + Libs      │  + Libs      │  + Libs    │
└──────────────┴──────────────┴──────────────┴────────────┘
```

**Virtual Machine Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    Host Operating System                 │
├─────────────────────────────────────────────────────────┤
│                        Hypervisor                        │
│                   (VMware, KVM, Hyper-V)                │
├──────────────┬──────────────┬──────────────┬────────────┤
│    VM 1      │    VM 2      │    VM 3      │    VM 4    │
│              │              │              │            │
│  Guest OS    │  Guest OS    │  Guest OS    │  Guest OS  │
│  (4-8 GB)    │  (4-8 GB)    │  (4-8 GB)    │  (4-8 GB)  │
│              │              │              │            │
│  App A       │  App B       │  App C       │  App D     │
│  + Libs      │  + Libs      │  + Libs      │  + Libs    │
└──────────────┴──────────────┴──────────────┴────────────┘
```

**Key Differences:**

**1. Operating System:**
- **VMs**: Each VM runs a complete guest OS (Windows, Linux) with its own kernel
- **Docker**: Containers share the host OS kernel, only package the application and libraries

**2. Resource Usage:**
```bash
# Virtual Machine
- OS: 4-8 GB RAM per VM
- Boot time: 30-60 seconds
- Disk: 10-100 GB per VM
- Running 10 VMs: ~50-80 GB RAM

# Docker Container
- OS: Shared kernel (0 MB overhead per container)
- Boot time: < 1 second
- Disk: 10-500 MB per container
- Running 10 containers: ~1-5 GB RAM
```

**3. Isolation Level:**
- **VMs**: Complete isolation via hardware virtualization (stronger security boundary)
- **Docker**: Process-level isolation via Linux namespaces and cgroups (lighter weight)

**4. Portability:**
- **VMs**: Platform-specific (different hypervisors, not easily portable)
- **Docker**: Write once, run anywhere (same container on dev laptop, staging, production)

**Docker Components:**

**1. Docker Image:**
A read-only template containing application code, runtime, libraries, and dependencies.

```dockerfile
# Dockerfile - Blueprint for building images
FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

# Set working directory
WORKDIR /app

# Copy application files
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .

# Define startup command
CMD ["python3", "app.py"]
```

```bash
# Build image from Dockerfile
docker build -t myapp:v1 .

# List images
docker images
REPOSITORY   TAG       IMAGE ID       SIZE
myapp        v1        abc123def456   150MB
ubuntu       20.04     xyz789abc123   72MB

# Image layers (each line in Dockerfile creates a layer)
docker history myapp:v1
```

**2. Docker Container:**
A running instance of an image.

```bash
# Run container from image
docker run -d \
  --name myapp-container \
  -p 8080:80 \
  -e DATABASE_URL=postgres://db:5432 \
  -v /host/data:/app/data \
  myapp:v1

# List running containers
docker ps
CONTAINER ID   IMAGE      STATUS       PORTS
abc123def456   myapp:v1   Up 5 mins    0.0.0.0:8080->80/tcp

# Execute command in running container
docker exec -it myapp-container /bin/bash

# View logs
docker logs myapp-container

# Stop and remove container
docker stop myapp-container
docker rm myapp-container
```

**3. Docker Registry:**
Storage and distribution system for Docker images.

```bash
# Docker Hub (public registry)
docker pull nginx:latest
docker tag myapp:v1 username/myapp:v1
docker push username/myapp:v1

# Private registry (AWS ECR, Google GCR, Azure ACR)
docker tag myapp:v1 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:v1
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:v1
```

**Docker Isolation Mechanisms:**

**1. Namespaces:**
Isolate process resources.

```bash
# PID namespace - separate process IDs
# Inside container: PID 1
# On host: PID 12345

# Network namespace - separate network stack
# Container has its own IP, ports, routing table

# Mount namespace - separate filesystem
# Container sees only its own filesystem

# UTS namespace - separate hostname
# Container can have different hostname than host

# IPC namespace - separate inter-process communication
# User namespace - separate user IDs
```

**2. Control Groups (cgroups):**
Limit resource usage.

```bash
# Limit CPU
docker run -d --cpus="1.5" myapp:v1

# Limit memory
docker run -d --memory="512m" myapp:v1

# Limit CPU shares (relative weight)
docker run -d --cpu-shares=512 myapp:v1
```

**3. Union File System:**
Layers enable efficient storage and sharing.

```
┌─────────────────────────────────┐
│    Container Layer (Read/Write) │ ← Changes made in container
├─────────────────────────────────┤
│    Application Layer (Read-Only)│ ← COPY . .
├─────────────────────────────────┤
│    Dependencies Layer           │ ← RUN pip install
├─────────────────────────────────┤
│    Base Image Layer             │ ← FROM ubuntu:20.04
└─────────────────────────────────┘

# Multiple containers share the same base layers
Container 1, Container 2, Container 3
    └─────────┬─────────┘
         Base Image (shared, saved once)
```

**Real-World Comparison:**

**Scenario 1: Running 50 Microservices**

With Virtual Machines:
```
50 VMs × 4 GB RAM = 200 GB RAM needed
50 VMs × 20 GB disk = 1 TB disk space
Boot time: 30 seconds each = 25 minutes total
Cost: High (infrastructure + licensing)
```

With Docker:
```
50 Containers × 50 MB RAM = 2.5 GB RAM needed
50 Containers × 200 MB disk = 10 GB disk space
Boot time: 1 second each = 50 seconds total
Cost: Low (infrastructure only)
```

**Scenario 2: Development Environment**

```bash
# Docker Compose - Define multi-container app
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_PASSWORD=secret

  redis:
    image: redis:6-alpine

volumes:
  postgres_data:

# Start entire environment
docker-compose up -d

# On any machine with Docker installed
# Exactly the same environment every time
# No "works on my machine" problems
```

**When to Use VMs vs Docker:**

**Use Virtual Machines when:**
1. Need complete OS isolation (different OS versions, Windows + Linux)
2. Running legacy applications that require specific OS
3. Stronger security boundary required (multi-tenant environments)
4. Need to run kernel modules or modify kernel parameters
5. Long-running, stateful applications (databases in production)

**Use Docker when:**
1. Microservices architecture
2. CI/CD pipelines (fast build and deploy)
3. Development environments (consistency across team)
4. Horizontal scaling (start/stop quickly)
5. Resource efficiency (run more workloads on same hardware)

**Docker Security Considerations:**

```bash
# Run as non-root user
FROM ubuntu:20.04
RUN useradd -m -u 1001 appuser
USER appuser

# Read-only filesystem
docker run --read-only -v /app/tmp:/tmp myapp:v1

# Drop capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp:v1

# Use security profiles
docker run --security-opt=no-new-privileges myapp:v1

# Scan images for vulnerabilities
docker scan myapp:v1
```

**Docker Networking:**

```bash
# Bridge network (default) - isolated network per host
docker network create my-bridge-net
docker run --network=my-bridge-net myapp:v1

# Host network - share host's network stack
docker run --network=host myapp:v1

# Overlay network - multi-host networking (Docker Swarm/Kubernetes)
docker network create -d overlay my-overlay-net

# Container communication
docker run --name=db postgres:14
docker run --name=app --link=db myapp:v1
# app can reach db at hostname "db"
```

**Docker Volumes (Persistent Data):**

```bash
# Named volume (managed by Docker)
docker volume create mydata
docker run -v mydata:/app/data myapp:v1

# Bind mount (host directory)
docker run -v /host/path:/container/path myapp:v1

# tmpfs mount (memory only, not persisted)
docker run --tmpfs /app/cache:size=100m myapp:v1

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mydata
```

**Best Practices:**

1. **Keep Images Small:**
```dockerfile
# Use Alpine Linux (5 MB vs 72 MB for Ubuntu)
FROM python:3.11-alpine

# Multi-stage builds
FROM golang:1.20 AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

FROM alpine:latest
COPY --from=builder /app/myapp /usr/local/bin/
CMD ["myapp"]
```

2. **Use .dockerignore:**
```
# .dockerignore
.git
node_modules
*.log
__pycache__
```

3. **One Process Per Container:**
```bash
# Bad: Running multiple services in one container
CMD nginx && postgres && redis

# Good: One container per service
docker run nginx:latest
docker run postgres:14
docker run redis:6
```

4. **Leverage Build Cache:**
```dockerfile
# Copy dependencies first (changes less often)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code last (changes frequently)
COPY . .
```

5. **Tag Images Properly:**
```bash
# Specific version (production)
docker tag myapp:latest myapp:1.2.3

# Never use :latest in production
# Bad:  image: myapp:latest
# Good: image: myapp:1.2.3
```

---

### Explain the Docker container lifecycle.

**Detailed Explanation:**

The Docker container lifecycle encompasses all states a container can be in from creation to removal. Understanding this lifecycle is crucial for managing containerized applications effectively.

**Container States:**

```
                    ┌─────────┐
                    │ Created │
                    └────┬────┘
                         │ docker start
                         v
    ┌──────────> ┌─────────┐ <──────────┐
    │            │ Running │            │
    │            └────┬────┘            │
    │                 │                 │
    │   docker pause  │  docker unpause │
    │                 v                 │
    │            ┌─────────┐            │
    │            │ Paused  │────────────┘
    │            └─────────┘
    │
    │   docker stop
    │   docker kill
    │                 │
    │                 v
    │            ┌─────────┐
    └────────────│ Stopped │
                 └────┬────┘
                      │ docker rm
                      v
                 ┌─────────┐
                 │ Deleted │
                 └─────────┘
```

**Detailed State Transitions:**

**1. Created State:**

Container is created but not started.

```bash
# Create container without starting
docker create \
  --name myapp \
  -p 8080:80 \
  -e DB_HOST=postgres \
  nginx:latest

# Container exists but is not running
docker ps -a
CONTAINER ID   NAME    STATUS
abc123         myapp   Created

# Inspect configuration (without running)
docker inspect myapp

# Start the created container
docker start myapp
```

Use cases:
- Pre-configure containers before starting
- Create containers in CI/CD pipelines for later use
- Test configuration without running

**2. Running State:**

Container is executing and active.

```bash
# Create and start in one command
docker run -d \
  --name myapp \
  -p 8080:80 \
  nginx:latest

# Check running containers
docker ps
CONTAINER ID   NAME    STATUS          PORTS
abc123         myapp   Up 5 minutes    0.0.0.0:8080->80/tcp

# View real-time stats
docker stats myapp
CONTAINER   CPU %   MEM USAGE / LIMIT   NET I/O
myapp       0.50%   10.2MB / 2GB        1.2kB / 850B

# Stream logs
docker logs -f myapp

# Execute commands in running container
docker exec -it myapp /bin/bash

# Attach to container's stdout/stderr
docker attach myapp
```

Container lifecycle events:
- Process starts with PID 1
- Health checks run (if configured)
- Logs generated
- Metrics collected
- Network active
- Resources consumed

**3. Paused State:**

Container processes are frozen (using cgroups freezer).

```bash
# Pause all processes in container
docker pause myapp

# Check status
docker ps
CONTAINER ID   NAME    STATUS
abc123         myapp   Up 10 minutes (Paused)

# Container is frozen:
# - Processes don't execute
# - No CPU cycles used
# - Memory remains allocated
# - Network connections maintained
# - Not responsive to requests

# Resume execution
docker unpause myapp

# Container continues from exact point where paused
docker ps
CONTAINER ID   NAME    STATUS
abc123         myapp   Up 11 minutes
```

Use cases:
- Temporarily freeze container during debugging
- Create checkpoint before risky operation
- Resource management (free CPU for other containers)
- Not commonly used in production

**4. Stopped State:**

Container is not running but configuration and filesystem remain.

```bash
# Graceful stop (SIGTERM, then SIGKILL after timeout)
docker stop myapp
# Sends SIGTERM to PID 1
# Waits 10 seconds (default)
# Sends SIGKILL if still running

# Stop with custom timeout
docker stop -t 30 myapp  # Wait 30 seconds

# Force stop immediately (SIGKILL)
docker kill myapp

# Check stopped containers
docker ps -a
CONTAINER ID   NAME    STATUS
abc123         myapp   Exited (0) 5 minutes ago

# View exit code
docker inspect -f '{{.State.ExitCode}}' myapp
0  # Success

# Common exit codes:
# 0 - Normal termination
# 1 - Application error
# 137 - Killed by SIGKILL (out of memory, docker kill)
# 139 - Segmentation fault
# 143 - Killed by SIGTERM (docker stop)

# Restart stopped container
docker start myapp

# Check logs from stopped container
docker logs myapp  # Still available
```

**5. Deleted State:**

Container is completely removed.

```bash
# Remove stopped container
docker rm myapp

# Force remove running container
docker rm -f myapp  # Stops then removes

# Remove with volumes
docker rm -v myapp  # Also removes anonymous volumes

# Container is gone
docker ps -a  # Not listed

# Data is lost unless:
# - Used named volumes (persist)
# - Used bind mounts (host filesystem)
# - Committed to image before removal
```

**Complete Lifecycle Example:**

```bash
# 1. CREATE: Build image
docker build -t webapp:v1 .

# 2. CREATE: Create container
docker create \
  --name webapp-prod \
  -p 80:8080 \
  -e ENV=production \
  -e DB_HOST=postgres.example.com \
  -v webapp-data:/app/data \
  --restart=unless-stopped \
  --health-cmd="curl -f http://localhost:8080/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  webapp:v1

# 3. RUNNING: Start container
docker start webapp-prod

# Monitor startup
docker logs -f webapp-prod

# Wait for healthy status
docker inspect -f '{{.State.Health.Status}}' webapp-prod
# starting... starting... healthy

# 4. RUNNING: Container is active
docker ps
docker stats webapp-prod
docker exec webapp-prod ps aux

# 5. PAUSED: Temporarily pause (rare)
docker pause webapp-prod
# Do maintenance...
docker unpause webapp-prod

# 6. STOPPED: Graceful shutdown
docker stop webapp-prod
# Application receives SIGTERM
# Cleanup operations (close DB connections, save state)
# Container stops after 10 seconds

# 7. RUNNING: Restart
docker start webapp-prod

# 8. STOPPED: Stop again for updates
docker stop webapp-prod

# 9. DELETED: Remove old container
docker rm webapp-prod

# 10. CREATE + RUNNING: Deploy new version
docker run -d \
  --name webapp-prod \
  -p 80:8080 \
  -e ENV=production \
  -e DB_HOST=postgres.example.com \
  -v webapp-data:/app/data \
  --restart=unless-stopped \
  webapp:v2  # New version
```

**Restart Policies:**

Control what happens when container stops or Docker daemon restarts.

```bash
# no (default) - Never restart
docker run --restart=no myapp

# always - Always restart (even if manually stopped)
docker run --restart=always myapp

# on-failure - Restart only on non-zero exit
docker run --restart=on-failure:5 myapp  # Max 5 retries

# unless-stopped - Always restart unless explicitly stopped
docker run --restart=unless-stopped myapp
# Most common for production

# After Docker daemon restart:
# - 'always' containers start
# - 'unless-stopped' containers start (if not manually stopped)
# - 'on-failure' containers don't start (unless they crashed)
# - 'no' containers don't start
```

**Container Exit Scenarios:**

**1. Normal Exit:**
```bash
# Application completes successfully
docker run alpine echo "Hello World"
# Exits with code 0

docker run --rm alpine sh -c "exit 0"
# Container automatically removed (--rm)
```

**2. Application Error:**
```bash
# Application crashes
docker run alpine sh -c "exit 1"
# Exits with code 1

# Check why it exited
docker inspect -f '{{.State.ExitCode}}' container_name
```

**3. Out of Memory (OOM):**
```bash
# Container exceeds memory limit
docker run -m 100m stress-ng --vm 1 --vm-bytes 200m
# Killed by kernel OOM killer
# Exit code: 137 (128 + 9 SIGKILL)

# Check OOM status
docker inspect -f '{{.State.OOMKilled}}' container_name
# true
```

**4. Health Check Failure:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost/ || exit 1
```

```bash
# Health check keeps failing
docker ps
CONTAINER ID   STATUS
abc123         Up 5 minutes (unhealthy)

# Docker doesn't auto-stop unhealthy containers
# But orchestrators (Kubernetes, ECS) will restart them
```

**5. Manual Stop:**
```bash
# User/admin stops container
docker stop myapp
# Exit code: 143 (128 + 15 SIGTERM)

# Force kill
docker kill myapp
# Exit code: 137 (128 + 9 SIGKILL)
```

**Lifecycle Hooks and Events:**

```bash
# Monitor container events
docker events --filter container=myapp

# Events generated:
# - create
# - start
# - pause
# - unpause
# - stop
# - die
# - destroy

# Real-time monitoring
docker events --filter event=start --filter event=stop
2026-02-24T10:00:00.000000000Z container start abc123 (name=myapp)
2026-02-24T10:15:00.000000000Z container stop abc123 (name=myapp)

# Automated actions based on events
docker events --format '{{.Status}}: {{.Actor.Attributes.name}}' | while read event; do
  echo "Event: $event"
  # Trigger alerts, logging, etc.
done
```

**Preserving Container State:**

**1. Commit Container to Image:**
```bash
# Make changes in running container
docker exec myapp apt-get install -y vim

# Save state as new image
docker commit myapp myapp:with-vim

# Start new container from saved state
docker run myapp:with-vim
```

**2. Export/Import Container:**
```bash
# Export container filesystem
docker export myapp > myapp.tar

# Import as image
docker import myapp.tar myapp:backup
```

**3. Checkpoint/Restore (Experimental):**
```bash
# Create checkpoint (snapshot)
docker checkpoint create myapp checkpoint1

# Stop and remove container
docker stop myapp
docker rm myapp

# Restore from checkpoint
docker start --checkpoint checkpoint1 myapp
# Container resumes from exact state
```

**Best Practices:**

1. **Use Health Checks:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD curl -f http://localhost:8080/health || exit 1
```

2. **Handle Signals Properly:**
```python
# Python example
import signal
import sys

def signal_handler(sig, frame):
    print('Graceful shutdown...')
    # Close database connections
    # Finish current requests
    # Save state
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Application code...
```

3. **Use Appropriate Restart Policies:**
```bash
# Production services
--restart=unless-stopped

# Batch jobs
--restart=on-failure:3

# Development
--restart=no
```

4. **Clean Up Resources:**
```bash
# Remove stopped containers automatically
docker run --rm myapp

# Clean up dangling containers
docker container prune

# Remove all stopped containers
docker container prune -a
```

5. **Monitor Container State:**
```bash
# Automated monitoring script
while true; do
  STATUS=$(docker inspect -f '{{.State.Status}}' myapp)
  HEALTH=$(docker inspect -f '{{.State.Health.Status}}' myapp)

  if [ "$STATUS" != "running" ] || [ "$HEALTH" = "unhealthy" ]; then
    echo "Container issue detected!"
    # Send alert
    # Restart container
    docker restart myapp
  fi

  sleep 60
done
```

---

### How do you optimize Docker images for production?

**Detailed Explanation:**

Optimizing Docker images is crucial for faster builds, smaller deployments, reduced costs, and improved security. A well-optimized image can be 10-100x smaller than an unoptimized one.

**Why Image Size Matters:**

```
Unoptimized Image: 2 GB
- Docker pull time: 5-10 minutes
- Deploy time: 10-15 minutes
- Storage cost: $0.10/GB/month × 2 GB × 100 servers = $20/month
- Vulnerability surface: High (many packages)

Optimized Image: 50 MB
- Docker pull time: 10-30 seconds
- Deploy time: 1-2 minutes
- Storage cost: $0.10/GB/month × 0.05 GB × 100 servers = $0.50/month
- Vulnerability surface: Low (minimal packages)
```

**1. Use Minimal Base Images:**

**Bad:**
```dockerfile
FROM ubuntu:20.04  # 72 MB

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "app.py"]

# Final image: ~800 MB
```

**Good:**
```dockerfile
FROM python:3.11-slim  # 45 MB (vs ubuntu 72 MB + python install)

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "app.py"]

# Final image: ~200 MB
```

**Better:**
```dockerfile
FROM python:3.11-alpine  # 5 MB!

WORKDIR /app

# Alpine uses apk instead of apt
RUN apk add --no-cache gcc musl-dev

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "app.py"]

# Final image: ~80 MB
```

**Base Image Comparison:**

| Base Image | Size | Use Case |
|------------|------|----------|
| ubuntu:20.04 | 72 MB | Full Linux environment, many tools |
| debian:bullseye-slim | 27 MB | Smaller Debian, good compatibility |
| alpine:latest | 5 MB | Minimal, but may have compatibility issues |
| python:3.11 | 900 MB | Python + build tools + everything |
| python:3.11-slim | 45 MB | Python + minimal dependencies |
| python:3.11-alpine | 20 MB | Smallest Python base |
| scratch | 0 MB | Empty, for static binaries only |
| distroless | 2-20 MB | Google's minimal images, no shell |

**2. Multi-Stage Builds:**

The most powerful optimization technique.

**Bad (Single Stage):**
```dockerfile
FROM golang:1.20  # 900 MB

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o myapp

CMD ["./myapp"]

# Final image: 1.2 GB
# Includes Go compiler, build tools, source code - all unnecessary at runtime!
```

**Good (Multi-Stage):**
```dockerfile
# Stage 1: Build
FROM golang:1.20 AS builder  # 900 MB - only used during build

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o myapp .

# Stage 2: Runtime
FROM alpine:latest  # 5 MB

WORKDIR /root/

# Copy only the binary from builder stage
COPY --from=builder /app/myapp .

CMD ["./myapp"]

# Final image: 10 MB (200x smaller!)
# Contains only the binary, nothing else
```

**Advanced Multi-Stage:**
```dockerfile
# Stage 1: Dependencies
FROM node:18 AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 3: Runtime
FROM node:18-alpine
WORKDIR /app

# Copy only production dependencies
COPY --from=deps /app/node_modules ./node_modules

# Copy only built artifacts
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

EXPOSE 3000
CMD ["node", "dist/server.js"]

# Final image: Minimal size with only runtime needs
```

**3. Leverage Build Cache:**

Docker caches each layer. Order matters!

**Bad (Cache Invalidated Often):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copying everything first means ANY file change invalidates cache
COPY . .  # Cache miss on every code change!

RUN pip3 install -r requirements.txt  # Reinstalls every time!

CMD ["python3", "app.py"]
```

**Good (Cache-Friendly):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies first (changes rarely)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt  # Cached unless requirements change!

# Copy code last (changes frequently)
COPY . .  # Only this layer rebuilds on code changes

CMD ["python3", "app.py"]
```

**Build Time Comparison:**
```bash
# First build
time docker build -t myapp:v1 .
# Build time: 120 seconds

# Change one Python file
echo "# comment" >> app.py

# Build with bad Dockerfile
time docker build -t myapp:v2 .
# Build time: 120 seconds (everything rebuilds)

# Build with good Dockerfile
time docker build -t myapp:v2 .
# Build time: 5 seconds (only copy layer rebuilds)
```

**4. Use .dockerignore:**

Exclude unnecessary files from build context.

**.dockerignore:**
```
# Version control
.git
.gitignore

# Dependencies (installed in container)
node_modules
venv
__pycache__

# Build artifacts
dist
build
*.egg-info

# IDE files
.vscode
.idea
*.swp

# Logs and temp files
*.log
*.tmp
.DS_Store

# Tests (if not running in container)
tests/
*.test.py

# Documentation
README.md
docs/

# CI/CD
.github
.gitlab-ci.yml
Jenkinsfile

# Environment files (contain secrets)
.env
.env.local
```

**Impact:**
```bash
# Without .dockerignore
docker build .
Sending build context to Docker daemon: 500 MB  # Includes node_modules, .git, etc.
Build time: 60 seconds

# With .dockerignore
docker build .
Sending build context to Docker daemon: 5 MB  # Only necessary files
Build time: 10 seconds
```

**5. Minimize Layers:**

Each RUN, COPY, ADD creates a layer.

**Bad (Many Layers):**
```dockerfile
FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN apt-get install -y curl
RUN apt-get install -y git
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# 7 layers, slower build, larger image
```

**Good (Combined Layers):**
```dockerfile
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 1 layer, faster build, smaller image
```

**Why This Matters:**
```bash
# Each layer is stored separately
Layer 1: apt-get update (50 MB)
Layer 2: apt-get install python3 (100 MB)
Layer 3: apt-get install pip (50 MB)
Layer 4: apt-get clean (0 MB but layer exists)
Layer 5: rm -rf (0 MB but layer exists)

# Cleanup in separate layer doesn't reduce size!
# Files deleted in Layer 5 still exist in Layers 1-4

# Combined layer:
Layer 1: update + install + clean + rm (150 MB)
# Cleanup happens in same layer, actually reduces size
```

**6. Remove Package Manager Cache:**

**Bad:**
```dockerfile
RUN apt-get update && apt-get install -y python3
# /var/lib/apt/lists/ contains 100+ MB of package lists
```

**Good:**
```dockerfile
RUN apt-get update && apt-get install -y python3 \
    && rm -rf /var/lib/apt/lists/*
# Removes cache in same layer, saves 100+ MB
```

**For Different Package Managers:**
```dockerfile
# APT (Debian/Ubuntu)
RUN apt-get update && apt-get install -y package \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# YUM (CentOS/RHEL)
RUN yum install -y package \
    && yum clean all \
    && rm -rf /var/cache/yum

# APK (Alpine)
RUN apk add --no-cache package
# --no-cache automatically avoids caching

# PIP (Python)
RUN pip install --no-cache-dir -r requirements.txt

# NPM (Node.js)
RUN npm ci --only=production \
    && npm cache clean --force
```

**7. Use Specific Versions:**

**Bad:**
```dockerfile
FROM python:3  # Which 3.x? Could be 3.8, 3.9, 3.11...
RUN pip install flask  # Which version? Latest changes over time
```

**Good:**
```dockerfile
FROM python:3.11.4-slim  # Exact version
RUN pip install flask==2.3.2  # Pinned version
```

**Benefits:**
- Reproducible builds
- Predictable behavior
- Security control (don't auto-update to vulnerable versions)
- Rollback capability

**8. Run as Non-Root User:**

**Bad:**
```dockerfile
FROM python:3.11-slim

COPY . /app
WORKDIR /app

CMD ["python", "app.py"]
# Runs as root (UID 0) - security risk!
```

**Good:**
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1001 appuser

# Set ownership
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Switch to non-root user
USER appuser

CMD ["python", "app.py"]
# Runs as appuser (UID 1001) - more secure
```

**9. Use Distroless Images (Advanced):**

Google's distroless images contain only your application and runtime dependencies, no shell or package managers.

```dockerfile
# Build stage
FROM golang:1.20 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o myapp

# Runtime stage - distroless
FROM gcr.io/distroless/static-debian11

COPY --from=builder /app/myapp /

USER nonroot:nonroot

ENTRYPOINT ["/myapp"]

# Final image: ~2 MB
# No shell, no package manager, only your binary
# Maximum security, minimal attack surface
```

**10. Optimize Application Code:**

```python
# Remove unnecessary dependencies
# requirements.txt - Bad
pandas  # 100+ MB with dependencies
numpy
scipy
matplotlib

# requirements.txt - Good (if you only need one)
pandas==1.5.3  # Only what you actually use
```

```dockerfile
# Install only production dependencies
FROM node:18-alpine

COPY package*.json ./
RUN npm ci --only=production  # Excludes devDependencies

COPY . .

CMD ["node", "server.js"]
```

**11. Compress and Optimize Binaries:**

```dockerfile
# Build with optimizations
FROM golang:1.20 AS builder
WORKDIR /app
COPY . .

# Build flags for smaller binary
RUN CGO_ENABLED=0 GOOS=linux go build \
    -a \
    -installsuffix cgo \
    -ldflags="-s -w" \
    -o myapp .

# -s: strip debug symbols
# -w: strip DWARF debug info
# Result: 50% smaller binary

# Further compress with UPX (optional)
RUN apk add --no-cache upx
RUN upx --best --lzma myapp
# Result: Another 50-70% reduction

FROM scratch
COPY --from=builder /app/myapp /
ENTRYPOINT ["/myapp"]
```

**Complete Optimized Example:**

**Before Optimization:**
```dockerfile
FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN apt-get install -y gcc g++ make
RUN apt-get install -y git curl wget

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python3", "app.py"]

# Image size: 1.5 GB
# Build time: 180 seconds
# Vulnerabilities: 150+
```

**After Optimization:**
```dockerfile
# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-alpine

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY --chown=nobody:nobody . .

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Run as non-root
USER nobody

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

CMD ["python", "app.py"]

# Image size: 80 MB (20x smaller!)
# Build time: 30 seconds (6x faster!)
# Vulnerabilities: 10-20
```

**Verification and Measurement:**

```bash
# Check image size
docker images myapp
REPOSITORY   TAG       SIZE
myapp        before    1.5GB
myapp        after     80MB

# Inspect layers
docker history myapp:after
IMAGE          CREATED BY                                      SIZE
abc123         CMD ["python" "app.py"]                         0B
def456         USER nobody                                     0B
ghi789         COPY . .                                        5MB
jkl012         COPY --from=builder /root/.local /root/.local  40MB
mno345         FROM python:3.11-alpine                        35MB

# Scan for vulnerabilities
docker scan myapp:after
# Low: 5, Medium: 3, High: 0, Critical: 0

# Test image
docker run --rm myapp:after python -c "import sys; print(sys.version)"
```

**Best Practices Summary:**

1. Use Alpine or slim base images
2. Multi-stage builds for compiled languages
3. Order Dockerfile commands by change frequency
4. Use .dockerignore
5. Combine RUN commands
6. Remove package manager cache
7. Pin versions
8. Run as non-root user
9. Use specific tags, never :latest
10. Scan for vulnerabilities regularly

---

### What is Docker Compose and when would you use it?

**Detailed Explanation:**

Docker Compose is a tool for defining and running multi-container Docker applications. Instead of managing containers individually with docker run commands, Compose uses a YAML file to configure all your application's services, networks, and volumes.

**Why Docker Compose?**

**Problem Without Compose:**

```bash
# Starting a web application manually requires multiple commands:

# 1. Create network
docker network create my-app-network

# 2. Start database
docker run -d \
  --name postgres-db \
  --network my-app-network \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypass \
  -e POSTGRES_DB=mydb \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:14

# 3. Start Redis
docker run -d \
  --name redis-cache \
  --network my-app-network \
  redis:6-alpine

# 4. Start backend
docker run -d \
  --name backend-api \
  --network my-app-network \
  -e DATABASE_URL=postgres://myuser:mypass@postgres-db:5432/mydb \
  -e REDIS_URL=redis://redis-cache:6379 \
  -p 8080:8080 \
  backend:v1

# 5. Start frontend
docker run -d \
  --name frontend-web \
  --network my-app-network \
  -e API_URL=http://backend-api:8080 \
  -p 80:80 \
  frontend:v1

# Stopping everything is equally tedious...
docker stop frontend-web backend-api redis-cache postgres-db
docker rm frontend-web backend-api redis-cache postgres-db
docker network rm my-app-network
```

**Solution With Compose:**

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  # Database service
  db:
    image: postgres:14
    container_name: postgres-db
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypass
      POSTGRES_DB: mydb
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - my-app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Cache service
  redis:
    image: redis:6-alpine
    container_name: redis-cache
    networks:
      - my-app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # Backend API service
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: backend-api
    environment:
      DATABASE_URL: postgres://myuser:mypass@db:5432/mydb
      REDIS_URL: redis://redis:6379
    ports:
      - "8080:8080"
    networks:
      - my-app-network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # Frontend web service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend-web
    environment:
      API_URL: http://backend:8080
    ports:
      - "80:80"
    networks:
      - my-app-network
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres-data:

networks:
  my-app-network:
    driver: bridge
```

**Usage:**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

**Complete Real-World Example:**

**Project Structure:**
```
my-app/
├── docker-compose.yml
├── docker-compose.override.yml      # Development overrides
├── docker-compose.prod.yml          # Production configuration
├── .env                             # Environment variables
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
```

**docker-compose.yml (Base Configuration):**
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
      POSTGRES_DB: ${DB_NAME:-myapp}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d  # Initialization scripts
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: 3.11
    environment:
      - DATABASE_URL=postgres://${DB_USER:-postgres}:${DB_PASSWORD:-changeme}@db:5432/${DB_NAME:-myapp}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key}
      - DEBUG=${DEBUG:-False}
    ports:
      - "${BACKEND_PORT:-8080}:8080"
    volumes:
      - ./backend:/app
      - backend_static:/app/static
    networks:
      - frontend
      - backend
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Frontend Web
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NODE_VERSION: 18
    environment:
      - API_BASE_URL=${API_BASE_URL:-http://localhost:8080}
      - NODE_ENV=${NODE_ENV:-production}
    ports:
      - "${FRONTEND_PORT:-80}:80"
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - frontend
    depends_on:
      - backend
    restart: unless-stopped

  # NGINX Reverse Proxy (Optional)
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - backend_static:/usr/share/nginx/html/static:ro
    networks:
      - frontend
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  backend_static:

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
```

**.env file:**
```bash
# Database Configuration
DB_USER=myuser
DB_PASSWORD=secure_password_here
DB_NAME=production_db

# Application Configuration
SECRET_KEY=your_very_secure_secret_key_here
DEBUG=False
NODE_ENV=production

# Ports
BACKEND_PORT=8080
FRONTEND_PORT=80

# URLs
API_BASE_URL=http://api.example.com
```

**docker-compose.override.yml (Automatic development overrides):**
```yaml
version: '3.8'

services:
  backend:
    build:
      target: development  # Use development stage from Dockerfile
    environment:
      - DEBUG=True
    volumes:
      - ./backend:/app  # Live code reload
    command: python -m flask run --host=0.0.0.0 --reload

  frontend:
    build:
      target: development
    volumes:
      - ./frontend/src:/app/src  # Live code reload
    command: npm run dev

  # Add development tools
  adminer:
    image: adminer
    ports:
      - "8081:8080"
    networks:
      - backend
    depends_on:
      - db
```

**docker-compose.prod.yml (Production overrides):**
```yaml
version: '3.8'

services:
  db:
    # Use managed database in production
    image: postgres:14-alpine
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  backend:
    # Build optimized production image
    build:
      target: production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M

  # Add monitoring
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
    networks:
      - backend

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    networks:
      - backend
```

**Using Different Compose Files:**

```bash
# Development (uses docker-compose.yml + docker-compose.override.yml automatically)
docker-compose up -d

# Production (specify production file)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Specific environment
docker-compose --env-file .env.staging up -d
```

**Advanced Docker Compose Features:**

**1. Service Dependencies:**

```yaml
services:
  backend:
    depends_on:
      db:
        condition: service_healthy  # Wait until healthy
      redis:
        condition: service_started  # Just wait for start
```

**2. Resource Limits:**

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

**3. Scaling Services:**

```bash
# Scale backend to 5 instances
docker-compose up -d --scale backend=5

# In compose file
services:
  backend:
    deploy:
      replicas: 5
```

**4. Extending Services:**

```yaml
# Common configuration
x-common-variables: &common-vars
  DATABASE_URL: postgres://db:5432/mydb
  LOG_LEVEL: info

services:
  backend:
    environment:
      <<: *common-vars
      SERVICE_NAME: backend

  worker:
    environment:
      <<: *common-vars
      SERVICE_NAME: worker
```

**5. Profiles (Selective Service Startup):**

```yaml
services:
  db:
    # Always starts

  backend:
    # Always starts

  test-runner:
    profiles:
      - test
    # Only starts with: docker-compose --profile test up

  debug-tools:
    profiles:
      - debug
    # Only starts with: docker-compose --profile debug up
```

**Common Docker Compose Commands:**

```bash
# Start services in foreground
docker-compose up

# Start services in background
docker-compose up -d

# Build images before starting
docker-compose up --build

# Recreate containers even if config hasn't changed
docker-compose up --force-recreate

# View logs
docker-compose logs
docker-compose logs -f backend  # Follow specific service
docker-compose logs --tail=100 backend  # Last 100 lines

# Execute command in service
docker-compose exec backend /bin/bash
docker-compose exec db psql -U postgres

# Run one-off command
docker-compose run backend python manage.py migrate
docker-compose run --rm backend pytest  # Remove container after

# List containers
docker-compose ps

# View configuration (resolved)
docker-compose config

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers and volumes
docker-compose down -v

# Remove orphan containers
docker-compose down --remove-orphans

# Restart specific service
docker-compose restart backend

# Pause/unpause services
docker-compose pause backend
docker-compose unpause backend

# View service resource usage
docker-compose top
```

**Use Cases:**

**1. Development Environment:**
```yaml
# Instant setup for new developers
version: '3.8'
services:
  app:
    build: .
    volumes:
      - .:/app  # Live code reload
    ports:
      - "3000:3000"
  db:
    image: postgres:14
  redis:
    image: redis:6

# New developer setup:
# git clone repo
# docker-compose up
# Done! Full environment running
```

**2. Testing:**
```bash
# Run tests in isolated environment
docker-compose run --rm backend pytest
docker-compose run --rm frontend npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

**3. CI/CD Pipeline:**
```yaml
# .gitlab-ci.yml
test:
  script:
    - docker-compose -f docker-compose.test.yml up --abort-on-container-exit
    - docker-compose down -v
```

**4. Microservices Development:**
```yaml
# docker-compose.yml
services:
  service-a:
    build: ./service-a
    ports:
      - "8081:8080"

  service-b:
    build: ./service-b
    ports:
      - "8082:8080"
    depends_on:
      - service-a

  service-c:
    build: ./service-c
    ports:
      - "8083:8080"
    depends_on:
      - service-b

# Start entire microservices ecosystem locally
docker-compose up -d
```

**Troubleshooting:**

```bash
# Service won't start
docker-compose logs backend  # Check logs
docker-compose ps  # Check status
docker-compose config  # Validate config

# Port already in use
docker-compose ps -a  # Check what's using ports
# Change port in docker-compose.yml or .env

# Network issues
docker-compose down
docker network prune
docker-compose up

# Volume permission issues
docker-compose exec backend ls -la /app
# Fix ownership in Dockerfile or use named volumes

# Can't connect to service
docker-compose exec backend ping db
docker-compose exec backend nslookup db
```

**Best Practices:**

1. **Use environment variables:**
```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}  # From .env
```

2. **Use named volumes for persistence:**
```yaml
volumes:
  postgres_data:  # Named volume (managed by Docker)
```

3. **Health checks:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
```

4. **Use .env for configuration:**
```bash
# .env file (not committed to git)
DB_PASSWORD=secret
API_KEY=your-key
```

5. **Separate concerns with profiles:**
```yaml
profiles: ['dev', 'test', 'debug']
```

---

## AWS / Cloud / Architecture

### Explain AWS VPC, subnets, route tables, and how they work together.

**Detailed Explanation:**

AWS Virtual Private Cloud (VPC) is a logically isolated network that you define in AWS. Understanding VPC components is fundamental to building secure, scalable cloud architectures.

**VPC Architecture Overview:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                     │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              VPC (10.0.0.0/16) - 65,536 IPs                  │  │
│  │                                                               │  │
│  │  ┌────────────────────────┐  ┌────────────────────────────┐ │  │
│  │  │   Public Subnet        │  │    Public Subnet           │ │  │
│  │  │   10.0.1.0/24          │  │    10.0.2.0/24             │ │  │
│  │  │   AZ: us-east-1a       │  │    AZ: us-east-1b          │ │  │
│  │  │                        │  │                            │ │  │
│  │  │   ┌──────────┐         │  │    ┌──────────┐           │ │  │
│  │  │   │  EC2     │         │  │    │  EC2     │           │ │  │
│  │  │   │Web Server│         │  │    │Web Server│           │ │  │
│  │  │   └──────────┘         │  │    └──────────┘           │ │  │
│  │  │   Public IP            │  │    Public IP              │ │  │
│  │  └────────┬───────────────┘  └──────────┬────────────────┘ │  │
│  │           │                               │                  │  │
│  │       Internet Gateway                    │                  │  │
│  │           │                               │                  │  │
│  │  ┌────────┴───────────────┐  ┌───────────┴────────────────┐│  │
│  │  │   Private Subnet       │  │    Private Subnet          ││  │
│  │  │   10.0.3.0/24          │  │    10.0.4.0/24             ││  │
│  │  │   AZ: us-east-1a       │  │    AZ: us-east-1b          ││  │
│  │  │                        │  │                            ││  │
│  │  │   ┌──────────┐         │  │    ┌──────────┐           ││  │
│  │  │   │  RDS     │         │  │    │  RDS     │           ││  │
│  │  │   │ Database │         │  │    │ Database │           ││  │
│  │  │   └──────────┘         │  │    └──────────┘           ││  │
│  │  │   No Public IP         │  │    No Public IP           ││  │
│  │  └────────────────────────┘  └────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**1. VPC (Virtual Private Cloud):**

A VPC is your own isolated network in AWS with complete control over:
- IP address range (CIDR block)
- Subnets
- Route tables
- Network gateways
- Security settings

**Creating a VPC:**

```bash
# AWS CLI - Create VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=my-vpc}]'

# VPC Details:
# - CIDR: 10.0.0.0/16 (65,536 IP addresses)
# - Range: 10.0.0.0 to 10.0.255.255
# - AWS reserves 5 IPs per subnet:
#   - 10.0.0.0: Network address
#   - 10.0.0.1: VPC router
#   - 10.0.0.2: DNS server
#   - 10.0.0.3: Future use
#   - 10.0.0.255: Broadcast (not supported but reserved)
```

**Terraform Example:**
```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "main-vpc"
  }
}
```

**CIDR Block Sizing:**

| CIDR | IPs Available | Use Case |
|------|---------------|----------|
| /16 | 65,536 | Large enterprise VPC |
| /20 | 4,096 | Medium organization |
| /24 | 256 | Small subnet |
| /28 | 16 | Very small subnet |

**2. Subnets:**

Subnets are segments of a VPC's IP address range where you place AWS resources.

**Types:**

**Public Subnet:**
- Has route to Internet Gateway
- Instances can have public IPs
- Used for web servers, load balancers, NAT gateways

**Private Subnet:**
- No direct route to internet
- Instances only have private IPs
- Used for databases, application servers
- Can access internet via NAT Gateway

**Creating Subnets:**

```bash
# Public Subnet in AZ 1
aws ec2 create-subnet \
  --vpc-id vpc-12345678 \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1a}]'

# Public Subnet in AZ 2 (for high availability)
aws ec2 create-subnet \
  --vpc-id vpc-12345678 \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1b}]'

# Private Subnet in AZ 1
aws ec2 create-subnet \
  --vpc-id vpc-12345678 \
  --cidr-block 10.0.3.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-subnet-1a}]'

# Private Subnet in AZ 2
aws ec2 create-subnet \
  --vpc-id vpc-12345678 \
  --cidr-block 10.0.4.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-subnet-1b}]'
```

**Terraform Multi-AZ Subnets:**
```hcl
# Public Subnets
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-${count.index + 1}"
    Type = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 3}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "private-subnet-${count.index + 1}"
    Type = "private"
  }
}
```

**3. Internet Gateway (IGW):**

Enables communication between VPC and the internet.

```bash
# Create Internet Gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=main-igw}]'

# Attach to VPC
aws ec2 attach-internet-gateway \
  --vpc-id vpc-12345678 \
  --internet-gateway-id igw-12345678
```

```hcl
# Terraform
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}
```

**4. Route Tables:**

Route tables contain rules (routes) that determine where network traffic is directed.

**Public Route Table (for public subnets):**

```bash
# Create public route table
aws ec2 create-route-table \
  --vpc-id vpc-12345678 \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=public-rt}]'

# Add route to Internet Gateway
aws ec2 create-route \
  --route-table-id rtb-12345678 \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-12345678

# Associate with public subnet
aws ec2 associate-route-table \
  --route-table-id rtb-12345678 \
  --subnet-id subnet-12345678

# Route table entries:
# Destination      Target
# 10.0.0.0/16      local (VPC internal traffic)
# 0.0.0.0/0        igw-12345678 (internet traffic)
```

**Private Route Table (for private subnets):**

```bash
# Create private route table
aws ec2 create-route-table \
  --vpc-id vpc-12345678 \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=private-rt}]'

# Add route to NAT Gateway
aws ec2 create-route \
  --route-table-id rtb-87654321 \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id nat-12345678

# Associate with private subnet
aws ec2 associate-route-table \
  --route-table-id rtb-87654321 \
  --subnet-id subnet-87654321

# Route table entries:
# Destination      Target
# 10.0.0.0/16      local (VPC internal traffic)
# 0.0.0.0/0        nat-12345678 (internet via NAT)
```

**Terraform Complete Route Tables:**
```hcl
# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-rt"
  }
}

# Associate public route table with public subnets
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Table
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "private-rt"
  }
}

# Associate private route table with private subnets
resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
```

**5. NAT Gateway:**

Allows instances in private subnets to access the internet without being directly accessible from the internet.

```bash
# Allocate Elastic IP for NAT Gateway
aws ec2 allocate-address --domain vpc

# Create NAT Gateway in public subnet
aws ec2 create-nat-gateway \
  --subnet-id subnet-12345678 \  # Must be public subnet
  --allocation-id eipalloc-12345678 \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=main-nat}]'

# NAT Gateway must be in public subnet
# Private instances route internet traffic through NAT
```

```hcl
# Terraform NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "nat-gateway-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "main-nat-gateway"
  }

  depends_on = [aws_internet_gateway.main]
}
```

**Complete VPC Architecture Example:**

**Terraform - Production-Ready VPC:**
```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "production-vpc"
    Environment = "production"
  }
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Public Subnets (2 AZs for HA)
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                     = "public-subnet-${count.index + 1}"
    "kubernetes.io/role/elb" = "1"  # For AWS Load Balancer Controller
  }
}

# Private Subnets (2 AZs for HA)
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 2)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name                              = "private-subnet-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"  # For internal load balancers
  }
}

# Database Subnets (2 AZs for RDS Multi-AZ)
resource "aws_subnet" "database" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 4)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "database-subnet-${count.index + 1}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  count  = 2  # One per AZ for high availability
  domain = "vpc"

  tags = {
    Name = "nat-eip-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways (one per AZ for HA)
resource "aws_nat_gateway" "main" {
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "nat-gateway-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-rt"
  }
}

# Public Route Table Associations
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Tables (one per AZ)
resource "aws_route_table" "private" {
  count  = 2
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "private-rt-${count.index + 1}"
  }
}

# Private Route Table Associations
resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Database Route Table
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "database-rt"
  }
}

# Database Route Table Associations
resource "aws_route_table_association" "database" {
  count          = 2
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# VPC Flow Logs (for monitoring)
resource "aws_flow_log" "main" {
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name = "vpc-flow-logs"
  }
}

# Outputs
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  value = aws_subnet.database[*].id
}
```

**How Traffic Flows:**

**Scenario 1: Internet to Web Server (Public Subnet)**
```
Internet User (1.2.3.4)
    ↓
Internet Gateway
    ↓
Public Subnet (10.0.1.0/24)
    ↓
Web Server EC2 (10.0.1.10 + Public IP 54.1.2.3)

Route Table (Public):
- 10.0.0.0/16 → local (internal VPC traffic)
- 0.0.0.0/0 → igw-xxx (internet traffic)
```

**Scenario 2: Web Server to Database (Private Subnet)**
```
Web Server (10.0.1.10 in public subnet)
    ↓
VPC local routing (10.0.0.0/16)
    ↓
Private Subnet (10.0.3.0/24)
    ↓
Database EC2 (10.0.3.50)

No route table needed - local VPC traffic
```

**Scenario 3: Database to Internet (for updates)**
```
Database (10.0.3.50 in private subnet)
    ↓
Route Table: 0.0.0.0/0 → nat-xxx
    ↓
NAT Gateway (in public subnet 10.0.1.0/24)
    ↓
Internet Gateway
    ↓
Internet

# Database can initiate connections to internet
# Internet cannot initiate connections to database
```

**Security Groups vs NACLs:**

**Security Groups (Stateful):**
```hcl
# Web Server Security Group
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Allow HTTP/HTTPS from anywhere"
  vpc_id      = aws_vpc.main.id

  # Inbound rules
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP from internet"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet"
  }

  # Outbound rules (usually allow all)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "web-sg"
  }
}

# Database Security Group
resource "aws_security_group" "database" {
  name        = "database-sg"
  description = "Allow PostgreSQL from web servers only"
  vpc_id      = aws_vpc.main.id

  # Only allow from web security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
    description     = "PostgreSQL from web servers"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "database-sg"
  }
}
```

**Network ACLs (Stateless - less common):**
```hcl
resource "aws_network_acl" "public" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.public[*].id

  # Inbound rules
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # Outbound rules
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = {
    Name = "public-nacl"
  }
}
```

**Troubleshooting VPC Connectivity:**

```bash
# Check route tables
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-12345678"

# Check if instance can reach internet
aws ec2 describe-instances --instance-ids i-12345678 \
  --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,PrivateIpAddress,SubnetId]'

# Check security groups
aws ec2 describe-security-groups --group-ids sg-12345678

# Check NACLs
aws ec2 describe-network-acls --network-acl-ids acl-12345678

# Common issues:
# 1. No route to IGW in public subnet → Add 0.0.0.0/0 → igw
# 2. No route to NAT in private subnet → Add 0.0.0.0/0 → nat
# 3. Security group blocking traffic → Update ingress rules
# 4. Instance in private subnet has no public IP → Expected, use NAT
# 5. NAT Gateway in private subnet → Must be in public subnet
```

**Best Practices:**

1. **Use multiple AZs for high availability**
2. **Separate subnets by tier (public/private/database)**
3. **One NAT Gateway per AZ** (expensive but highly available)
4. **Use VPC Flow Logs** for monitoring
5. **Tag all resources** for cost allocation
6. **Use Security Groups** (not NACLs) for most security
7. **Plan CIDR blocks** carefully (can't easily change later)
8. **Use Transit Gateway** for VPC-to-VPC connectivity at scale

---


### How do you design a highly available and scalable architecture on AWS?

**Detailed Explanation:**

Designing highly available (HA) and scalable architecture requires understanding multiple AWS services and how they work together to eliminate single points of failure and handle varying loads.

**Core Principles:**

1. **No Single Points of Failure**
2. **Multiple Availability Zones**
3. **Auto Scaling**
4. **Load Distribution**
5. **Decoupling Components**
6. **Monitoring and Self-Healing**

**Reference Architecture: Three-Tier Web Application**

```
┌────────────────────────────────────────────────────────────────────┐
│                          AWS Region (us-east-1)                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Route 53 (DNS)                            │  │
│  │              myapp.com → CloudFront                          │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
│                             │                                      │
│  ┌──────────────────────────┴──────────────────────────────────┐  │
│  │                    CloudFront (CDN)                          │  │
│  │            Global Edge Locations                             │  │
│  │            Cache static content                              │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
│                             │                                      │
│  ┌──────────────────────────┴──────────────────────────────────┐  │
│  │              Application Load Balancer (ALB)                 │  │
│  │              Public Subnets (Multi-AZ)                       │  │
│  │              Health Checks + SSL Termination                 │  │
│  └──────────────┬──────────────────────┬──────────────────────┘  │
│                 │                      │                          │
│  ┌──────────────┴──────────┐  ┌───────┴──────────────┐          │
│  │   Availability Zone 1    │  │  Availability Zone 2 │          │
│  │                          │  │                      │          │
│  │  ┌────────────────────┐  │  │  ┌────────────────┐ │          │
│  │  │ Web Tier (ASG)     │  │  │  │ Web Tier (ASG) │ │          │
│  │  │ - EC2/Containers   │  │  │  │ - EC2/Containers│ │         │
│  │  │ - Private Subnet   │  │  │  │ - Private Subnet│ │         │
│  │  └─────────┬──────────┘  │  │  └────────┬───────┘ │          │
│  │            │              │  │           │         │          │
│  │  ┌─────────┴──────────┐  │  │  ┌────────┴───────┐│          │
│  │  │ App Tier (ASG)     │  │  │  │ App Tier (ASG) ││          │
│  │  │ - Business Logic   │  │  │  │ - Business Logic││         │
│  │  │ - Private Subnet   │  │  │  │ - Private Subnet││         │
│  │  └─────────┬──────────┘  │  │  └────────┬───────┘│          │
│  │            │              │  │           │         │          │
│  │  ┌─────────┴──────────┐  │  │  ┌────────┴───────┐│          │
│  │  │ Data Tier          │←─┼──┼─→│ Data Tier      ││          │
│  │  │ - RDS Multi-AZ     │  │  │  │ - Read Replica ││          │
│  │  │ - ElastiCache      │  │  │  │ - ElastiCache  ││          │
│  │  │ - Private Subnet   │  │  │  │ - Private Subnet││         │
│  │  └────────────────────┘  │  │  └────────────────┘│          │
│  └──────────────────────────┘  └─────────────────────┘          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               S3 (Static Assets, Backups)                 │   │
│  │               Versioning + Cross-Region Replication       │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

**1. DNS Layer - Route 53:**

```hcl
# Terraform Configuration
resource "aws_route53_zone" "main" {
  name = "myapp.com"
}

# Alias record to CloudFront
resource "aws_route53_record" "main" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "myapp.com"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}

# Health check for failover
resource "aws_route53_health_check" "main" {
  fqdn              = "myapp.com"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name = "main-health-check"
  }
}

# Failover routing (primary/secondary regions)
resource "aws_route53_record" "primary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "myapp.com"
  type    = "A"

  set_identifier  = "primary"
  health_check_id = aws_route53_health_check.main.id

  failover_routing_policy {
    type = "PRIMARY"
  }

  alias {
    name                   = aws_lb.primary.dns_name
    zone_id                = aws_lb.primary.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "secondary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "myapp.com"
  type    = "A"

  set_identifier = "secondary"

  failover_routing_policy {
    type = "SECONDARY"
  }

  alias {
    name                   = aws_lb.secondary.dns_name
    zone_id                = aws_lb.secondary.zone_id
    evaluate_target_health = true
  }
}
```

**2. CDN Layer - CloudFront:**

```hcl
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Main distribution"
  default_root_object = "index.html"

  # Origin - ALB
  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Origin - S3 for static assets
  origin {
    domain_name = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id   = "s3"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "alb"

    forwarded_values {
      query_string = true
      headers      = ["Host", "Authorization"]

      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  # Cache behavior for static assets
  ordered_cache_behavior {
    path_pattern     = "/static/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "s3"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400  # 1 day
    max_ttl                = 31536000  # 1 year
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.main.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

**3. Load Balancing Layer - ALB:**

```hcl
resource "aws_lb" "main" {
  name               = "main-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  access_logs {
    bucket  = aws_s3_bucket.logs.id
    prefix  = "alb"
    enabled = true
  }

  tags = {
    Name = "main-alb"
  }
}

# Target Group for Web Tier
resource "aws_lb_target_group" "web" {
  name     = "web-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 3600
    enabled         = true
  }

  tags = {
    Name = "web-tg"
  }
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

# HTTP to HTTPS Redirect
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
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

# Path-based routing
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
```

**4. Compute Layer - Auto Scaling Groups:**

```hcl
# Launch Template for Web Tier
resource "aws_launch_template" "web" {
  name_prefix   = "web-"
  image_id      = data.aws_ami.amazon_linux_2.id
  instance_type = "t3.medium"

  vpc_security_group_ids = [aws_security_group.web.id]

  iam_instance_profile {
    arn = aws_iam_instance_profile.web.arn
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    db_endpoint     = aws_db_instance.main.endpoint
    cache_endpoint  = aws_elasticache_cluster.main.cache_nodes[0].address
    s3_bucket       = aws_s3_bucket.app_data.id
    environment     = "production"
  }))

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = 20
      volume_type = "gp3"
      iops        = 3000
      throughput  = 125
      encrypted   = true
      kms_key_id  = aws_kms_key.main.arn
    }
  }

  monitoring {
    enabled = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # IMDSv2 only
    http_put_response_hop_limit = 1
  }

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = "web-instance"
      Tier = "web"
    }
  }
}

# Auto Scaling Group for Web Tier
resource "aws_autoscaling_group" "web" {
  name                = "web-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.web.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = 2
  max_size         = 10
  desired_capacity = 2

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  enabled_metrics = [
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupMaxSize",
    "GroupMinSize",
    "GroupPendingInstances",
    "GroupStandbyInstances",
    "GroupTerminatingInstances",
    "GroupTotalInstances",
  ]

  tag {
    key                 = "Name"
    value               = "web-instance"
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Target Tracking Scaling Policy - CPU
resource "aws_autoscaling_policy" "cpu" {
  name                   = "cpu-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.web.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Target Tracking Scaling Policy - Request Count
resource "aws_autoscaling_policy" "request_count" {
  name                   = "request-count-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.web.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.main.arn_suffix}/${aws_lb_target_group.web.arn_suffix}"
    }
    target_value = 1000.0
  }
}

# Scheduled Scaling (for predictable traffic patterns)
resource "aws_autoscaling_schedule" "scale_up_morning" {
  scheduled_action_name  = "scale-up-morning"
  min_size               = 4
  max_size               = 10
  desired_capacity       = 4
  recurrence             = "0 8 * * MON-FRI"  # 8 AM weekdays
  autoscaling_group_name = aws_autoscaling_group.web.name
}

resource "aws_autoscaling_schedule" "scale_down_evening" {
  scheduled_action_name  = "scale-down-evening"
  min_size               = 2
  max_size               = 10
  desired_capacity       = 2
  recurrence             = "0 20 * * *"  # 8 PM daily
  autoscaling_group_name = aws_autoscaling_group.web.name
}
```

**5. Database Layer - RDS Multi-AZ:**

```hcl
# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "main-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = {
    Name = "main-db-subnet-group"
  }
}

# RDS Parameter Group
resource "aws_db_parameter_group" "postgres" {
  name   = "postgres-14-custom"
  family = "postgres14"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries longer than 1 second
  }
}

# Primary Database
resource "aws_db_instance" "main" {
  identifier     = "main-db"
  engine         = "postgres"
  engine_version = "14.7"
  instance_class = "db.r6g.xlarge"

  allocated_storage     = 100
  max_allocated_storage = 1000  # Storage autoscaling
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  db_name  = "myapp"
  username = "admin"
  password = random_password.db_password.result

  multi_az               = true  # High availability
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  parameter_group_name   = aws_db_parameter_group.postgres.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "main-db-final-snapshot"

  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  tags = {
    Name = "main-db"
  }
}

# Read Replica for Scaling Reads
resource "aws_db_instance" "read_replica" {
  identifier             = "main-db-read-replica"
  replicate_source_db    = aws_db_instance.main.identifier
  instance_class         = "db.r6g.large"
  publicly_accessible    = false
  skip_final_snapshot    = true
  performance_insights_enabled = true

  tags = {
    Name = "main-db-read-replica"
  }
}
```

**6. Caching Layer - ElastiCache:**

```hcl
# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "main-cache-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

# ElastiCache Parameter Group
resource "aws_elasticache_parameter_group" "redis" {
  name   = "redis-7-custom"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }
}

# Redis Replication Group (Multi-AZ with automatic failover)
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "main-redis"
  replication_group_description = "Main Redis cluster"

  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.r6g.large"
  number_cache_clusters = 2  # 1 primary + 1 replica
  port                 = 6379

  parameter_group_name = aws_elasticache_parameter_group.redis.name
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.cache.id]

  automatic_failover_enabled = true
  multi_az_enabled           = true

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token_enabled         = true
  auth_token                 = random_password.redis_auth.result

  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"
  maintenance_window       = "mon:05:00-mon:07:00"

  notification_topic_arn = aws_sns_topic.alerts.arn

  tags = {
    Name = "main-redis"
  }
}
```

**7. Storage Layer - S3:**

```hcl
# Application Data Bucket
resource "aws_s3_bucket" "app_data" {
  bucket = "myapp-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "app-data"
  }
}

# Versioning
resource "aws_s3_bucket_versioning" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

# Lifecycle Policy
resource "aws_s3_bucket_lifecycle_configuration" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  rule {
    id     = "transition-old-objects"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # Infrequent Access
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# Cross-Region Replication (for DR)
resource "aws_s3_bucket_replication_configuration" "app_data" {
  bucket = aws_s3_bucket.app_data.id
  role   = aws_iam_role.s3_replication.arn

  rule {
    id     = "replicate-all"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.app_data_replica.arn
      storage_class = "STANDARD_IA"

      encryption_configuration {
        replica_kms_key_id = aws_kms_key.s3_replica.arn
      }
    }
  }
}
```

**8. Monitoring and Alarms:**

```hcl
# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "infrastructure-alerts"

  tags = {
    Name = "infrastructure-alerts"
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "ops-team@example.com"
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  alarm_name          = "alb-unhealthy-hosts"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "Alert when unhealthy hosts > 1"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.web.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when RDS CPU > 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "rds-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when DB connections > 80"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "elasticache_cpu" {
  alarm_name          = "elasticache-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "Alert when ElastiCache CPU > 75%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.main.id
  }
}
```

**Availability Calculations:**

```
Single AZ: 99.5% = 43.8 hours downtime/year
Multi-AZ: 99.99% = 52 minutes downtime/year

With proper multi-AZ setup:
- ALB: 99.99% SLA
- EC2 Auto Scaling (multi-AZ): 99.99%
- RDS Multi-AZ: 99.95% SLA
- ElastiCache Multi-AZ: 99.99%
- S3: 99.99% availability, 99.999999999% durability

Combined: ~99.95% availability = ~4.4 hours downtime/year
```

**Cost Optimization Strategies:**

1. **Reserved Instances/Savings Plans** for baseline capacity
2. **Spot Instances** for fault-tolerant workloads
3. **Right-sizing** based on CloudWatch metrics
4. **S3 Intelligent-Tiering** for automatic cost optimization
5. **CloudFront** to reduce origin requests
6. **Aurora Serverless** for variable workloads
7. **Lambda** for event-driven tasks

**Disaster Recovery Strategy:**

```hcl
# Backup and restore across regions
# RTO: 1-4 hours, RPO: 1 hour

# Cross-region replication
resource "aws_s3_bucket_replication_configuration" "dr" {
  bucket = aws_s3_bucket.app_data.id
  role   = aws_iam_role.replication.arn

  rule {
    status = "Enabled"

    destination {
      bucket = aws_s3_bucket.dr_replica.arn
      # In us-west-2
    }
  }
}

# RDS automated backups + snapshots
# Copy snapshots to DR region
resource "aws_db_snapshot_copy" "dr" {
  source_db_snapshot_identifier = aws_db_snapshot.main.id
  target_db_snapshot_identifier = "main-db-dr-snapshot"
  destination_region            = "us-west-2"
  kms_key_id                    = aws_kms_key.dr.arn
}

# Infrastructure as Code in both regions
# Can recreate entire stack in DR region within hours
```

**Best Practices Summary:**

1. **Multi-AZ Everything**: ALB, ASG, RDS, ElastiCache
2. **Auto Scaling**: Handle traffic spikes automatically
3. **Monitoring**: CloudWatch + SNS for proactive alerts
4. **Security**: Security groups, NACLs, encryption at rest and in transit
5. **Backups**: Automated backups, snapshots, cross-region replication
6. **Immutable Infrastructure**: Use launch templates, replace don't modify
7. **Infrastructure as Code**: Terraform/CloudFormation for reproducibility
8. **Cost Management**: Tags, budgets, right-sizing

---

## Terraform / IaC

### Explain Terraform state management and best practices.

**Detailed Explanation:**

Terraform state is a critical component that tracks the current state of your infrastructure. Mismanaging state can lead to infrastructure drift, corruption, or complete loss of control over your resources.

**What is Terraform State?**

Terraform state (`terraform.tfstate`) is a JSON file that maps your Terraform configuration to real-world resources. It contains:
- Resource IDs and attributes
- Metadata about resources
- Dependencies between resources
- Provider configuration

**Local State (Development Only):**

```bash
# Initialize Terraform
terraform init

# Creates local state file
terraform apply

# State stored locally
ls -la
terraform.tfstate
terraform.tfstate.backup  # Previous state

# View state
terraform state list
terraform state show aws_instance.web

# State file content (simplified):
{
  "version": 4,
  "terraform_version": "1.6.0",
  "resources": [
    {
      "mode": "managed",
      "type": "aws_instance",
      "name": "web",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "attributes": {
            "id": "i-1234567890abcdef0",
            "ami": "ami-0c55b159cbfafe1f0",
            "instance_type": "t3.micro",
            "private_ip": "10.0.1.10"
          }
        }
      ]
    }
  ]
}
```

**Problems with Local State:**

1. **No Collaboration**: Team members can't share state
2. **No Locking**: Concurrent runs corrupt state
3. **No Encryption**: Sensitive data in plain text
4. **No Versioning**: Can't roll back to previous state
5. **Manual Backup**: Risk of losing state file

**Remote State - S3 Backend (Production):**

**backend.tf:**
```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "production/vpc/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789:key/abc-123"
    dynamodb_table = "terraform-state-lock"
    
    # Versioning for state history
    versioning     = true
  }
}
```

**Setting Up S3 Backend:**

**1. Create S3 Bucket:**
```hcl
# bootstrap/main.tf - Run this first to create backend resources
resource "aws_s3_bucket" "terraform_state" {
  bucket = "mycompany-terraform-state"

  lifecycle {
    prevent_destroy = true  # Never delete state bucket!
  }

  tags = {
    Name = "Terraform State"
  }
}

# Enable versioning
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform.arn
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}
```

**2. Create DynamoDB Table for State Locking:**
```hcl
resource "aws_dynamodb_table" "terraform_locks" {
  name           = "terraform-state-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "Terraform State Lock"
  }
}
```

**3. Initialize Backend:**
```bash
# Bootstrap: Create backend resources first
cd bootstrap
terraform init
terraform apply

# Main infrastructure: Configure backend
cd ../main
terraform init
# Terraform will prompt to migrate existing state to S3

# Verify backend configuration
terraform show
```

**State Locking with DynamoDB:**

```bash
# Terminal 1
terraform apply
# Acquires lock in DynamoDB

# Terminal 2
terraform apply
# Error: state locked!
# Lock ID: 12345678-1234-1234-1234-123456789012
# Acquired by: user@hostname
# Acquired at: 2026-02-24 10:00:00

# Lock released automatically after apply completes

# Force unlock (dangerous!)
terraform force-unlock 12345678-1234-1234-1234-123456789012
```

**Workspaces for Multi-Environment:**

```bash
# List workspaces
terraform workspace list
* default

# Create workspace
terraform workspace new staging
terraform workspace new production

# Switch workspace
terraform workspace select staging

# Current workspace
terraform workspace show
staging

# State files are isolated per workspace:
# s3://bucket/env:/staging/terraform.tfstate
# s3://bucket/env:/production/terraform.tfstate
```

**Using Workspaces in Configuration:**
```hcl
locals {
  env = terraform.workspace

  instance_counts = {
    default    = 1
    staging    = 2
    production = 5
  }

  instance_type = {
    default    = "t3.micro"
    staging    = "t3.small"
    production = "t3.large"
  }
}

resource "aws_instance" "web" {
  count         = local.instance_counts[local.env]
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = local.instance_type[local.env]

  tags = {
    Name        = "web-${local.env}-${count.index}"
    Environment = local.env
  }
}
```

**Alternative: Directory Structure for Environments:**

```
terraform/
├── modules/
│   ├── vpc/
│   ├── eks/
│   └── rds/
├── environments/
│   ├── dev/
│   │   ├── backend.tf
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── backend.tf
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── production/
│       ├── backend.tf
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
```

**environments/production/backend.tf:**
```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "production/terraform.tfstate"  # Different key per env
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

**State Management Commands:**

```bash
# List all resources in state
terraform state list

# Show details of specific resource
terraform state show aws_instance.web

# Remove resource from state (doesn't destroy resource)
terraform state rm aws_instance.web

# Move resource to different address
terraform state mv aws_instance.web aws_instance.web_server

# Import existing resource into state
terraform import aws_instance.web i-1234567890abcdef0

# Pull remote state to local
terraform state pull > terraform.tfstate

# Push local state to remote
terraform state push terraform.tfstate

# Replace provider in state (after provider migration)
terraform state replace-provider registry.terraform.io/hashicorp/aws \
  registry.terraform.io/hashicorp/aws
```

**State File Structure:**

```json
{
  "version": 4,
  "terraform_version": "1.6.0",
  "serial": 15,
  "lineage": "abc-123-def-456",
  "outputs": {
    "vpc_id": {
      "value": "vpc-12345678",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "aws_vpc",
      "name": "main",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "id": "vpc-12345678",
            "cidr_block": "10.0.0.0/16",
            "tags": {
              "Name": "main-vpc"
            }
          },
          "private": "eyJzY2hlbWFfdmVyc2lvbiI6IjEifQ==",
          "dependencies": []
        }
      ]
    }
  ]
}
```

**Sensitive Data in State:**

State files contain sensitive data (passwords, keys, etc.). Must protect!

```hcl
# Mark outputs as sensitive
output "db_password" {
  value     = aws_db_instance.main.password
  sensitive = true
}

# State still contains the password!
# View state (sensitive values shown):
terraform state pull | jq '.resources[] | select(.type=="aws_db_instance")'

# Best practices:
# 1. Use KMS encryption for S3 state
# 2. Restrict S3 bucket access via IAM
# 3. Enable S3 bucket versioning
# 4. Use AWS Secrets Manager instead of storing in Terraform
```

**Handling Sensitive Values:**

```hcl
# Bad: Password in Terraform
resource "aws_db_instance" "main" {
  password = "hardcoded-password"  # Don't do this!
}

# Better: Use AWS Secrets Manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "production/db/password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}

# Best: Let AWS manage passwords
resource "aws_db_instance" "main" {
  manage_master_user_password = true  # AWS Secrets Manager integration
}
```

**State Backup and Recovery:**

```bash
# S3 versioning keeps all state versions
aws s3api list-object-versions \
  --bucket mycompany-terraform-state \
  --prefix production/terraform.tfstate

# Restore previous version
aws s3api get-object \
  --bucket mycompany-terraform-state \
  --key production/terraform.tfstate \
  --version-id abc123 \
  terraform.tfstate.backup

# Restore state
terraform state push terraform.tfstate.backup
```

**State Disaster Recovery:**

```bash
# 1. State file deleted - Recover from S3 versioning
aws s3api list-object-versions \
  --bucket mycompany-terraform-state \
  --prefix production/terraform.tfstate

# Download previous version
aws s3api get-object \
  --bucket mycompany-terraform-state \
  --key production/terraform.tfstate \
  --version-id <version-id> \
  restored-terraform.tfstate

# 2. State corrupted - Restore from backup
terraform state push terraform.tfstate.backup

# 3. State completely lost - Rebuild from scratch
# For each resource:
terraform import aws_vpc.main vpc-12345678
terraform import aws_subnet.public[0] subnet-12345678
# ... (tedious but possible)

# 4. Prevention: Cross-region replication
resource "aws_s3_bucket_replication_configuration" "state" {
  bucket = aws_s3_bucket.terraform_state.id
  role   = aws_iam_role.replication.arn

  rule {
    status = "Enabled"
    destination {
      bucket = aws_s3_bucket.terraform_state_replica.arn
      # In different region
    }
  }
}
```

**Remote State Data Source:**

Share state between Terraform projects:

```hcl
# Project A: VPC infrastructure
# outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

# Project B: Application infrastructure
# Read state from Project A
data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = "mycompany-terraform-state"
    key    = "production/vpc/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use outputs from Project A
resource "aws_instance" "web" {
  subnet_id = data.terraform_remote_state.vpc.outputs.private_subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.web.id]
}
```

**State Locking Deep Dive:**

```bash
# DynamoDB lock table structure:
aws dynamodb get-item \
  --table-name terraform-state-lock \
  --key '{"LockID":{"S":"mycompany-terraform-state/production/terraform.tfstate-md5"}}'

{
  "Item": {
    "LockID": {"S": "mycompany-terraform-state/production/terraform.tfstate-md5"},
    "Info": {
      "S": "{\"ID\":\"abc-123\",\"Operation\":\"OperationTypeApply\",\"Info\":\"\",\"Who\":\"user@hostname\",\"Version\":\"1.6.0\",\"Created\":\"2026-02-24T10:00:00Z\",\"Path\":\"production/terraform.tfstate\"}"
    }
  }
}

# Lock stuck? Check who has it:
aws dynamodb get-item --table-name terraform-state-lock \
  --key '{"LockID":{"S":"<lockid>"}}' \
  | jq -r '.Item.Info.S' | jq .

# Force unlock if necessary
terraform force-unlock <lock-id>
```

**Best Practices:**

1. **Never Edit State Files Manually**: Use `terraform state` commands
2. **Always Use Remote Backend**: Never use local state in teams
3. **Enable State Locking**: Prevent concurrent modifications
4. **Encrypt State**: Use KMS encryption for S3
5. **Version State**: Enable S3 versioning
6. **Backup State**: Cross-region replication
7. **Restrict Access**: IAM policies for state bucket
8. **Separate State Per Environment**: Different state files for dev/staging/prod
9. **Use Data Sources**: Share outputs between projects
10. **Regular Backups**: Automated state backup to separate location

**Common State Issues:**

**1. State Drift:**
```bash
# Someone modified resources outside Terraform
terraform plan
# Shows drift

# Refresh state to match reality
terraform apply -refresh-only

# Or reconcile changes
terraform apply
```

**2. Orphaned Resources:**
```bash
# Resource deleted outside Terraform
terraform apply
# Error: resource not found

# Remove from state
terraform state rm aws_instance.deleted
```

**3. Duplicate Resources:**
```bash
# Resource created twice
terraform apply
# Error: resource already exists

# Import existing resource
terraform import aws_instance.duplicate i-1234567890
```

**4. State Lock Timeout:**
```bash
# Process killed while locked
terraform apply
# Error: state locked

# Force unlock
terraform force-unlock <lock-id>
```

---


## CI/CD / DevOps

### Explain a complete CI/CD pipeline and best practices.

**Detailed Explanation:**

A CI/CD pipeline automates the software delivery process from code commit to production deployment. Understanding each stage and implementing best practices is crucial for DevOps engineers.

**Complete CI/CD Pipeline Architecture:**

```
┌──────────────────────────────────────────────────────────────────┐
│                         DEVELOPER                                 │
│                              │                                    │
│                    git commit & push                              │
│                              ▼                                    │
├──────────────────────────────────────────────────────────────────┤
│                      SOURCE CONTROL                               │
│               GitHub/GitLab/Bitbucket                             │
│                    Webhook Trigger                                │
│                              ▼                                    │
├──────────────────────────────────────────────────────────────────┤
│                     CI PIPELINE (Build)                           │
│  1. Checkout Code                                                 │
│  2. Install Dependencies                                          │
│  3. Run Unit Tests                                                │
│  4. Run Linting/Code Quality                                      │
│  5. Run Security Scans                                            │
│  6. Build Artifact/Container                                      │
│  7. Push to Registry                                              │
│                              ▼                                    │
├──────────────────────────────────────────────────────────────────┤
│                   CD PIPELINE (Deploy)                            │
│  8. Deploy to Dev Environment                                     │
│  9. Run Integration Tests                                         │
│ 10. Deploy to Staging                                             │
│ 11. Run E2E Tests                                                 │
│ 12. Manual Approval (Optional)                                    │
│ 13. Deploy to Production                                          │
│ 14. Health Checks                                                 │
│ 15. Smoke Tests                                                   │
│                              ▼                                    │
├──────────────────────────────────────────────────────────────────┤
│                    MONITORING & FEEDBACK                          │
│    Metrics, Logs, Alerts, Rollback if Needed                     │
└──────────────────────────────────────────────────────────────────┘
```

**1. GitHub Actions Pipeline Example:**

**.github/workflows/ci-cd.yml:**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: my-app
  EKS_CLUSTER: production-cluster

jobs:
  # Job 1: Code Quality and Testing
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:6-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
        run: |
          # Flake8 for Python linting
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          # Black for code formatting
          black --check .
          # isort for import sorting
          isort --check-only .

      - name: Run security scan
        run: |
          # Bandit for security issues
          bandit -r . -f json -o bandit-report.json
          # Safety for dependency vulnerabilities
          safety check --json

      - name: Run unit tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/unit \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --junitxml=pytest-report.xml \
            -v

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/integration -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

  # Job 2: Build and Push Docker Image
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            VERSION=${{ github.sha }}
            BUILD_DATE=${{ github.event.head_commit.timestamp }}

      - name: Scan image for vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.meta.outputs.tags }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  # Job 3: Deploy to Dev
  deploy-dev:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: development

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name dev-cluster --region ${{ env.AWS_REGION }}

      - name: Deploy to Kubernetes
        run: |
          # Update image in deployment
          kubectl set image deployment/my-app \
            my-app=${{ needs.build.outputs.image-tag }} \
            -n development

          # Wait for rollout
          kubectl rollout status deployment/my-app -n development --timeout=5m

      - name: Run smoke tests
        run: |
          sleep 30
          curl -f https://dev.myapp.com/health || exit 1

  # Job 4: Deploy to Staging
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name staging-cluster --region ${{ env.AWS_REGION }}

      - name: Deploy with Helm
        run: |
          helm upgrade --install my-app ./charts/my-app \
            --namespace staging \
            --set image.tag=${{ needs.build.outputs.image-tag }} \
            --set environment=staging \
            --wait \
            --timeout 5m

      - name: Run E2E tests
        run: |
          npm ci
          npm run test:e2e -- --baseUrl=https://staging.myapp.com

      - name: Performance tests
        run: |
          # Run k6 load tests
          k6 run --vus 10 --duration 30s tests/load/api-test.js

  # Job 5: Deploy to Production
  deploy-production:
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://myapp.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name ${{ env.EKS_CLUSTER }} --region ${{ env.AWS_REGION }}

      - name: Canary Deployment (10%)
        run: |
          # Deploy canary version
          kubectl apply -f k8s/canary-deployment.yaml
          kubectl set image deployment/my-app-canary \
            my-app=${{ needs.build.outputs.image-tag }} \
            -n production

          # Monitor for 5 minutes
          sleep 300

      - name: Check canary metrics
        run: |
          # Check error rate, latency from Prometheus/CloudWatch
          python scripts/check_canary_metrics.py

      - name: Full Production Deployment
        run: |
          # Blue-green deployment
          helm upgrade --install my-app ./charts/my-app \
            --namespace production \
            --set image.tag=${{ needs.build.outputs.image-tag }} \
            --set replicaCount=10 \
            --wait \
            --timeout 10m

          # Wait for rollout
          kubectl rollout status deployment/my-app -n production

      - name: Smoke tests
        run: |
          curl -f https://myapp.com/health || exit 1
          curl -f https://myapp.com/api/version || exit 1

      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release v${{ github.run_number }}
          body: |
            Deployed to production
            Commit: ${{ github.sha }}
          draft: false
          prerelease: false

      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment completed!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
```

**2. GitLab CI/CD Pipeline:**

**.gitlab-ci.yml:**
```yaml
stages:
  - test
  - build
  - deploy-dev
  - deploy-staging
  - deploy-production

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

# Test Stage
test:unit:
  stage: test
  image: python:3.11
  services:
    - postgres:14
    - redis:6-alpine
  variables:
    POSTGRES_DB: test
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  before_script:
    - pip install -r requirements.txt
    - pip install -r requirements-dev.txt
  script:
    - flake8 .
    - black --check .
    - pytest tests/unit --cov=src --cov-report=xml
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

test:security:
  stage: test
  image: python:3.11
  script:
    - pip install bandit safety
    - bandit -r . -f json -o bandit-report.json
    - safety check
  allow_failure: true

# Build Stage
build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
    - docker tag $IMAGE_TAG $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main
    - develop

# Deploy to Dev
deploy:dev:
  stage: deploy-dev
  image: alpine/k8s:1.28.0
  before_script:
    - kubectl config use-context dev-cluster
  script:
    - kubectl set image deployment/my-app my-app=$IMAGE_TAG -n development
    - kubectl rollout status deployment/my-app -n development
  environment:
    name: development
    url: https://dev.myapp.com
  only:
    - develop

# Deploy to Staging
deploy:staging:
  stage: deploy-staging
  image: alpine/helm:latest
  before_script:
    - kubectl config use-context staging-cluster
  script:
    - helm upgrade --install my-app ./charts/my-app
        --namespace staging
        --set image.tag=$CI_COMMIT_SHORT_SHA
        --wait
  environment:
    name: staging
    url: https://staging.myapp.com
  only:
    - main

# Deploy to Production
deploy:production:
  stage: deploy-production
  image: alpine/helm:latest
  before_script:
    - kubectl config use-context prod-cluster
  script:
    - helm upgrade --install my-app ./charts/my-app
        --namespace production
        --set image.tag=$CI_COMMIT_SHORT_SHA
        --set replicaCount=10
        --wait
  environment:
    name: production
    url: https://myapp.com
  when: manual  # Require manual approval
  only:
    - main
```

**3. Jenkins Pipeline (Jenkinsfile):**

```groovy
pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-east-1'
        ECR_REPO = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/my-app"
        IMAGE_TAG = "${env.GIT_COMMIT.take(7)}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    agent {
                        docker {
                            image 'python:3.11'
                        }
                    }
                    steps {
                        sh '''
                            pip install -r requirements.txt
                            pip install -r requirements-dev.txt
                            pytest tests/unit --cov=src --junitxml=results.xml
                        '''
                    }
                    post {
                        always {
                            junit 'results.xml'
                        }
                    }
                }
                
                stage('Linting') {
                    agent {
                        docker {
                            image 'python:3.11'
                        }
                    }
                    steps {
                        sh '''
                            pip install flake8 black
                            flake8 .
                            black --check .
                        '''
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        sh '''
                            pip install bandit
                            bandit -r . -f json -o bandit-report.json
                        '''
                    }
                }
            }
        }
        
        stage('Build') {
            steps {
                script {
                    docker.build("${ECR_REPO}:${IMAGE_TAG}")
                }
            }
        }
        
        stage('Push to ECR') {
            steps {
                script {
                    sh '''
                        aws ecr get-login-password --region ${AWS_REGION} | \
                            docker login --username AWS --password-stdin ${ECR_REPO}
                        docker push ${ECR_REPO}:${IMAGE_TAG}
                        docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_REPO}:latest
                        docker push ${ECR_REPO}:latest
                    '''
                }
            }
        }
        
        stage('Deploy to Dev') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    kubectl set image deployment/my-app \
                        my-app=${ECR_REPO}:${IMAGE_TAG} \
                        -n development
                    kubectl rollout status deployment/my-app -n development
                '''
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    helm upgrade --install my-app ./charts/my-app \
                        --namespace staging \
                        --set image.tag=${IMAGE_TAG} \
                        --wait
                '''
            }
        }
        
        stage('Integration Tests') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    npm ci
                    npm run test:e2e -- --baseUrl=https://staging.myapp.com
                '''
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                sh '''
                    helm upgrade --install my-app ./charts/my-app \
                        --namespace production \
                        --set image.tag=${IMAGE_TAG} \
                        --set replicaCount=10 \
                        --wait \
                        --timeout 10m
                '''
            }
        }
        
        stage('Smoke Tests') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    curl -f https://myapp.com/health || exit 1
                '''
            }
        }
    }
    
    post {
        success {
            slackSend(
                color: 'good',
                message: "Deployment successful: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "Deployment failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
        always {
            cleanWs()
        }
    }
}
```

**CI/CD Best Practices:**

**1. Fast Feedback:**
```yaml
# Fail fast - run quick tests first
stages:
  - lint          # 1-2 minutes
  - unit-test     # 2-5 minutes
  - build         # 5-10 minutes
  - integration   # 10-15 minutes
  - deploy        # 5-10 minutes
```

**2. Parallel Execution:**
```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
```

**3. Caching:**
```yaml
- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: |
      ~/.cache/pip
      node_modules
    key: ${{ runner.os }}-${{ hashFiles('**/requirements.txt', '**/package-lock.json') }}
```

**4. Security:**
```yaml
# Scan for vulnerabilities
- name: Run Trivy
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    severity: 'CRITICAL,HIGH'
    
# Scan Docker image
- name: Scan Docker image
  run: |
    trivy image --severity HIGH,CRITICAL myapp:latest
```

**5. Automated Rollback:**
```bash
# Kubernetes rollback
kubectl rollout undo deployment/my-app -n production

# Helm rollback
helm rollback my-app -n production
```

**6. Blue-Green Deployment:**
```yaml
# Deploy green version
kubectl apply -f green-deployment.yaml

# Test green version
curl https://green.myapp.com/health

# Switch traffic from blue to green
kubectl patch service my-app -p '{"spec":{"selector":{"version":"green"}}}'

# Monitor for issues
# If problems, switch back to blue
kubectl patch service my-app -p '{"spec":{"selector":{"version":"blue"}}}'
```

**7. Canary Deployment:**
```yaml
# Deploy canary with 10% traffic
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
  - my-app
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: my-app
        subset: canary
  - route:
    - destination:
        host: my-app
        subset: stable
      weight: 90
    - destination:
        host: my-app
        subset: canary
      weight: 10
```

**8. Feature Flags:**
```python
# LaunchDarkly / Unleash integration
from ldclient import get as get_ld_client

ld_client = get_ld_client()
user = {"key": "user-123", "email": "user@example.com"}

if ld_client.variation("new-feature", user, False):
    # New feature code
    process_with_new_algorithm()
else:
    # Old feature code
    process_with_old_algorithm()
```

**9. Database Migrations:**
```yaml
# Run migrations before deployment
- name: Run database migrations
  run: |
    kubectl run migrate --rm -i \
      --image=$IMAGE_TAG \
      --restart=Never \
      --namespace=production \
      -- python manage.py migrate
```

**10. Monitoring Integration:**
```yaml
- name: Create Datadog deployment marker
  run: |
    curl -X POST "https://api.datadoghq.com/api/v1/events" \
      -H "DD-API-KEY: ${{ secrets.DD_API_KEY }}" \
      -d @- << EOF
    {
      "title": "Deployment to production",
      "text": "Version ${{ github.sha }} deployed",
      "tags": ["environment:production","service:my-app"]
    }
    EOF
```

---

## Linux / Systems

### Explain Linux boot process and systemd.

**Detailed Explanation:**

Understanding the Linux boot process and systemd is essential for troubleshooting system startup issues and managing services.

**Linux Boot Process:**

```
1. BIOS/UEFI
    ↓
2. Boot Loader (GRUB)
    ↓
3. Kernel Initialization
    ↓
4. Init System (systemd)
    ↓
5. System Services
    ↓
6. Login
```

**Detailed Boot Stages:**

**Stage 1: BIOS/UEFI**
```
Power On
    ↓
POST (Power-On Self-Test)
    ↓
Detect Hardware (CPU, RAM, Disks)
    ↓
Locate Boot Device
    ↓
Read MBR (Master Boot Record) / GPT (GUID Partition Table)
    ↓
Load Boot Loader
```

**Stage 2: Boot Loader (GRUB)**
```bash
# GRUB Configuration
/boot/grub/grub.cfg

# Example GRUB entry
menuentry 'Ubuntu' {
    set root='hd0,gpt2'
    linux /vmlinuz-5.15.0-50-generic root=UUID=abc-123 ro quiet splash
    initrd /initrd.img-5.15.0-50-generic
}

# GRUB commands
grub-install /dev/sda  # Install GRUB
update-grub            # Regenerate GRUB config
```

**Stage 3: Kernel Initialization**
```
Load Kernel (vmlinuz)
    ↓
Decompress Kernel
    ↓
Load initramfs (initial RAM filesystem)
    ↓
Mount root filesystem (read-only)
    ↓
Start init process (PID 1) - systemd
```

**View kernel boot messages:**
```bash
dmesg | less
dmesg | grep -i error

# Kernel ring buffer
journalctl -k

# Boot messages
journalctl -b
```

**Stage 4: systemd Initialization**

**systemd - System and Service Manager**

systemd is the init system (PID 1) on most modern Linux distributions.

**Key Concepts:**

**1. Units:**
Different types of systemd resources:

- **Service units (.service)**: System services
- **Target units (.target)**: Group of units (like runlevels)
- **Mount units (.mount)**: Filesystem mount points
- **Socket units (.socket)**: IPC sockets
- **Timer units (.timer)**: Scheduled tasks (like cron)
- **Device units (.device)**: Hardware devices

**2. Service Unit Example:**

**/etc/systemd/system/myapp.service:**
```ini
[Unit]
Description=My Application Service
Documentation=https://docs.myapp.com
After=network.target postgresql.service
Requires=postgresql.service
Wants=redis.service

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
Environment="NODE_ENV=production"
Environment="PORT=3000"
EnvironmentFile=/opt/myapp/.env
ExecStartPre=/opt/myapp/scripts/pre-start.sh
ExecStart=/usr/bin/node /opt/myapp/server.js
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/opt/myapp/scripts/stop.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/myapp/data

# Resource Limits
LimitNOFILE=65536
MemoryLimit=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

**Service Types:**

```ini
# simple - main process (default)
Type=simple
ExecStart=/usr/bin/myapp

# forking - process forks to background
Type=forking
ExecStart=/usr/bin/daemon
PIDFile=/run/daemon.pid

# oneshot - process exits after starting
Type=oneshot
ExecStart=/usr/bin/setup-script.sh

# notify - process sends ready notification
Type=notify
ExecStart=/usr/bin/myapp
NotifyAccess=main

# dbus - service acquires D-Bus name
Type=dbus
BusName=com.example.myapp
```

**3. systemd Commands:**

```bash
# Service Management
systemctl start myapp.service       # Start service
systemctl stop myapp.service        # Stop service
systemctl restart myapp.service     # Restart service
systemctl reload myapp.service      # Reload config without restart
systemctl status myapp.service      # Check status
systemctl enable myapp.service      # Start at boot
systemctl disable myapp.service     # Don't start at boot
systemctl is-active myapp.service   # Check if running
systemctl is-enabled myapp.service  # Check if enabled

# View logs
journalctl -u myapp.service         # All logs
journalctl -u myapp.service -f      # Follow logs
journalctl -u myapp.service --since today
journalctl -u myapp.service --since "2026-02-24 10:00:00"
journalctl -u myapp.service -n 100  # Last 100 lines

# List units
systemctl list-units                # All active units
systemctl list-units --type=service # All services
systemctl list-unit-files           # All unit files
systemctl list-dependencies myapp.service  # Dependencies

# System state
systemctl status                    # System status
systemctl list-jobs                 # Active jobs
systemctl is-system-running         # System state

# Reload systemd
systemctl daemon-reload             # Reload unit files
```

**4. Targets (Runlevels):**

Targets are groups of units, similar to runlevels in SysV init.

```bash
# Common targets
multi-user.target    # Multi-user system (runlevel 3)
graphical.target     # Multi-user with GUI (runlevel 5)
rescue.target        # Single-user mode (runlevel 1)
emergency.target     # Emergency shell
reboot.target        # Reboot
poweroff.target      # Power off

# Check current target
systemctl get-default
# multi-user.target

# Change default target
systemctl set-default graphical.target

# Switch target
systemctl isolate multi-user.target

# List targets
systemctl list-units --type=target
```

**5. Timer Units (systemd cron alternative):**

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Run backup daily

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00  # Every day at 2 AM
Persistent=true             # Run if missed

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Backup Service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
```

```bash
# Enable timer
systemctl enable backup.timer
systemctl start backup.timer

# List timers
systemctl list-timers

# Check timer status
systemctl status backup.timer
```

**6. Socket Activation:**

systemd can start services on-demand when a socket is accessed.

```ini
# /etc/systemd/system/myapp.socket
[Unit]
Description=My App Socket

[Socket]
ListenStream=8080
Accept=no

[Install]
WantedBy=sockets.target
```

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My App Service
Requires=myapp.socket

[Service]
Type=simple
ExecStart=/usr/bin/myapp
StandardInput=socket
```

**7. journalctl - System Logging:**

```bash
# View all logs
journalctl

# Follow logs (like tail -f)
journalctl -f

# Show logs since boot
journalctl -b
journalctl -b -1  # Previous boot

# Filter by time
journalctl --since "2026-02-24"
journalctl --since "2 hours ago"
journalctl --until "2026-02-24 12:00:00"

# Filter by unit
journalctl -u nginx.service
journalctl -u nginx.service -u postgresql.service

# Filter by priority
journalctl -p err       # Errors only
journalctl -p warning   # Warnings and above

# Filter by identifier
journalctl -t sshd

# Show kernel messages
journalctl -k

# Show only current boot
journalctl -b 0

# Reverse order (newest first)
journalctl -r

# Output formats
journalctl -o json-pretty
journalctl -o verbose

# Disk usage
journalctl --disk-usage

# Vacuum old logs
journalctl --vacuum-time=30d  # Keep 30 days
journalctl --vacuum-size=1G   # Keep 1GB
```

**8. systemd-analyze:**

```bash
# Boot time analysis
systemd-analyze
# Startup finished in 3.2s (kernel) + 5.8s (userspace) = 9.0s

# Service startup times
systemd-analyze blame
# 2.5s postgresql.service
# 1.8s network.service
# 1.2s docker.service

# Critical chain (slowest path)
systemd-analyze critical-chain

# Plot boot process
systemd-analyze plot > boot.svg

# Verify unit file
systemd-analyze verify myapp.service
```

**9. Resource Control (cgroups):**

```ini
[Service]
# CPU
CPUQuota=200%        # 2 cores
CPUShares=1024       # Relative weight

# Memory
MemoryLimit=2G       # Hard limit
MemoryHigh=1.5G      # Soft limit (throttle)

# IO
IOWeight=100         # Relative weight (10-1000)
IOReadBandwidthMax=/dev/sda 10M
IOWriteBandwidthMax=/dev/sda 5M

# Processes
TasksMax=100         # Max number of processes

# Files
LimitNOFILE=65536    # Max open files
```

**View resource usage:**
```bash
systemctl show myapp.service -p CPUQuotaPerSecUSec
systemctl show myapp.service -p MemoryCurrent

# cgroup stats
systemd-cgtop
```

**10. Troubleshooting systemd:**

```bash
# Service fails to start
systemctl status myapp.service
# Check "Active" line and error messages

# View full logs
journalctl -u myapp.service -n 50 --no-pager

# Check unit file syntax
systemd-analyze verify myapp.service

# List failed units
systemctl --failed

# Reset failed state
systemctl reset-failed myapp.service

# View dependencies
systemctl list-dependencies myapp.service

# Check if service is masked
systemctl is-enabled myapp.service
# masked - can't start (unmask with: systemctl unmask)

# Emergency mode
# Edit GRUB: add systemd.unit=emergency.target
# Or at boot: Ctrl+Alt+Del, add "emergency" to kernel line
```

**Common Issues:**

**1. Service won't start:**
```bash
# Check logs
journalctl -u myapp.service -n 50

# Common causes:
# - Wrong path in ExecStart
# - Missing dependencies (After= directive)
# - Permission issues
# - Port already in use
```

**2. Service starts but crashes:**
```bash
# Check for segfaults
journalctl -u myapp.service | grep -i "signal"

# Increase restart delay
RestartSec=30

# Limit restart attempts
StartLimitBurst=5
StartLimitIntervalSec=300
```

**3. Slow boot:**
```bash
# Find slow services
systemd-analyze blame

# Disable unnecessary services
systemctl disable bluetooth.service
systemctl mask plymouth-quit-wait.service
```

**Best Practices:**

1. **Use systemd for all services**: Don't use init.d scripts
2. **Enable logging**: `StandardOutput=journal`
3. **Set resource limits**: Prevent runaway processes
4. **Use Wants instead of Requires**: For soft dependencies
5. **Configure restarts**: `Restart=on-failure`
6. **Security hardening**: Use ProtectSystem, PrivateTmp, etc.
7. **Document services**: Add Description and Documentation
8. **Test before enabling**: Start service manually first
9. **Version control unit files**: Keep in Git
10. **Monitor service health**: Use monitoring tools with systemd

---


## Networking

### Explain the OSI model and TCP/IP stack with practical examples.

**Detailed Explanation:**

The OSI (Open Systems Interconnection) model and TCP/IP stack are fundamental frameworks for understanding network communication. DevOps engineers need this knowledge for troubleshooting connectivity issues, configuring firewalls, and optimizing network performance.

**OSI Model - 7 Layers:**

```
┌─────────────────────────────────────────────────────────┐
│ Layer 7: Application  │ HTTP, FTP, SMTP, DNS, SSH       │
├─────────────────────────────────────────────────────────┤
│ Layer 6: Presentation │ SSL/TLS, JPEG, ASCII, Encryption│
├─────────────────────────────────────────────────────────┤
│ Layer 5: Session      │ NetBIOS, RPC, SQL Sessions      │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Transport    │ TCP, UDP, Port Numbers          │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Network      │ IP, ICMP, Routing, IP Addresses │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Data Link    │ Ethernet, MAC Addresses, Switches│
├─────────────────────────────────────────────────────────┤
│ Layer 1: Physical     │ Cables, Hubs, Signals, Bits     │
└─────────────────────────────────────────────────────────┘
```

**TCP/IP Model - 4 Layers:**

```
┌─────────────────────────────────────────────────┐
│ Application Layer    │ HTTP, FTP, DNS, SSH      │
│ (OSI 5-7)            │                          │
├─────────────────────────────────────────────────┤
│ Transport Layer      │ TCP, UDP                 │
│ (OSI 4)              │                          │
├─────────────────────────────────────────────────┤
│ Internet Layer       │ IP, ICMP, ARP            │
│ (OSI 3)              │                          │
├─────────────────────────────────────────────────┤
│ Network Access Layer │ Ethernet, WiFi           │
│ (OSI 1-2)            │                          │
└─────────────────────────────────────────────────┘
```

**Detailed Layer Breakdown:**

**Layer 1: Physical Layer**

Physical transmission of bits over a medium.

```
Devices: Cables, Hubs, Repeaters, Network Interface Cards
Data Unit: Bits (0s and 1s)
Protocols: Ethernet physical (100BASE-T, 1000BASE-T)

Example:
- Cat6 Ethernet cable
- Fiber optic cable
- WiFi radio waves
```

**Troubleshooting:**
```bash
# Check physical link status
ethtool eth0
# Link detected: yes
# Speed: 1000Mb/s
# Duplex: Full

# Check cable
ip link show eth0
# state UP - physically connected
# state DOWN - cable unplugged or interface disabled

# Bring interface up
ip link set eth0 up

# Check interface statistics
ip -s link show eth0
# RX errors, TX errors - bad cable or NIC
```

**Layer 2: Data Link Layer**

MAC addressing, frame transmission, switching.

```
Devices: Switches, Bridges, NICs
Data Unit: Frames
Protocols: Ethernet, ARP
Addressing: MAC addresses (48-bit, e.g., AA:BB:CC:DD:EE:FF)

Frame Structure:
┌──────────────┬──────────────┬──────┬──────────┬─────┐
│ Destination  │ Source       │ Type │ Data     │ CRC │
│ MAC (6 bytes)│ MAC (6 bytes)│(2 B) │(46-1500) │(4 B)│
└──────────────┴──────────────┴──────┴──────────┴─────┘
```

**Commands:**
```bash
# View MAC address
ip link show
# link/ether aa:bb:cc:dd:ee:ff

# View ARP cache (IP to MAC mapping)
ip neighbor show
# 192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE

# ARP table
arp -a
# gateway (192.168.1.1) at aa:bb:cc:dd:ee:ff [ether] on eth0

# Flush ARP cache
ip neighbor flush all

# View switch MAC table (if you have access to switch)
# show mac address-table
```

**Layer 3: Network Layer**

IP addressing, routing, packet forwarding.

```
Devices: Routers, Layer 3 Switches
Data Unit: Packets
Protocols: IPv4, IPv6, ICMP, OSPF, BGP
Addressing: IP addresses (IPv4: 32-bit, IPv6: 128-bit)

IPv4 Packet Header:
┌────────┬────────┬───────────┬────────────┬────────┐
│Version │ IHL    │ TOS       │ Total Len  │  ID    │
├────────┼────────┼───────────┼────────────┼────────┤
│ Flags  │ Fragment Offset    │ TTL        │Protocol│
├────────┴────────┴───────────┴────────────┴────────┤
│ Header Checksum                                    │
├────────────────────────────────────────────────────┤
│ Source IP Address                                  │
├────────────────────────────────────────────────────┤
│ Destination IP Address                             │
└────────────────────────────────────────────────────┘
```

**Commands:**
```bash
# View IP address
ip addr show
# inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0

# Add IP address
ip addr add 192.168.1.100/24 dev eth0

# View routing table
ip route show
# default via 192.168.1.1 dev eth0
# 192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100

# Add static route
ip route add 10.0.0.0/8 via 192.168.1.1

# Trace route
traceroute google.com
# Shows all hops (routers) between you and destination

# Ping (ICMP Echo Request/Reply)
ping -c 4 google.com

# MTU path discovery
tracepath google.com
```

**Layer 4: Transport Layer**

End-to-end communication, port numbers, reliability.

```
Data Unit: Segments (TCP) or Datagrams (UDP)
Protocols: TCP, UDP, SCTP
Addressing: Port numbers (0-65535)

TCP Header:
┌───────────────┬───────────────┬─────────────────┐
│ Source Port   │ Dest Port     │ Sequence Number │
├───────────────┴───────────────┼─────────────────┤
│ Acknowledgment Number         │ Flags | Window  │
├───────────────────────────────┼─────────────────┤
│ Checksum      │ Urgent Ptr    │ Options         │
└───────────────┴───────────────┴─────────────────┘

TCP Flags: SYN, ACK, FIN, RST, PSH, URG

UDP Header (simpler):
┌───────────────┬───────────────┬─────────┬─────────┐
│ Source Port   │ Dest Port     │ Length  │Checksum │
└───────────────┴───────────────┴─────────┴─────────┘
```

**TCP 3-Way Handshake:**
```
Client                          Server
  │                                │
  │──── SYN (seq=100) ──────────→ │  1. Client sends SYN
  │                                │
  │←─── SYN-ACK (seq=200, ───────│  2. Server responds SYN-ACK
  │      ack=101)                  │
  │                                │
  │──── ACK (ack=201) ──────────→ │  3. Client sends ACK
  │                                │
  │        Connection Established  │
```

**Commands:**
```bash
# View open ports and connections
netstat -tuln
# -t: TCP
# -u: UDP
# -l: listening
# -n: numeric (don't resolve names)

# Modern alternative
ss -tuln
# Much faster than netstat

# Show all TCP connections
ss -t -a

# Show processes using ports
ss -tulpn
# PID/Program name

# Alternative
lsof -i -P -n
# -i: network files
# -P: don't resolve port names
# -n: don't resolve hostnames

# Check if port is open
nc -zv google.com 80
# Connection to google.com 80 port [tcp/http] succeeded!

# Test TCP connection
telnet google.com 80
GET / HTTP/1.1
Host: google.com

# Test UDP
nc -u 8.8.8.8 53  # DNS query
```

**TCP vs UDP:**

| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Connection-oriented | Connectionless |
| Reliability | Guaranteed delivery | Best effort |
| Ordering | Ordered | Unordered |
| Speed | Slower | Faster |
| Overhead | Higher | Lower |
| Use Cases | HTTP, SSH, FTP | DNS, DHCP, Video Streaming |

**Layer 5-7: Application Layers**

```
Layer 7: Application Layer
- HTTP/HTTPS (Port 80/443)
- FTP (Port 21)
- SSH (Port 22)
- SMTP (Port 25)
- DNS (Port 53)
- DHCP (Port 67/68)

Layer 6: Presentation Layer
- SSL/TLS encryption
- Data compression
- Character encoding

Layer 5: Session Layer
- Session management
- Authentication
- Connection recovery
```

**Practical Troubleshooting Scenarios:**

**Scenario 1: Website Not Loading**

```bash
# Step 1: Check local network (Layer 1-2)
ip link show eth0
# state UP/DOWN?

# Step 2: Check IP configuration (Layer 3)
ip addr show eth0
# Have IP address?

# Step 3: Check gateway connectivity (Layer 3)
ping 192.168.1.1
# Can reach gateway?

# Step 4: Check DNS (Layer 7)
nslookup google.com
# DNS resolving?

# Step 5: Check internet connectivity (Layer 3)
ping 8.8.8.8
# Can reach internet?

# Step 6: Check application (Layer 7)
curl -I https://google.com
# HTTP response?

# Detailed layer-by-layer check
# Layer 1-2: Physical
ethtool eth0

# Layer 3: Network
ip route show
traceroute 8.8.8.8

# Layer 4: Transport
ss -tuln | grep :80

# Layer 7: Application
curl -v https://google.com
```

**Scenario 2: Slow Network Performance**

```bash
# Check bandwidth
iperf3 -s  # Server
iperf3 -c server_ip  # Client

# Check latency
ping -c 100 server_ip
# Look for:
# - Average latency
# - Packet loss %
# - Jitter (variation in latency)

# Check MTU
ip link show eth0 | grep mtu
# mtu 1500

# Test MTU path
ping -M do -s 1472 google.com
# -M do: Don't fragment
# -s 1472: Packet size (1500 - 28 byte header)

# Check for packet loss
mtr google.com
# Shows packet loss at each hop

# Check interface errors
ip -s link show eth0
# RX/TX errors, dropped packets

# Check TCP window size
ss -i
# Check for window scaling
```

**Scenario 3: Cannot Connect to Service**

```bash
# Check if service is listening
ss -tuln | grep :3000
# Should show LISTEN state

# Check firewall
iptables -L -n -v
# or
firewall-cmd --list-all

# Test from localhost
curl http://localhost:3000

# Test from same network
curl http://192.168.1.100:3000

# Test DNS resolution
dig service.example.com
nslookup service.example.com

# Check routing
ip route get 192.168.1.100

# Packet capture
tcpdump -i eth0 port 3000 -n
# Watch actual packets
```

**Common Ports:**

```bash
# Well-Known Ports (0-1023)
20, 21   - FTP
22       - SSH
23       - Telnet
25       - SMTP
53       - DNS
67, 68   - DHCP
80       - HTTP
110      - POP3
143      - IMAP
443      - HTTPS
3306     - MySQL
5432     - PostgreSQL
6379     - Redis
27017    - MongoDB

# Registered Ports (1024-49151)
3000     - Node.js default
5000     - Flask default
8080     - HTTP alternate
8443     - HTTPS alternate
9200     - Elasticsearch

# Dynamic Ports (49152-65535)
# Ephemeral ports for client connections
```

**Network Tools:**

```bash
# ping - Test connectivity
ping -c 4 8.8.8.8

# traceroute - Trace packet path
traceroute google.com

# mtr - Continuous traceroute
mtr google.com

# dig - DNS lookup
dig google.com
dig @8.8.8.8 google.com  # Use specific DNS server

# nslookup - DNS lookup
nslookup google.com

# curl - HTTP requests
curl -I https://google.com  # Headers only
curl -v https://google.com  # Verbose

# wget - Download files
wget https://example.com/file.tar.gz

# nc (netcat) - Network Swiss Army knife
nc -zv google.com 80  # Port scan
nc -l 8000  # Listen on port 8000

# nmap - Network scanner
nmap -p 1-1000 192.168.1.1  # Port scan
nmap -sP 192.168.1.0/24  # Host discovery

# tcpdump - Packet capture
tcpdump -i eth0 -n port 80
tcpdump -i any -w capture.pcap

# wireshark - GUI packet analyzer
wireshark

# iperf3 - Bandwidth testing
iperf3 -s  # Server
iperf3 -c server_ip  # Client

# ss - Socket statistics
ss -tuln  # All listening TCP/UDP
ss -t -a  # All TCP connections

# ip - Modern network config
ip addr show
ip route show
ip link show

# route - Routing table (deprecated)
route -n

# ifconfig - Interface config (deprecated)
ifconfig eth0
```

**Subnetting and CIDR:**

```bash
# CIDR Notation: IP/Prefix
192.168.1.0/24

# /24 = 255.255.255.0
# Network: 192.168.1.0
# Usable IPs: 192.168.1.1 - 192.168.1.254
# Broadcast: 192.168.1.255
# Total hosts: 256 (254 usable)

# Common Subnets:
/32 = 255.255.255.255  = 1 host
/30 = 255.255.255.252  = 4 hosts (2 usable)
/29 = 255.255.255.248  = 8 hosts (6 usable)
/28 = 255.255.255.240  = 16 hosts (14 usable)
/27 = 255.255.255.224  = 32 hosts (30 usable)
/26 = 255.255.255.192  = 64 hosts (62 usable)
/25 = 255.255.255.128  = 128 hosts (126 usable)
/24 = 255.255.255.0    = 256 hosts (254 usable)
/16 = 255.255.0.0      = 65,536 hosts
/8  = 255.0.0.0        = 16,777,216 hosts

# Calculate subnet
ipcalc 192.168.1.0/24
# Network: 192.168.1.0/24
# Netmask: 255.255.255.0
# Broadcast: 192.168.1.255
# HostMin: 192.168.1.1
# HostMax: 192.168.1.254
# Hosts/Net: 254
```

**NAT (Network Address Translation):**

```bash
# View NAT rules (iptables)
iptables -t nat -L -n -v

# SNAT (Source NAT) - Change source IP
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j SNAT --to-source 1.2.3.4

# MASQUERADE (Dynamic SNAT)
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE

# DNAT (Destination NAT) - Port forwarding
iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.1.100:8080
```

**DNS:**

```bash
# Forward lookup
dig google.com
# Returns A record (IP address)

# Reverse lookup
dig -x 8.8.8.8
# Returns PTR record (hostname)

# Specific record types
dig google.com A      # IPv4 address
dig google.com AAAA   # IPv6 address
dig google.com MX     # Mail servers
dig google.com NS     # Name servers
dig google.com TXT    # Text records
dig google.com CNAME  # Canonical name

# Trace DNS resolution
dig +trace google.com

# Check local DNS cache
systemd-resolve --status

# Flush DNS cache
systemd-resolve --flush-caches
# or
resolvectl flush-caches
```

**Load Balancing Algorithms:**

```
1. Round Robin
   Request 1 → Server A
   Request 2 → Server B
   Request 3 → Server C
   Request 4 → Server A (repeats)

2. Least Connections
   Choose server with fewest active connections

3. IP Hash
   Hash client IP to determine server
   Same client always goes to same server

4. Weighted Round Robin
   Server A: Weight 3
   Server B: Weight 2
   Server C: Weight 1
   A gets 3x more traffic than C
```

**Best Practices:**

1. **Use appropriate protocol**: TCP for reliability, UDP for speed
2. **Monitor network metrics**: Latency, packet loss, bandwidth
3. **Implement proper timeouts**: Connection, read, write timeouts
4. **Use keepalive**: Detect broken connections
5. **Enable compression**: Reduce bandwidth usage
6. **Use CDN**: Reduce latency for global users
7. **Implement rate limiting**: Prevent abuse
8. **Use private networks**: VPC for cloud resources
9. **Enable encryption**: TLS for data in transit
10. **Document network architecture**: IP ranges, VLANs, firewall rules

---

## Monitoring / Troubleshooting / SRE

### How do you approach production incident troubleshooting?

**Detailed Explanation:**

Effective incident response requires a systematic approach, proper tooling, and clear communication. This is a critical skill for SRE and DevOps engineers.

**Incident Response Framework:**

```
1. DETECT
   ↓
2. TRIAGE
   ↓
3. INVESTIGATE
   ↓
4. MITIGATE
   ↓
5. RESOLVE
   ↓
6. POST-MORTEM
```

**1. DETECT Phase:**

**Monitoring Stack:**

```
┌──────────────────────────────────────────────┐
│           Application/Infrastructure         │
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    ┌────▼────┐         ┌────▼────┐
    │ Metrics │         │  Logs   │
    │(Prometheus)       │(ELK/Loki)
    └────┬────┘         └────┬────┘
         │                   │
         └─────────┬─────────┘
                   │
            ┌──────▼──────┐
            │  Alerting   │
            │(AlertManager)
            └──────┬──────┘
                   │
         ┌─────────┴──────────┐
         │                    │
    ┌────▼────┐         ┌─────▼────┐
    │ PagerDuty│        │  Slack   │
    └──────────┘        └──────────┘
```

**Prometheus Alerting Rules:**

```yaml
# alerts.yml
groups:
  - name: application_alerts
    interval: 30s
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) /
          rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
          description: "Error rate is {{ $value | humanizePercentage }}"
          runbook: "https://wiki.company.com/runbooks/high-error-rate"

      # High Latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 1.0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.instance }}"
          description: "95th percentile latency is {{ $value }}s"

      # Service Down
      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.instance }} has been down for 2 minutes"

      # High CPU Usage
      - alert: HighCPU
        expr: |
          100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}%"

      # High Memory Usage
      - alert: HighMemory
        expr: |
          (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) /
          node_memory_MemTotal_bytes * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}%"

      # Disk Space Low
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} /
          node_filesystem_size_bytes{mountpoint="/"}) * 100 < 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Only {{ $value }}% disk space remaining"

      # Pod Crash Loop
      - alert: PodCrashLoop
        expr: |
          rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod {{ $labels.pod }} is crash looping"
          description: "Restart count: {{ $value }}"

      # SSL Certificate Expiring
      - alert: SSLCertExpiringSoon
        expr: |
          probe_ssl_earliest_cert_expiry - time() < 86400 * 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "SSL cert expiring soon for {{ $labels.instance }}"
          description: "Certificate expires in {{ $value | humanizeDuration }}"
```

**2. TRIAGE Phase:**

**Initial Assessment (First 2 Minutes):**

```bash
# Triage Checklist
1. Severity Level
   - P0 (Critical): Complete outage, data loss, security breach
   - P1 (High): Major feature broken, significant customer impact
   - P2 (Medium): Minor feature broken, limited customer impact
   - P3 (Low): Cosmetic issue, no customer impact

2. Customer Impact
   - How many users affected?
   - Which features affected?
   - Revenue impact?

3. Communication
   - Start incident channel (Slack)
   - Page on-call engineer
   - Notify stakeholders
   - Update status page
```

**Incident Commander Role:**

```bash
# Incident Commander Responsibilities:
1. Coordinate response team
2. Maintain communication
3. Make decisions
4. Delegate tasks
5. Track timeline
6. Manage stakeholders

# Communication Template
"[INCIDENT] P0 - API Service Down
Status: Investigating
Impact: All users unable to login
Started: 2026-02-24 14:30 UTC
Commander: @john
Engineers: @team-backend
Updates: Every 15 minutes"
```

**3. INVESTIGATE Phase:**

**The Four Golden Signals (Google SRE):**

```
1. LATENCY
   - How long does it take to serve requests?
   - Query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

2. TRAFFIC
   - How much demand is on the system?
   - Query: rate(http_requests_total[5m])

3. ERRORS
   - What is the error rate?
   - Query: rate(http_requests_total{status=~"5.."}[5m])

4. SATURATION
   - How "full" is the service?
   - CPU, Memory, Disk, Network utilization
```

**Systematic Troubleshooting Process:**

```bash
# Step 1: Gather Context
# What changed recently?
git log --since="1 hour ago" --oneline

# Recent deployments?
kubectl rollout history deployment/myapp -n production

# Infrastructure changes?
terraform show | grep "last_modified"

# Step 2: Check Application Logs
# Recent errors
kubectl logs deployment/myapp -n production --since=10m | grep ERROR

# Tail logs in real-time
kubectl logs -f deployment/myapp -n production

# All pods
kubectl logs -l app=myapp -n production --tail=100

# Previous pod (after crash)
kubectl logs myapp-pod-xyz --previous

# Step 3: Check Metrics
# Prometheus queries
# High error rate?
rate(http_requests_total{status=~"5.."}[5m])

# High latency?
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Resource usage?
container_memory_usage_bytes{pod=~"myapp.*"}
rate(container_cpu_usage_seconds_total{pod=~"myapp.*"}[5m])

# Step 4: Check Dependencies
# Database connections
SELECT count(*) FROM pg_stat_activity;

# Cache hit rate
redis-cli info stats | grep hit_rate

# External API status
curl https://status.external-api.com

# Step 5: Check Infrastructure
# Node health
kubectl get nodes

# Pod health
kubectl get pods -n production

# Events
kubectl get events -n production --sort-by='.lastTimestamp'

# Step 6: Check Network
# DNS resolution
nslookup api.example.com

# Connectivity
curl -I https://api.example.com

# Latency
ping api.example.com

# Port open?
nc -zv api.example.com 443
```

**Common Incident Patterns:**

**Pattern 1: Deployment Caused Issue**

```bash
# Symptoms
- Errors spiked after deployment
- New version has bugs

# Investigation
kubectl rollout history deployment/myapp -n production
git log --oneline -10
git diff HEAD~1 HEAD

# Mitigation
kubectl rollout undo deployment/myapp -n production

# Verification
kubectl rollout status deployment/myapp -n production
curl https://api.example.com/health
```

**Pattern 2: Database Connection Pool Exhausted**

```bash
# Symptoms
- "Too many connections" errors
- Slow response times
- Connection timeouts

# Investigation
# Check active connections
kubectl exec -it myapp-pod -- psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Check connection pool settings
kubectl exec -it myapp-pod -- env | grep DB_POOL

# Mitigation
# Increase connection pool size
kubectl set env deployment/myapp DB_POOL_SIZE=50 -n production

# Kill idle connections
kubectl exec -it postgres-pod -- psql -U postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"
```

**Pattern 3: Memory Leak**

```bash
# Symptoms
- Memory usage increasing over time
- OOMKilled pods
- Slow performance

# Investigation
# Check memory usage trend
kubectl top pods -n production | grep myapp

# Check OOM events
kubectl get events -n production | grep OOMKilled

# View detailed metrics
kubectl describe pod myapp-pod -n production

# Mitigation (Short-term)
# Restart pods
kubectl rollout restart deployment/myapp -n production

# Increase memory limit
kubectl set resources deployment/myapp \
  --limits=memory=2Gi -n production

# Long-term: Fix memory leak in code
# Profile application
# Run with: python -m memory_profiler script.py
```

**Pattern 4: Traffic Spike (DDoS or Viral Content)**

```bash
# Symptoms
- Sudden increase in traffic
- High CPU/memory usage
- Slow response times

# Investigation
# Check request rate
rate(http_requests_total[1m])

# Check source IPs
kubectl logs deployment/myapp -n production | \
  awk '{print $1}' | sort | uniq -c | sort -rn | head -20

# Mitigation
# Scale up
kubectl scale deployment/myapp --replicas=20 -n production

# Enable autoscaling
kubectl autoscale deployment/myapp \
  --min=5 --max=50 --cpu-percent=70 -n production

# Rate limiting (if attack)
# Enable WAF rules
# Block malicious IPs in security groups
```

**Pattern 5: External Dependency Down**

```bash
# Symptoms
- Timeouts connecting to external service
- Errors from third-party API

# Investigation
# Check external service status
curl https://status.external-service.com

# Check DNS
nslookup external-api.com

# Check network path
traceroute external-api.com

# Mitigation
# Enable circuit breaker
# Return cached data
# Degrade gracefully
# Switch to backup provider
```

**4. MITIGATE Phase:**

**Immediate Actions:**

```bash
# 1. Rollback deployment
kubectl rollout undo deployment/myapp -n production

# 2. Scale resources
kubectl scale deployment/myapp --replicas=10 -n production

# 3. Disable feature flag
curl -X POST https://launchdarkly.com/api/v2/flags/new-feature \
  -H "Authorization: $LD_API_KEY" \
  -d '{"on": false}'

# 4. Restart service
kubectl rollout restart deployment/myapp -n production

# 5. Clear cache
kubectl exec -it redis-pod -- redis-cli FLUSHALL

# 6. Failover to backup
# Switch DNS to backup region
# Or use Route53 health checks

# 7. Block malicious traffic
# Add WAF rule
aws wafv2 update-web-acl --scope REGIONAL \
  --id xxx --default-action Block={}
```

**5. RESOLVE Phase:**

```bash
# 1. Verify fix
# Check error rate
rate(http_requests_total{status=~"5.."}[5m])

# Check latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Check application logs
kubectl logs deployment/myapp -n production --tail=100

# 2. Monitor closely
# Watch metrics for 30 minutes
# Ensure issue doesn't recur

# 3. Update status page
"[RESOLVED] API Service Down
Issue: Database connection pool exhausted
Fix: Increased connection pool size
Duration: 45 minutes
Impact: ~30% of users experienced errors"

# 4. Close incident
# Mark incident as resolved in PagerDuty
# Thank team members
# Schedule post-mortem
```

**6. POST-MORTEM Phase:**

**Post-Mortem Template:**

```markdown
# Incident Post-Mortem

## Summary
Brief description of what happened

## Timeline (All times UTC)
- 14:30 - Alert fired: High error rate
- 14:32 - Incident commander assigned
- 14:35 - Root cause identified: DB connection pool exhausted
- 14:40 - Mitigation applied: Increased pool size
- 15:15 - Issue resolved
- 15:30 - Monitoring period complete

## Root Cause
Database connection pool size (default 10) was insufficient for
traffic volume after marketing campaign launch.

## Impact
- Duration: 45 minutes
- Users affected: ~10,000 (30% of active users)
- Requests failed: ~50,000
- Revenue impact: $5,000 estimated

## What Went Well
- Alert fired quickly (< 2 minutes)
- Team responded promptly
- Root cause identified quickly
- Mitigation was effective

## What Went Wrong
- No load testing before marketing campaign
- Connection pool size not tuned for expected traffic
- No runbook for this scenario
- Monitoring didn't show connection pool metrics

## Action Items
1. [ ] Add connection pool metrics to Grafana dashboard (@john, 2026-03-01)
2. [ ] Create runbook for DB connection issues (@jane, 2026-03-03)
3. [ ] Implement load testing in CI/CD pipeline (@team, 2026-03-10)
4. [ ] Review and tune all connection pool sizes (@team, 2026-03-05)
5. [ ] Add pre-deployment checklist for marketing campaigns (@sarah, 2026-03-01)
6. [ ] Set up synthetic monitoring for critical paths (@tom, 2026-03-07)

## Lessons Learned
- Always load test before traffic surges
- Monitor resource limits (connections, file descriptors, etc.)
- Document common issues in runbooks
- Coordinate with marketing for campaign launches
```

**SRE Metrics:**

```bash
# SLI (Service Level Indicator)
# Actual measurement of service performance

# Example SLIs:
- Request success rate: 99.5%
- Request latency P95: 200ms
- Request latency P99: 500ms
- System uptime: 99.9%

# SLO (Service Level Objective)
# Target value for SLI

# Example SLOs:
- 99.9% of requests succeed
- 95% of requests complete in < 200ms
- System available 99.95% of time

# SLA (Service Level Agreement)
# Contract with customers about service levels
# Includes penalties if SLOs not met

# Error Budget
# Amount of downtime allowed within SLO
# 99.9% uptime = 43.8 minutes downtime/month allowed

# Calculate error budget
Total requests: 1,000,000
SLO: 99.9% success
Error budget: 1,000 failed requests allowed

If error budget exhausted:
- Stop new features
- Focus on reliability
- No risky deployments
```

**Monitoring Best Practices:**

1. **Use the RED method** (Request rate, Error rate, Duration)
2. **Implement the USE method** (Utilization, Saturation, Errors)
3. **Set up alerting on symptoms, not causes**
4. **Alert on what matters**: Page only for actionable issues
5. **Document runbooks**: Step-by-step resolution guides
6. **Automate common fixes**: Self-healing systems
7. **Practice incident response**: GameDays, chaos engineering
8. **Review incidents**: Blameless post-mortems
9. **Track MTTR**: Mean Time To Recovery
10. **Improve observability**: Structured logging, distributed tracing

---

## Python / Automation / API

### How do you write production-ready Python code for automation?

**Detailed Explanation:**

Production Python automation requires proper error handling, logging, configuration management, testing, and operational best practices.

**1. Project Structure:**

```
automation-project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── decorators.py
│   └── modules/
│       ├── __init__.py
│       ├── aws_handler.py
│       └── k8s_handler.py
├── tests/
│   ├── __init__.py
│   ├── test_aws_handler.py
│   └── test_k8s_handler.py
├── scripts/
│   └── deploy.sh
├── config/
│   ├── dev.yaml
│   ├── staging.yaml
│   └── production.yaml
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

**2. Configuration Management:**

**config/settings.py:**
```python
import os
from typing import Optional
from pydantic import BaseSettings, Field, validator

class Settings(BaseSettings):
    """Application settings with validation."""

    # Application
    app_name: str = "automation-service"
    environment: str = Field(default="development", env="ENV")
    debug: bool = Field(default=False, env="DEBUG")

    # AWS
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_profile: Optional[str] = Field(default=None, env="AWS_PROFILE")
    s3_bucket: str = Field(..., env="S3_BUCKET")  # Required

    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")

    # API
    api_key: str = Field(..., env="API_KEY")
    api_timeout: int = Field(default=30, env="API_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Initialize settings
settings = Settings()
```

**3. Logging:**

**utils/logging.py:**
```python
import logging
import json
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger
from typing import Any, Dict

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add custom fields
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        # Add extra context
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure application logging."""

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Silence noisy loggers
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Usage
from config.settings import settings
setup_logging(settings.log_level, settings.log_format)

logger = logging.getLogger(__name__)

# Log with context
logger.info("User logged in", extra={"user_id": 123, "request_id": "abc-123"})
```

**4. Error Handling and Retries:**

**utils/decorators.py:**
```python
import time
import functools
import logging
from typing import Callable, Type, Tuple, Any
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

def retry(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    max_delay: float = 60.0,
) -> Callable:
    """
    Retry decorator with exponential backoff.

    Args:
        exceptions: Tuple of exceptions to catch
        tries: Number of attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay (exponential backoff)
        max_delay: Maximum delay between retries

    Example:
        @retry(exceptions=(RequestException,), tries=3, delay=1, backoff=2)
        def fetch_data():
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _tries, _delay = tries, delay

            for attempt in range(_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == _tries - 1:
                        logger.error(
                            f"{func.__name__} failed after {_tries} attempts",
                            exc_info=True
                        )
                        raise

                    wait_time = min(_delay, max_delay)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{_tries}). "
                        f"Retrying in {wait_time}s...",
                        extra={"exception": str(e)}
                    )
                    time.sleep(wait_time)
                    _delay *= backoff

        return wrapper

    return decorator

def timeout(seconds: int) -> Callable:
    """
    Timeout decorator.

    Example:
        @timeout(30)
        def long_running_task():
            # Task that might take too long
            pass
    """
    import signal

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            def timeout_handler(signum, frame):
                raise TimeoutError(f"{func.__name__} timed out after {seconds}s")

            # Set alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)

            try:
                result = func(*args, **kwargs)
            finally:
                # Restore old handler and cancel alarm
                signal.signal(signal.SIGALRM, old_handler)
                signal.alarm(0)

            return result

        return wrapper

    return decorator

def log_execution_time(func: Callable) -> Callable:
    """Log function execution time."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logger.info(
                f"{func.__name__} executed",
                extra={"execution_time": f"{execution_time:.2f}s"}
            )

    return wrapper
```

**5. AWS Automation Example:**

**modules/aws_handler.py:**
```python
import boto3
import logging
from typing import List, Dict, Optional
from botocore.exceptions import ClientError, BotoCoreError
from config.settings import settings
from utils.decorators import retry, log_execution_time

logger = logging.getLogger(__name__)

class AWSHandler:
    """AWS operations handler."""

    def __init__(self):
        self.session = boto3.Session(
            region_name=settings.aws_region,
            profile_name=settings.aws_profile
        )
        self.ec2 = self.session.client("ec2")
        self.s3 = self.session.client("s3")
        self.rds = self.session.client("rds")

    @retry(exceptions=(ClientError, BotoCoreError), tries=3, delay=1, backoff=2)
    @log_execution_time
    def list_ec2_instances(
        self,
        filters: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        List EC2 instances with optional filters.

        Args:
            filters: List of filters (e.g., [{"Name": "tag:Environment", "Values": ["production"]}])

        Returns:
            List of instance dictionaries

        Raises:
            ClientError: If AWS API call fails
        """
        try:
            kwargs = {}
            if filters:
                kwargs["Filters"] = filters

            response = self.ec2.describe_instances(**kwargs)

            instances = []
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instances.append({
                        "id": instance["InstanceId"],
                        "type": instance["InstanceType"],
                        "state": instance["State"]["Name"],
                        "private_ip": instance.get("PrivateIpAddress"),
                        "public_ip": instance.get("PublicIpAddress"),
                        "tags": {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
                    })

            logger.info(f"Found {len(instances)} EC2 instances")
            return instances

        except ClientError as e:
            logger.error(f"Failed to list EC2 instances: {e}", exc_info=True)
            raise

    @retry(exceptions=(ClientError,), tries=3)
    @log_execution_time
    def stop_ec2_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """
        Stop EC2 instances.

        Args:
            instance_ids: List of instance IDs to stop

        Returns:
            Dictionary with stopping instances info

        Raises:
            ClientError: If stop operation fails
        """
        if not instance_ids:
            logger.warning("No instance IDs provided")
            return {"StoppingInstances": []}

        try:
            logger.info(f"Stopping {len(instance_ids)} instances")
            response = self.ec2.stop_instances(InstanceIds=instance_ids)

            logger.info(f"Successfully stopped {len(instance_ids)} instances")
            return response

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidInstanceID.NotFound":
                logger.error(f"Some instances not found: {instance_ids}")
            else:
                logger.error(f"Failed to stop instances: {e}", exc_info=True)
            raise

    @retry(exceptions=(ClientError,), tries=3)
    @log_execution_time
    def create_snapshot(
        self,
        volume_id: str,
        description: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create EBS snapshot.

        Args:
            volume_id: EBS volume ID
            description: Snapshot description
            tags: Optional tags for snapshot

        Returns:
            Snapshot ID

        Raises:
            ClientError: If snapshot creation fails
        """
        try:
            logger.info(f"Creating snapshot for volume {volume_id}")

            response = self.ec2.create_snapshot(
                VolumeId=volume_id,
                Description=description
            )

            snapshot_id = response["SnapshotId"]

            # Add tags
            if tags:
                self.ec2.create_tags(
                    Resources=[snapshot_id],
                    Tags=[{"Key": k, "Value": v} for k, v in tags.items()]
                )

            logger.info(f"Created snapshot {snapshot_id} for volume {volume_id}")
            return snapshot_id

        except ClientError as e:
            logger.error(f"Failed to create snapshot: {e}", exc_info=True)
            raise

    @retry(exceptions=(ClientError,), tries=3)
    @log_execution_time
    def upload_to_s3(
        self,
        file_path: str,
        bucket: str,
        key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload file to S3.

        Args:
            file_path: Local file path
            bucket: S3 bucket name
            key: S3 object key
            metadata: Optional metadata

        Returns:
            S3 URI

        Raises:
            ClientError: If upload fails
        """
        try:
            logger.info(f"Uploading {file_path} to s3://{bucket}/{key}")

            extra_args = {}
            if metadata:
                extra_args["Metadata"] = metadata

            self.s3.upload_file(
                Filename=file_path,
                Bucket=bucket,
                Key=key,
                ExtraArgs=extra_args
            )

            s3_uri = f"s3://{bucket}/{key}"
            logger.info(f"Successfully uploaded to {s3_uri}")
            return s3_uri

        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}", exc_info=True)
            raise
```

**6. Main Application:**

**main.py:**
```python
import argparse
import logging
import sys
from typing import Optional
from config.settings import settings
from utils.logging import setup_logging
from modules.aws_handler import AWSHandler

# Setup logging
setup_logging(settings.log_level, settings.log_format)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AWS Automation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--action",
        required=True,
        choices=["list-instances", "stop-instances", "create-snapshot"],
        help="Action to perform"
    )

    parser.add_argument(
        "--instance-ids",
        nargs="+",
        help="Instance IDs (for stop-instances)"
    )

    parser.add_argument(
        "--volume-id",
        help="Volume ID (for create-snapshot)"
    )

    parser.add_argument(
        "--environment",
        help="Filter by environment tag"
    )

    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()

    logger.info(
        f"Starting automation tool",
        extra={
            "action": args.action,
            "environment": settings.environment
        }
    )

    try:
        aws = AWSHandler()

        if args.action == "list-instances":
            filters = []
            if args.environment:
                filters.append({
                    "Name": "tag:Environment",
                    "Values": [args.environment]
                })

            instances = aws.list_ec2_instances(filters=filters)

            print(f"\nFound {len(instances)} instances:")
            for inst in instances:
                print(f"  - {inst['id']}: {inst['state']} ({inst['type']})")

        elif args.action == "stop-instances":
            if not args.instance_ids:
                logger.error("--instance-ids required for stop-instances")
                sys.exit(1)

            result = aws.stop_ec2_instances(args.instance_ids)
            print(f"\nStopping {len(result['StoppingInstances'])} instances")

        elif args.action == "create-snapshot":
            if not args.volume_id:
                logger.error("--volume-id required for create-snapshot")
                sys.exit(1)

            snapshot_id = aws.create_snapshot(
                volume_id=args.volume_id,
                description=f"Automated snapshot - {settings.environment}",
                tags={
                    "Environment": settings.environment,
                    "CreatedBy": "automation-tool"
                }
            )
            print(f"\nCreated snapshot: {snapshot_id}")

        logger.info("Automation completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Automation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**7. Unit Tests:**

**tests/test_aws_handler.py:**
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from modules.aws_handler import AWSHandler

@pytest.fixture
def aws_handler():
    """Create AWSHandler instance for testing."""
    with patch("modules.aws_handler.boto3.Session"):
        handler = AWSHandler()
        handler.ec2 = Mock()
        handler.s3 = Mock()
        return handler

def test_list_ec2_instances_success(aws_handler):
    """Test successful EC2 instance listing."""
    # Mock response
    aws_handler.ec2.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-12345",
                        "InstanceType": "t3.micro",
                        "State": {"Name": "running"},
                        "PrivateIpAddress": "10.0.1.10",
                        "Tags": [
                            {"Key": "Name", "Value": "web-server"},
                            {"Key": "Environment", "Value": "production"}
                        ]
                    }
                ]
            }
        ]
    }

    # Call method
    instances = aws_handler.list_ec2_instances()

    # Assertions
    assert len(instances) == 1
    assert instances[0]["id"] == "i-12345"
    assert instances[0]["state"] == "running"
    assert instances[0]["tags"]["Environment"] == "production"

def test_list_ec2_instances_error(aws_handler):
    """Test EC2 instance listing with error."""
    # Mock error
    aws_handler.ec2.describe_instances.side_effect = ClientError(
        {"Error": {"Code": "UnauthorizedOperation", "Message": "Not authorized"}},
        "DescribeInstances"
    )

    # Should raise after retries
    with pytest.raises(ClientError):
        aws_handler.list_ec2_instances()

def test_stop_ec2_instances_success(aws_handler):
    """Test successful EC2 instance stop."""
    # Mock response
    aws_handler.ec2.stop_instances.return_value = {
        "StoppingInstances": [
            {"InstanceId": "i-12345", "CurrentState": {"Name": "stopping"}}
        ]
    }

    # Call method
    result = aws_handler.stop_ec2_instances(["i-12345"])

    # Assertions
    assert len(result["StoppingInstances"]) == 1
    aws_handler.ec2.stop_instances.assert_called_once_with(InstanceIds=["i-12345"])

def test_stop_ec2_instances_empty_list(aws_handler):
    """Test stopping with empty instance list."""
    result = aws_handler.stop_ec2_instances([])
    assert result["StoppingInstances"] == []
    aws_handler.ec2.stop_instances.assert_not_called()
```

**8. Requirements:**

**requirements.txt:**
```
boto3==1.28.0
botocore==1.31.0
pydantic==2.4.0
pydantic-settings==2.0.3
python-json-logger==2.0.7
requests==2.31.0
python-dotenv==1.0.0
```

**requirements-dev.txt:**
```
-r requirements.txt
pytest==7.4.2
pytest-cov==4.1.0
pytest-mock==3.11.1
black==23.9.1
flake8==6.1.0
mypy==1.5.1
isort==5.12.0
```

**Best Practices:**

1. **Use type hints**: Helps with IDE autocomplete and catches errors
2. **Structured logging**: JSON format for easy parsing
3. **Configuration management**: Environment-specific settings
4. **Error handling**: Retry logic with exponential backoff
5. **Testing**: Unit tests with mocking
6. **Code quality**: Black, flake8, isort, mypy
7. **Documentation**: Docstrings for all functions
8. **CLI interface**: argparse for user-friendly commands
9. **Graceful degradation**: Handle partial failures
10. **Monitoring**: Integrate with observability tools

---


## SQL / Database Design

### Explain database normalization and when to denormalize.

**Detailed Explanation:**

Normalization organizes data to minimize redundancy and dependency. Understanding when to normalize vs denormalize is crucial for database performance.

**Normal Forms:**

**1NF (First Normal Form):**
- Each column contains atomic (indivisible) values
- Each column contains values of a single type
- Each column has a unique name
- The order doesn't matter

**Bad (Not 1NF):**
```sql
CREATE TABLE employees (
    id INT,
    name VARCHAR(100),
    phone_numbers VARCHAR(200)  -- "555-1234, 555-5678" - Multiple values!
);
```

**Good (1NF):**
```sql
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE employee_phones (
    id INT PRIMARY KEY,
    employee_id INT,
    phone_number VARCHAR(20),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

**2NF (Second Normal Form):**
- Must be in 1NF
- All non-key attributes must depend on the entire primary key (for composite keys)

**Bad (Not 2NF):**
```sql
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT,
    product_name VARCHAR(100),  -- Depends only on product_id, not full key!
    product_price DECIMAL(10,2), -- Depends only on product_id, not full key!
    PRIMARY KEY (order_id, product_id)
);
```

**Good (2NF):**
```sql
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2)
);

CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**3NF (Third Normal Form):**
- Must be in 2NF
- No transitive dependencies (non-key attributes shouldn't depend on other non-key attributes)

**Bad (Not 3NF):**
```sql
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    department_id INT,
    department_name VARCHAR(100),  -- Depends on department_id, not employee id!
    department_location VARCHAR(100) -- Depends on department_id!
);
```

**Good (3NF):**
```sql
CREATE TABLE departments (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    location VARCHAR(100)
);

CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);
```

**Complete Normalized Schema Example:**

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Addresses table (one-to-many with users)
CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),
    is_primary BOOLEAN DEFAULT false,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    parent_category_id INT,
    FOREIGN KEY (parent_category_id) REFERENCES categories(id)
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(10,2) NOT NULL,
    shipping_address_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (shipping_address_id) REFERENCES addresses(id)
);

-- Order items (many-to-many between orders and products)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,  -- Price at time of order
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_products_category_id ON products(category_id);
```

**When to Denormalize:**

Denormalization intentionally introduces redundancy for performance.

**Reasons to Denormalize:**

1. **Read Performance**: Reduce JOINs for frequently accessed data
2. **Aggregation**: Pre-calculate expensive aggregations
3. **Reporting**: Optimize for analytics queries
4. **Caching**: Store computed values

**Denormalization Example:**

```sql
-- Normalized: Requires JOIN for every order query
SELECT o.*, u.email, u.username
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.id = 12345;

-- Denormalized: Add user info to orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    user_email VARCHAR(255),  -- Denormalized!
    user_name VARCHAR(100),   -- Denormalized!
    status VARCHAR(50),
    total_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Now no JOIN needed
SELECT * FROM orders WHERE id = 12345;

-- Trade-off: Must update orders when user email/name changes
UPDATE orders SET user_email = 'new@email.com' WHERE user_id = 123;
```

**Common Denormalization Patterns:**

**1. Materialized Views:**
```sql
-- Expensive query: calculate order totals
SELECT
    o.id,
    o.created_at,
    SUM(oi.quantity * oi.unit_price) as total
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.created_at;

-- Create materialized view
CREATE MATERIALIZED VIEW order_totals AS
SELECT
    o.id,
    o.created_at,
    SUM(oi.quantity * oi.unit_price) as total
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.created_at;

-- Refresh periodically
REFRESH MATERIALIZED VIEW order_totals;

-- Query is now fast
SELECT * FROM order_totals WHERE id = 12345;
```

**2. Aggregate Columns:**
```sql
-- Add aggregate column to avoid repeated calculations
ALTER TABLE products ADD COLUMN total_sales INT DEFAULT 0;
ALTER TABLE products ADD COLUMN total_revenue DECIMAL(10,2) DEFAULT 0;

-- Update with trigger
CREATE OR REPLACE FUNCTION update_product_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET
        total_sales = total_sales + NEW.quantity,
        total_revenue = total_revenue + (NEW.quantity * NEW.unit_price)
    WHERE id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER product_stats_trigger
AFTER INSERT ON order_items
FOR EACH ROW
EXECUTE FUNCTION update_product_stats();

-- Now query is simple
SELECT name, total_sales, total_revenue
FROM products
ORDER BY total_revenue DESC
LIMIT 10;
```

**3. Cache Tables:**
```sql
-- Daily sales summary (expensive to calculate)
CREATE TABLE daily_sales_summary (
    date DATE PRIMARY KEY,
    total_orders INT,
    total_revenue DECIMAL(10,2),
    average_order_value DECIMAL(10,2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate with scheduled job
INSERT INTO daily_sales_summary (date, total_orders, total_revenue, average_order_value)
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as average_order_value
FROM orders
WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
GROUP BY DATE(created_at)
ON CONFLICT (date) DO UPDATE SET
    total_orders = EXCLUDED.total_orders,
    total_revenue = EXCLUDED.total_revenue,
    average_order_value = EXCLUDED.average_order_value,
    calculated_at = CURRENT_TIMESTAMP;
```

**Query Optimization:**

```sql
-- EXPLAIN ANALYZE shows query execution plan
EXPLAIN ANALYZE
SELECT u.username, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username
ORDER BY order_count DESC
LIMIT 10;

-- Output shows:
-- - Execution time
-- - Rows processed
-- - Index usage
-- - Join method (Nested Loop, Hash Join, Merge Join)

-- Common optimizations:

-- 1. Add indexes
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- 2. Use EXPLAIN to verify index usage
EXPLAIN SELECT * FROM orders WHERE user_id = 123;
-- Should show "Index Scan" not "Seq Scan"

-- 3. Avoid SELECT *
SELECT id, username FROM users;  -- Better
SELECT * FROM users;              -- Wasteful

-- 4. Use LIMIT for large result sets
SELECT * FROM orders ORDER BY created_at DESC LIMIT 100;

-- 5. Use EXISTS instead of COUNT for existence checks
-- Bad
SELECT * FROM users WHERE (SELECT COUNT(*) FROM orders WHERE user_id = users.id) > 0;

-- Good
SELECT * FROM users WHERE EXISTS (SELECT 1 FROM orders WHERE user_id = users.id);

-- 6. Batch operations
-- Bad: N+1 queries
for user_id in user_ids:
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

-- Good: Single query
cursor.execute("SELECT * FROM users WHERE id = ANY(%s)", (user_ids,))
```

**Database Indexing:**

```sql
-- B-Tree index (default, most common)
CREATE INDEX idx_users_email ON users(email);

-- Partial index (only index subset of rows)
CREATE INDEX idx_active_users ON users(email) WHERE active = true;

-- Composite index (multiple columns)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
-- Useful for: WHERE user_id = X AND status = Y
-- Also useful for: WHERE user_id = X (uses first column)

-- Unique index
CREATE UNIQUE INDEX idx_unique_email ON users(email);

-- Full-text search index
CREATE INDEX idx_products_search ON products USING gin(to_tsvector('english', name || ' ' || description));

-- Query with full-text search
SELECT * FROM products
WHERE to_tsvector('english', name || ' ' || description) @@ to_tsquery('laptop');

-- JSONB index
CREATE INDEX idx_metadata ON products USING gin(metadata);

-- Query JSONB
SELECT * FROM products WHERE metadata @> '{"color": "red"}';

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

**Transactions and ACID:**

```sql
-- Transaction example
BEGIN;

-- Deduct from account
UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

-- Add to account
UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

-- Check if successful
SELECT balance FROM accounts WHERE id = 1;

-- Commit or rollback
COMMIT;
-- or
ROLLBACK;

-- Transaction isolation levels
-- READ UNCOMMITTED - Dirty reads possible
-- READ COMMITTED - Default in PostgreSQL
-- REPEATABLE READ - Prevents non-repeatable reads
-- SERIALIZABLE - Fully isolated

-- Set isolation level
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

**Database Best Practices:**

1. **Use appropriate data types**: INT vs BIGINT, VARCHAR vs TEXT
2. **Add indexes on foreign keys**: Improves JOIN performance
3. **Use constraints**: PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK
4. **Normalize for OLTP**: Optimize for transactions
5. **Denormalize for OLAP**: Optimize for analytics
6. **Use connection pooling**: Reduce connection overhead
7. **Monitor slow queries**: Use pg_stat_statements
8. **Regular VACUUM**: Prevent bloat in PostgreSQL
9. **Backup regularly**: Automated backups to S3
10. **Use read replicas**: Scale read operations

---

## JavaScript / Promises

### Explain JavaScript Promises and async/await.

**Detailed Explanation:**

Promises are a way to handle asynchronous operations in JavaScript. Understanding them is crucial for modern JavaScript development.

**Callback Hell (The Problem):**

```javascript
// Nested callbacks - hard to read and maintain
getUser(userId, function(user) {
    getOrders(user.id, function(orders) {
        getOrderDetails(orders[0].id, function(details) {
            getShippingInfo(details.shippingId, function(shipping) {
                console.log(shipping);
            });
        });
    });
});
```

**Promises (The Solution):**

```javascript
// Promise states:
// - Pending: Initial state
// - Fulfilled: Operation completed successfully
// - Rejected: Operation failed

// Creating a promise
const promise = new Promise((resolve, reject) => {
    // Asynchronous operation
    setTimeout(() => {
        const success = true;
        if (success) {
            resolve("Operation successful!");
        } else {
            reject("Operation failed!");
        }
    }, 1000);
});

// Using a promise
promise
    .then(result => {
        console.log(result); // "Operation successful!"
        return result.toUpperCase();
    })
    .then(upperResult => {
        console.log(upperResult); // "OPERATION SUCCESSFUL!"
    })
    .catch(error => {
        console.error(error);
    })
    .finally(() => {
        console.log("Cleanup");
    });
```

**Promise Chaining:**

```javascript
// Much better than callback hell
getUser(userId)
    .then(user => getOrders(user.id))
    .then(orders => getOrderDetails(orders[0].id))
    .then(details => getShippingInfo(details.shippingId))
    .then(shipping => console.log(shipping))
    .catch(error => console.error(error));
```

**Async/Await (Syntactic Sugar):**

```javascript
// Even cleaner syntax
async function getUserShippingInfo(userId) {
    try {
        const user = await getUser(userId);
        const orders = await getOrders(user.id);
        const details = await getOrderDetails(orders[0].id);
        const shipping = await getShippingInfo(details.shippingId);
        console.log(shipping);
    } catch (error) {
        console.error(error);
    }
}

// Call async function
getUserShippingInfo(123);
```

**Parallel Execution:**

```javascript
// Sequential (slow) - 3 seconds total
async function sequential() {
    const user1 = await getUser(1);    // 1 second
    const user2 = await getUser(2);    // 1 second
    const user3 = await getUser(3);    // 1 second
    return [user1, user2, user3];
}

// Parallel (fast) - 1 second total
async function parallel() {
    const [user1, user2, user3] = await Promise.all([
        getUser(1),    // All execute simultaneously
        getUser(2),
        getUser(3)
    ]);
    return [user1, user2, user3];
}

// Promise.all - Waits for all, fails if any fails
Promise.all([promise1, promise2, promise3])
    .then(results => console.log(results))
    .catch(error => console.error(error));

// Promise.allSettled - Waits for all, never fails
Promise.allSettled([promise1, promise2, promise3])
    .then(results => {
        results.forEach(result => {
            if (result.status === 'fulfilled') {
                console.log('Success:', result.value);
            } else {
                console.log('Failed:', result.reason);
            }
        });
    });

// Promise.race - Returns first to complete
Promise.race([promise1, promise2, promise3])
    .then(result => console.log('First:', result))
    .catch(error => console.error('First error:', error));

// Promise.any - Returns first to succeed, fails if all fail
Promise.any([promise1, promise2, promise3])
    .then(result => console.log('First success:', result))
    .catch(error => console.error('All failed:', error));
```

**Real-World Examples:**

**1. API Calls:**
```javascript
// Fetch user data from API
async function fetchUserData(userId) {
    try {
        const response = await fetch(`https://api.example.com/users/${userId}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const userData = await response.json();
        return userData;
    } catch (error) {
        console.error('Error fetching user:', error);
        throw error;
    }
}

// Usage
fetchUserData(123)
    .then(user => console.log(user))
    .catch(error => console.error(error));
```

**2. Multiple API Calls:**
```javascript
async function getDashboardData(userId) {
    try {
        // Fetch all data in parallel
        const [user, orders, notifications, stats] = await Promise.all([
            fetch(`/api/users/${userId}`).then(r => r.json()),
            fetch(`/api/orders?userId=${userId}`).then(r => r.json()),
            fetch(`/api/notifications?userId=${userId}`).then(r => r.json()),
            fetch(`/api/stats?userId=${userId}`).then(r => r.json())
        ]);

        return { user, orders, notifications, stats };
    } catch (error) {
        console.error('Error loading dashboard:', error);
        throw error;
    }
}
```

**3. Retry Logic:**
```javascript
async function fetchWithRetry(url, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                return await response.json();
            }
            throw new Error(`HTTP ${response.status}`);
        } catch (error) {
            if (i === maxRetries - 1) {
                throw error;
            }
            console.log(`Retry ${i + 1}/${maxRetries}`);
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}
```

**4. Timeout:**
```javascript
function timeout(promise, ms) {
    return Promise.race([
        promise,
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Timeout')), ms)
        )
    ]);
}

// Usage
try {
    const result = await timeout(
        fetch('https://api.example.com/slow'),
        5000  // 5 second timeout
    );
    console.log(result);
} catch (error) {
    console.error('Request timed out:', error);
}
```

---

## System Design / Architecture

### How do you design a scalable and resilient distributed system?

**Key Principles:**

**1. Scalability:**
- **Horizontal scaling**: Add more servers (preferred)
- **Vertical scaling**: Add more resources to single server (limited)

**2. High Availability:**
- No single points of failure
- Multi-region deployment
- Auto-failover

**3. Resilience:**
- Circuit breakers
- Retries with exponential backoff
- Graceful degradation
- Chaos engineering

**4. Observability:**
- Metrics, logs, traces
- Distributed tracing
- Health checks

**5. Security:**
- Encryption in transit and at rest
- Least privilege access
- Network segmentation
- DDoS protection

**System Design Approach:**

```
1. Requirements Gathering
   - Functional requirements
   - Non-functional requirements (scale, performance, SLAs)

2. Capacity Planning
   - Users: 10 million
   - Requests: 10,000 QPS
   - Data: 1 TB
   - Growth: 20% per year

3. High-Level Design
   - Components
   - Data flow
   - APIs

4. Deep Dive
   - Database schema
   - Caching strategy
   - Load balancing
   - Failure scenarios

5. Bottlenecks and Trade-offs
   - CAP theorem
   - Consistency vs availability
   - Cost optimization
```

**Example: URL Shortener (like bit.ly)**

**Requirements:**
- Shorten long URLs
- Redirect short URLs to original
- 100M URLs per month
- Low latency (<100ms)
- High availability (99.9%)

**Design:**

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  CDN/CloudFront │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Load Balancer │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────┐
│ App  │  │ App  │
│Server│  │Server│
└───┬──┘  └───┬──┘
    │         │
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌────────┐
│Redis │  │Database│
│Cache │  │(Sharded)│
└──────┘  └────────┘
```

**More topics covered in original file sections...**

---

## Security

### Explain key security practices for DevOps/Cloud environments.

**1. Identity and Access Management (IAM):**

```bash
# Principle of least privilege
# Bad: Admin access for everyone
{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
}

# Good: Specific permissions
{
    "Effect": "Allow",
    "Action": [
        "s3:GetObject",
        "s3:PutObject"
    ],
    "Resource": "arn:aws:s3:::my-bucket/*"
}

# Use IAM roles, not access keys
# Enable MFA
# Rotate credentials regularly
# Use temporary credentials (STS)
```

**2. Network Security:**

```bash
# Security groups (stateful firewall)
# Allow only necessary ports
# Use private subnets for databases
# Implement WAF for web apps
# Use VPN or AWS PrivateLink for admin access
```

**3. Encryption:**

```bash
# Encrypt data at rest (S3, EBS, RDS)
# Encrypt data in transit (TLS/HTTPS)
# Use AWS KMS for key management
# Rotate encryption keys
```

**4. Secrets Management:**

```bash
# Never hardcode secrets
# Use AWS Secrets Manager or HashiCorp Vault
# Inject secrets at runtime
# Audit secret access
```

**5. Container Security:**

```bash
# Scan images for vulnerabilities
docker scan myimage:latest

# Run as non-root user
USER 1001

# Use minimal base images
FROM alpine

# Sign and verify images
docker trust sign myimage:v1
```

**6. Compliance and Auditing:**

```bash
# Enable CloudTrail (audit logs)
# Enable AWS Config (compliance)
# Use AWS Security Hub
# Regular security audits
# Automated compliance checks
```

---

## GCP

### Key GCP Services:

- **Compute Engine**: VMs (like EC2)
- **GKE**: Google Kubernetes Engine
- **Cloud Storage**: Object storage (like S3)
- **Cloud SQL**: Managed databases
- **BigQuery**: Data warehouse
- **Cloud Functions**: Serverless (like Lambda)
- **Cloud Pub/Sub**: Messaging (like SNS/SQS)
- **Cloud Run**: Containerized apps

**Similar concepts to AWS but with different names and some unique features.**

---

## Git / Deployment

### Git Best Practices:

```bash
# Branching strategy
main/master    # Production
develop        # Development
feature/*      # Features
hotfix/*       # Emergency fixes
release/*      # Release candidates

# Commit messages
feat: Add user authentication
fix: Fix memory leak in cache
docs: Update API documentation
refactor: Simplify database queries
test: Add unit tests for auth

# Workflow
git checkout -b feature/user-auth
# Make changes
git add .
git commit -m "feat: Add user authentication"
git push origin feature/user-auth
# Create pull request
# Code review
# Merge to develop
# Deploy
```

---

## Java Concurrency

### Key Concepts:

- **Threads**: Concurrent execution
- **Synchronization**: Prevent race conditions
- **Locks**: ReentrantLock, ReadWriteLock
- **Executors**: Thread pools
- **CompletableFuture**: Async programming
- **Atomic variables**: Lock-free updates
- **volatile keyword**: Visibility guarantee

---

## DSA / Algorithmic Problems

### Common Patterns:

1. **Two Pointers**: Array problems
2. **Sliding Window**: Substring problems
3. **Binary Search**: Sorted arrays
4. **DFS/BFS**: Graph traversal
5. **Dynamic Programming**: Optimization
6. **Hash Maps**: Fast lookups
7. **Heaps**: Top K elements
8. **Trie**: Prefix matching

---

## Deployment / Hosting

### Deployment Strategies:

**1. Blue-Green Deployment:**
- Two identical environments
- Switch traffic instantly
- Easy rollback

**2. Canary Deployment:**
- Gradual rollout (10% → 50% → 100%)
- Monitor metrics
- Rollback if issues

**3. Rolling Deployment:**
- Update instances one by one
- No downtime
- Gradual migration

**4. Feature Flags:**
- Deploy code but keep features disabled
- Enable for specific users/% of traffic
- Quick disable if issues

---

## Conclusion

This comprehensive guide covers all major DevOps/Cloud/SRE interview topics with:

- Detailed explanations
- Real-world examples
- Code samples
- Best practices
- Troubleshooting tips
- Production-ready patterns

**Key Takeaways:**

1. **Automation is King**: Automate everything - testing, deployment, infrastructure
2. **Observability Matters**: You can't fix what you can't see
3. **Security is Not Optional**: Build security in from the start
4. **Scale Horizontally**: Add more instances, not bigger instances
5. **Fail Fast and Recover**: Design for failure, not perfection
6. **Documentation is Critical**: Future you will thank present you
7. **Keep Learning**: DevOps evolves rapidly

**Interview Preparation Tips:**

1. Practice hands-on: Build real projects
2. Understand the "why", not just the "how"
3. Be ready to discuss trade-offs
4. Know your company's tech stack
5. Prepare questions about their infrastructure
6. Share real experiences and lessons learned
7. Be honest about what you don't know

**Resources for Further Learning:**

- AWS/GCP/Azure Documentation
- Kubernetes Documentation
- Site Reliability Engineering (Google)
- The Phoenix Project (DevOps book)
- Designing Data-Intensive Applications
- System Design Interview books
- Hands-on labs: A Cloud Guru, Linux Academy
- Open source contributions
- Personal projects on GitHub

**Good luck with your interviews!**

---

**Document Version**: 1.0  
**Last Updated**: February 24, 2026  
**Total Sections**: 18  
**Comprehensive Topics Covered**: All major DevOps/Cloud/SRE areas  

---

*End of DevOps & Cloud Engineering Interview Study Guide*

