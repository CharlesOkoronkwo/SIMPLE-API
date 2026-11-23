# legacy-deploy (not part of Ledger)

This folder holds the deployment experiment this repository started as: Terraform for a
GKE cluster, a Dockerfile, and two GitHub Actions workflows that provisioned and deployed
the original `/time` API.

It is kept for history only.

- Ledger does not need any of it. It runs locally with Python and SQLite and needs no
  network, cloud account or container runtime.
- The project ID, service account, state bucket and image name in these files have been
  replaced with placeholders (`your-gcp-project-id` and similar).
- The workflows are in `workflows-inactive/`, outside `.github/workflows/`, so GitHub
  does not run them. They also refer to directories (`terraform/`, `kubernetes_resource/`)
  and a `Dockerfile` spelling that no longer match this layout, so they would need
  rework before any real use.
- Nothing here has been run against a real cloud project as part of Ledger.
