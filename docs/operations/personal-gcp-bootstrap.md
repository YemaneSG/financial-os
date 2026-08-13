# Personal GCP bootstrap

This runbook creates the Financial OS deployment boundary in a new, personally
owned Google Cloud project. It intentionally keeps employer-owned cloud projects
out of the data path.

Do not put real project IDs, billing account IDs, email addresses, Firebase
configuration, owner subject IDs, or generated credentials in this repository.
Store them only in local ignored files, the Google Cloud console, GitHub
environment variables, or Secret Manager.

## Preconditions

- A personal Google account. It does not need to own a GCP project already.
- A billing profile you personally control.
- `gcloud`, Terraform 1.9.8, Docker, Node 20, and pnpm 11.
- This repository published to the intended GitHub account.

## 1. Create the personal project

1. Sign in to the Google Cloud console with the personal account.
2. Create a new project with a non-sensitive project ID.
3. Link the personal billing profile and set a conservative billing budget.
4. Enable Firebase on that same project and add a Web application.
5. Enable Google as a Firebase Authentication provider.

The Firebase sign-in email and the GCP project owner may be the same personal
Google account, but they do not have to be. Runtime authorization binds to the
stable Firebase user ID (`sub` in the verified Firebase ID token), never to the
display email.

## 2. Prepare local, ignored deployment inputs

```bash
cp infra/environments/dev/terraform.tfvars.example \
  infra/environments/dev/terraform.tfvars
```

Fill the ignored `terraform.tfvars` with the personal project number, private
bucket name, GitHub repository coordinates, hosting origin, billing account,
and alert address. Confirm it is ignored before adding any value:

```bash
git check-ignore infra/environments/dev/terraform.tfvars
```

## 3. Bootstrap the cloud prerequisites

Create a private GCS state bucket in the personal project first. Then initialize
Terraform and create only the APIs, identities, registry, storage, database, and
secret containers. This two-phase bootstrap is necessary because the Cloud Run
services must start from the real application image, which does not exist until
Artifact Registry has been created.

```bash
terraform -chdir=infra/environments/dev init \
  -backend-config="bucket=YOUR_PRIVATE_TERRAFORM_STATE_BUCKET" \
  -backend-config="prefix=financial-os/dev"

terraform -chdir=infra/environments/dev validate
terraform -chdir=infra/environments/dev plan \
  -target=module.apis \
  -target=module.iam \
  -target=module.registry \
  -target=module.storage \
  -target=module.sql \
  -target=module.secrets \
  -out=bootstrap.tfplan
terraform -chdir=infra/environments/dev show bootstrap.tfplan
terraform -chdir=infra/environments/dev apply bootstrap.tfplan
```

A human must inspect the plan before apply because Cloud SQL and networking are
billable. Never commit the plan, state, `.tfvars`, or backend configuration.

Build the bootstrap image locally, push it to the newly created registry, resolve
its immutable digest, and put that digest in the ignored `terraform.tfvars` as
`initial_image`:

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
FINOS_REGISTRY="$(terraform -chdir=infra/environments/dev output -raw artifact_registry_url)"
FINOS_IMAGE="${FINOS_REGISTRY}/app:bootstrap"
docker build --file apps/api/Dockerfile --tag "${FINOS_IMAGE}" .
docker push "${FINOS_IMAGE}"
gcloud artifacts docker images describe "${FINOS_IMAGE}" \
  --format='value(image_summary.digest)'
```

Use `${FINOS_REGISTRY}/app@sha256:...`, not the mutable tag, for
`initial_image`.

## 4. Grant PostgreSQL roles

Terraform creates three passwordless IAM database users, but PostgreSQL schema
privileges are a separate control plane. Retrieve their opaque usernames without
putting them in a tracked file:

```bash
terraform -chdir=infra/environments/dev output -raw migrate_database_user
terraform -chdir=infra/environments/dev output -raw api_database_user
terraform -chdir=infra/environments/dev output -raw worker_database_user
```

Set a strong one-time password for the built-in `postgres` administrator in the
Cloud SQL console and keep it only in a personal password manager. In Cloud SQL
Studio, copy `scripts/bootstrap-database-access.sql`, replace its three
`YOUR_*_DATABASE_USER` placeholders, and execute it against `financialos`. Do not
save or commit the substituted SQL. The migration role receives schema creation
rights; the API and worker receive only runtime table access.

## 5. Complete the Terraform apply

Review and apply the full plan. This creates Cloud Run, Cloud Tasks, monitoring,
and the remaining IAM bindings using the bootstrap image digest:

```bash
terraform -chdir=infra/environments/dev plan -out=dev.tfplan
terraform -chdir=infra/environments/dev show dev.tfplan
terraform -chdir=infra/environments/dev apply dev.tfplan
```

## 6. Replace all placeholder secret versions

Terraform creates secret containers with obvious placeholder versions. Before
the first application deploy, add real versions through the console or `gcloud`.
Required values include:

- Cloud SQL IAM connection settings
- stable owner Firebase UID, stored as `google:<firebase-uid>`
- Firebase project ID
- private evidence bucket name
- deployed hosting origin
- task-invoker service-account email
- full private worker processing URL
- worker OIDC audience (the worker base URL)
- extraction model, prompt, and schema versions

Values that depend on Cloud Run, such as the worker URL and OIDC audience, are
available only after step 5. The placeholder versions are adequate for the
bootstrap revision but must be replaced before processing a receipt.

Use Secret Manager input from standard input or a protected local file. Do not
put secret values on a shell command line that enters history.

## 7. Configure GitHub environment variables

Create the `dev` GitHub environment and set the non-secret deployment variables
documented in `.github/workflows/deploy.yml`, including the WIF provider, deploy
service account, project ID, Firebase Web configuration, API URL, and hosting
URL. WIF is restricted to this repository's `main` branch; do not create a
service-account key.

## 8. Register the single owner

After Firebase Hosting is deployed, sign in once and copy the account's stable
Firebase UID from Firebase Console → Authentication → Users. Add
`google:<firebase-uid>` as the latest `owner-allowlist` secret version, then add
the same subject to PostgreSQL through Cloud SQL Studio:

```sql
INSERT INTO auth_subjects (
  id, provider, provider_subject, allowlisted
)
VALUES (
  gen_random_uuid(), 'google', 'google:YOUR_FIREBASE_UID', TRUE
)
ON CONFLICT (provider_subject)
DO UPDATE SET allowlisted = EXCLUDED.allowlisted, updated_at = now();
```

Deploy a new API revision after updating the secret; running instances do not
reload Secret Manager environment variables in place. Never store the UID in a
tracked file—it is an opaque identifier, but it remains private deployment data.

## 9. Release gates

Before any real receipt upload:

1. CI is green, including integration, contract, security, container, and
   Terraform checks.
2. The database access bootstrap completed, and the migration job succeeds before
   traffic switches.
3. Hosting security headers pass `scripts/validate-headers.sh`.
4. An iPhone Safari test verifies camera capture, multi-image ordering, upload,
   durable acknowledgement, and install-to-home-screen behavior.
5. A synthetic end-to-end receipt reaches a terminal extraction state.
6. Bucket public-access prevention and Cloud Run worker denial are rechecked.

## Current project boundary

As of the initial implementation session, no Financial OS application resource
or personal financial data has been deployed to a cloud project. Cloud deployment
remains blocked until a personally controlled GCP project is selected.
