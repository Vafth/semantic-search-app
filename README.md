# semantic-search-app

Experimental prototype of a semantic search app using IBM Granite embedding models.

A microservices-based vector search engine that indexes `.txt` documents and retrieves 
relevant content using dense embeddings.

Supports three IBM Granite embedding models (small English, normal English, multilingual),
optional sentence-level result refinement, and deep search for borderline chunks.
Deployable locally via Docker Compose, in a Kubernetes cluster via Minikube, or on GCP GKE.

---

## Usage Examples

<details>
<summary>Step-by-step Guide</summary>

### 1. Open the app in your browser

Navigate to `http://localhost:8080`.
Click on **Register** in the top right corner to create your account.

![Sign-in/Register modal](docs/screenshots/auth.png)

### 2. Upload the document

In the Upload Document section, click **Choose File**, select `test2.txt`, then click **Upload**.

![Upload document](docs/screenshots/document-list-empty.png)

### 3. Wait for processing

The document will be indexed across all three embedding models. For a small document this takes 10–20 seconds. A larger document (200+ chunks) may take several minutes. Watch the **Documents** table — wait until the status turns green and says ready.

![Document list after upload](docs/screenshots/document-processing.png)

### 4. Render the document

Click the **Render** button next to the document name to display the full text. After a search, matched sentences will be highlighted in yellow.

![Document render](docs/screenshots/document-render.png)

### 5. Configure search parameters

Fill in the search query and adjust the parameters as needed (e.g., choosing your model, Top K results, and Score Threshold).

![Search results](docs/screenshots/empty-search-params.png)

### 6. Run the search

Click **Search** to execute your query. The search results will populate at the bottom, displaying the similarity score and source filename. To see the matched sentences highlighted in yellow, click **Render** next to your document in the table.

![Search results](docs/screenshots/search-success-whole-screen.png)

</details>

<details>
<summary>Search History</summary>

The app automatically saves your previous search requests so you can easily return to them later.

### Accessing Your History

To open your search history, click the burger menu (≡) in the top-left corner of the screen. This will slide out a sidebar displaying your past searches.

![Search results](docs/screenshots/search-history.png)

### Loading a Previous Search

Clicking on any search result from the history list will automatically restore your previous session. It will instantly fill in your previous parameters, populate the search results list, and apply the proper highlighting to the loaded document snippets.

![Search results](docs/screenshots/autofilled-search-params-with-history-bar.png)
![Search results](docs/screenshots/autofilled-search-result.png)

### Managing Your History

To keep your history clean, you can remove any saved search result. Simply click the "X" on the right side of the specific search item in the history list to delete it.

</details>

<details>
<summary>Manage Profile</summary>

Your account settings are accessible at any time from the top-right corner of the screen, without leaving your current search session.

### Accessing Your Profile

Click your username button in the top bar to open the account dropdown. It displays your role, registration date, last update, and current storage usage with a live progress bar showing how much of your quota is used.

![Profile card](docs/screenshots/profile-card.png)

### Changing Your Username

Click **Change username** to expand the form, enter your new username, and press **Update username**. The top bar and account card will reflect the new name immediately.

![Username changed successfully](docs/screenshots/username-change-success.png)

### Changing Your Password

Click **Change password** to expand the form. You will need to confirm your current password before setting a new one. Passwords must be at least 8 characters.
A confirmation message appears inline on success.

![Password changed successfully](docs/screenshots/password-change-success.png)

</details>

---

## Architecture

```
                  ┌─────────────────────────────┐
                  │           Browser           │
                  └──────────────┬──────────────┘
                                 │ HTTP :8080
                                 ▼
                  ┌─────────────────────────────┐
                  │         API Gateway         │
                  │      (serves frontend)      │
                  └──────────────┬──────────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       ▼                         ▼                         ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ User Service │          │   Document   │          │    Search    │
│    :8003     │          │   Service    │          │    Service   │
│              │          │    :8001     │          │    :8002     │
└──────┬───────┘          └──────┬───────┘          └──────┬───────┘
       │                         │                         │
       │   ┌─────────────────────┴─────────────────────────┤
       ▼   ▼                                               │
┌──────────────┐                                           │
│  PostgreSQL  │                                           │
│   Database   │                                           │
│    :5432     │                                           │
└──────────────┘                                           │
                                                           │
                ┌──────────────────────────────────────────┘
                │
                ├─────────────────────────────────┐
                ▼                                 ▼
 ┌─────────────────────────────┐   ┌─────────────────────────────┐
 │        Model Service        │   │           Qdrant            │
 │    IBM Granite Embeddings   │   │       Vector Database       │
 │            :8000            │   │            :6333            │
 └─────────────────────────────┘   └─────────────────────────────┘
```

---

### Services

| Service | Port | Description |
|---|---|---|
| gateway | 8080 | API gateway + frontend |
| model-service | 8000 | IBM Granite embedding inference |
| user-service | 8001 | User authentication, account management, and search history |
| document-service | 8002 | Document upload, indexing, retrieval |
| search-service | 8003 | Vector search with refine and deep search |
| qdrant | 6333 | Vector database |
| postgres | 5432 | Relational database for users, document metadata, and history |

### Embedding Models

| Model key | Model | Dims | Use case |
|---|---|---|---|
| `small_model` | granite-embedding-small-english-r2 | 384 | Fast, English |
| `normal_model` | granite-embedding-english-r2 | 768 | Accurate, English |
| `multilingual_model` | granite-embedding-278m-multilingual | 768 | Multilingual |

---

## Prerequisites

- [uv](https://github.com/astral-sh/uv) — Python package manager
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Minikube](https://minikube.sigs.k8s.io/) _(for Minikube deployment)_
- [kubectl](https://kubernetes.io/docs/tasks/tools/) _(for Kubernetes deployments)_
- [Terraform](https://developer.hashicorp.com/terraform) _(for infrastructure provisioning)_
- [Helm](https://helm.sh/) _(for Kubernetes package management)_
- [ArgoCD](https://argo-cd.readthedocs.io/en/stable/) _(for GitOps deployment)_
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) _(for GCP deployment)_

---

## Running the Project

<details>
<summary>Option 1: Local Development (Docker Compose)</summary>

#### Prerequisites

- Docker & Docker Compose

#### 1. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

> Modify secret keys and database credentials inside `.env`

#### 2. Start Services

```bash
docker compose up --build -d
```

#### 3. Access the Application

Open your browser and navigate to `http://localhost:8080`.

</details>

<details>
<summary>Option 2: GCP GKE</summary>

#### Prerequisites

- gcloud CLI (authenticated), kubectl, Terraform, Helm

#### 1. Authenticate with GCP

```bash
gcloud auth application-default login
gcloud config set project <your-project-id>
```

#### 2. Configure Terraform

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

> Fill in your GCP project ID, region, zone, cluster name, and application secrets

#### 3. Provision Infrastructure

```bash
cd terraform
terraform init
terraform apply
```

Terraform provisions:
- VPC, subnet, and GKE cluster
- Node pool with configured machine type
- Static external IP for the gateway LoadBalancer
- Kubernetes namespace and secrets

#### 6. Access the Application

The gateway is exposed via a GCP LoadBalancer. Get the external IP:

```bash
kubectl get service gateway -n semantic-search-ns
```

Open `http://<EXTERNAL-IP>` in your browser.

</details>

---

## CI/CD

The project uses a dual CI/CD setup:

### Jenkins (Primary)

Self-hosted Jenkins running via Docker Compose with Docker-in-Docker, configured entirely as code using JCasC (Jenkins Configuration as Code).

**Setup:**

```bash
cd jenkins
docker compose up -d --build
```

Access Jenkins at `http://localhost:8080`.

Copy and fill in credentials:

```bash
cp jenkins/.env.example jenkins/.env
```

```env
JENKINS_ADMIN_PASSWORD=your_password
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_pat
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_token
```

**Pipelines:**

| Pipeline | Trigger | Description |
|---|---|---|
| `services/gateway` | Manual | Build, test, report coverage |
| `services/search_service` | Manual | Build, test, report coverage |
| `services/document_service` | Manual | Build, test, report coverage |
| `services/user_service` | Manual | Build, test, report coverage |
| `services/model_service` | Manual | Build, test, report coverage |
| `build-and-deploy` | Manual | Build all images, push to GHCR, update Helm values |

Each service pipeline uses Docker Compose with real Postgres, Qdrant, and WireMock instances — no mocks for infrastructure dependencies.

### GitHub Actions (Secondary)

Defined in `.github/workflows/` — currently paused due to runner limits. Workflow files serve as the canonical CI definition for future cloud runner setup.

---

## API Endpoints

All endpoints are accessible through the gateway at `http://localhost:8080`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Frontend |
| `POST` | `/api/upload` | Upload and index a `.txt` document |
| `GET` | `/api/documents` | List all indexed documents |
| `GET` | `/api/document/{id}/text` | Retrieve full document text |
| `DELETE` | `/api/document/{id}` | Delete a document |
| `GET` | `/api/search` | Semantic search |
| `GET` | `/api/history` | Get whole search history |
| `DELETE` | `/api/history/{id}` | Delete a history record |
| `GET` | `/auth/me` | Get user data |
| `PATCH` | `/auth/me/username` | Change username |
| `PATCH` | `/auth/me/password` | Change password |

### Search Parameters

| Parameter | Default | Description |
| --- | --- | --- |
| `query` | required | Search query |
| `model` | `small_model` | Embedding model to use |
| `top_k` | `5` | Number of results |
| `score` | `0.4` | Minimum similarity score |
| `refine` | `false` | Filter irrelevant sentences within chunks |
| `dif` | `0.05` | Sentence score threshold = score + dif |
| `deep` | `false` | Scan borderline chunks at sentence level |
| `deep_min` | `0.25` | Lower bound for borderline chunks |
| `document_ids` | none | Comma-separated list of document IDs to search within |

---

## Roadmap

- [x] **v0.1.0 — Core Search Engine**
  - Microservices architecture (Gateway, Document, Search, Model Services, Qdrant)
  - Vector search with 3 IBM Granite embedding models
  - Result refinement and deep search capabilities
  - Initial Docker Compose & Minikube deployment

- [x] **v0.1.5 — User Service, Auth & Account Management (Current)**
  - User authentication with JWT and PostgreSQL integration
  - Three-tier role hierarchy (owner / admin / user) with owner bootstrapped on first start
  - Per-role storage quotas enforced server-side on document upload
  - Account settings — username and password change
  - Persistent search history with full parameter and result replay, deletable entries
  - Redesigned UI — search panel with sliders, account dropdown, history sidebar
  - Automated deployment with Terraform, Helm, and ArgoCD
  - CI pipeline with GitHub Actions

- [ ] **v0.2.0 — Administration, Monitoring & CI**
  - Admin dashboard — user management, per-user stats, aggregate usage analytics
  - Owner dashboard — cluster metrics via Grafana and Loki (infrastructure level)
  - Expanded test suite — max coverage of unit, integration, and E2E tests
  - CI/CD transition to Jenkins with DockerHub registry

- [ ] **v0.3.0 — Agentic RAG & Cloud Deployment**
  - Migrate embedding models from HuggingFace to Ollama
  - AI Chat Assistant (Qwen 2.5) replacing static search as primary interface
  - Intelligent multi-query search — assistant operates on history, selects models, fans out queries
  - Chat-scoped document management and per-chat model selection
  - Cloud infrastructure deployment (AWS / Azure)

---

## Sources

- https://huggingface.co/ibm-granite/
- https://python-client.qdrant.tech/

---

## License

MIT