# KernelCI Staging Web

This is a web application for managing KernelCI staging builds. 
It provides a web interface for triggering and monitoring staging runs, managing users, and configuring the application.
Main purpose of this application to improve developers cooperation and visibility of staging runs,
without requiring ssh privileges to staging server.

## How to Run

1.  **Install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Run the application:**
    ```bash
    python3 main.py
    ```
    Or use the provided run script:
    ```bash
    ./run.py
    ```

3.  **Access the web interface:**
    Open your browser and go to `http://localhost:9090`.

## Default Login

*   **Username:** admin
*   **Password:** admin

It is recommended to change the admin password after the first login.

## GitHub OAuth Login

Optionally, users can log in with their GitHub account. Access is restricted
to members of a GitHub team — by default the `staging` team of the `kernelci`
organization.

1.  Register a GitHub OAuth App (Settings → Developer settings → OAuth Apps)
    with the authorization callback URL set to
    `https://<your-host>/auth/github/callback`.
2.  Configure the `[github_oauth]` section in `config/staging.toml`:
    ```toml
    [github_oauth]
    enabled = true
    client_id = "<client id>"
    client_secret = "<client secret>"
    org = "kernelci"        # GitHub organization
    team = "staging"        # team slug whose members are allowed
    member_role = "maintainer"  # role for users created via OAuth
    ```

On first login a user account is created automatically with the configured
role. If a local account with the same username already exists, it is linked
to the GitHub account and keeps its existing role.
