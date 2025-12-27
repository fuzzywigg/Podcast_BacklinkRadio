# ANDON LABS - DEPLOYMENT INITIATION PROTOCOL

**TARGET AUDIENCE:** Andon Labs Development Team / Payment Portal LLM Agent  
**PURPOSE:** Initialization of Hive Infrastructure (Cloud Run + Firestore)

---

To the initialization Agent:
Please execute the following setup sequence to prepare the Backlink Hive for deployment.

## 1. Google Cloud Platform Provisioning

**Context:** The Hive requires a stateless container runtime (Cloud Run) and a persistent NoSQL document store (Firestore) to maintain memory of the "Queen" and her "Bees" (Agents).

### Action Checklist

- [ ] **Create/Select Project:** Ensure a GCP Project exists (e.g., `andon-backlink-hive-prod`).
- [ ] **Enable APIs:**
  - `run.googleapis.com` (Cloud Run)
  - `firestore.googleapis.com` (Firestore)
  - `artifactregistry.googleapis.com` (Container Registry)
  - `cloudbuild.googleapis.com` (Cloud Build)
- [ ] **Initialize Firestore:**
  - **CRITICAL:** Select **Native Mode** (not Datastore mode).
  - **Region:** Recommended `us-central1` (or match Cloud Run region).
  - **Collection:** The app defaults to using a root collection named `hive_data`. No manual schema creation is needed; the Storage Adapter will create documents on first write.

## 2. Environment Configuration (The "Genesis Config")

The following environment variables must be injected into the Cloud Run service at deployment time.

| Variable | Required | Description | Example Value |
| :--- | :--- | :--- | :--- |
| `GCP_PROJECT_ID` | **YES** | The Project ID where Firestore lives. | `andon-backlink-hive` |
| `STORAGE_TYPE` | **YES** | Switches storage from local file to cloud. | `FIRESTORE` |
| `HIVE_SECRET_KEY` | **YES** | Used to HMAC sign state changes. | `(Generate a strong UUID)` |
| `OPENAI_API_KEY` | **YES** | Powering the LLM brains. | `sk-...` |
| `TWITTER_API_KEY` | No | If `SocialPosterBee` is active. | `...` |
| `TWITTER_API_SECRET` | No | If `SocialPosterBee` is active. | `...` |
| `BROWSER_USE_API_KEY`| No | If using Browser Use for deep scraping. | `...` |

## 3. Deployment Instruction (CLI)

Once prerequisites are met, deploy the Hive using the generated Dockerfile:

```bash
# 1. Build and Submit to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/backlink-hive

# 2. Deploy to Cloud Run
gcloud run deploy backlink-hive \
  --image gcr.io/PROJECT_ID/backlink-hive \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \  # (Or --no-allow-unauthenticated for internal only)
  --set-env-vars STORAGE_TYPE=FIRESTORE,GCP_PROJECT_ID=PROJECT_ID,HIVE_SECRET_KEY=SECRET
```

## 4. Verification

After deployment, access the service URL:

- `/health` -> Should return `{"status": "ok"}`.
- `/` -> Should load the Dashboard HTML.
