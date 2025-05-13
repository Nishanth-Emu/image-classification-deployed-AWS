## Setup

### Prerequisites

*   Python 3.12+ installed.
*   `pip` installed.
*   **(For EC2 Deployment)** An AWS Account and an EC2 instance (e.g., Ubuntu AMI).
*   **(For EC2 Deployment)** SSH access to your EC2 instance and the associated `.pem` key file.

### Local Setup

1.  **Clone the repository (or create the files):**
    *   Place `app.py` and `streamlit_app.py` in your project directory.
    *   Create the `Fruit_AI` directory and place your `fruit_cnn_model.h5` file inside it.

2.  **Create a Virtual Environment:**
    *   It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python3 -m venv myenv
    ```
    *(Replace `myenv` with your preferred virtual environment name.)*

3.  **Activate the Virtual Environment:**
    *   **On Linux/macOS:**
        ```bash
        source myenv/bin/activate
        ```

4.  **Create `requirements.txt`:**
    *   Create a file named `requirements.txt` in your project directory with the following content:
    ```txt
    fastapi
    uvicorn
    tensorflow
    Pillow
    numpy
    streamlit
    requests
    ```

5.  **Install Dependencies:**
    *   With your virtual environment activated, install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

6.  **Obtain the Model File:**
    *   Ensure your trained Keras model (`fruit_cnn_model.h5`) is placed in the `Fruit_AI/` directory.

## Running Locally

1.  Activate your virtual environment (`source myenv/bin/activate` or equivalent).
2.  **Start the FastAPI backend:**
    *   Navigate to your project directory and run:
    ```bash
    uvicorn app:app --reload --host 127.0.0.1 --port 8000
    ```
    *   The `--reload` flag is useful for local development. `--host 127.0.0.1` makes it accessible only from your local machine.

3.  Open a **new** terminal window/tab.
4.  Activate the **same** virtual environment in the new terminal.
5.  **Start the Streamlit frontend:**
    *   Navigate to your project directory and run:
    ```bash
    streamlit run streamlit_app.py
    ```
    *   This will typically open the Streamlit app in your web browser at `http://localhost:8501`.

## Deployment on EC2

This section summarizes the steps for deploying on an Ubuntu EC2 instance.

1.  **Launch an EC2 Instance:**
    *   Launch an Ubuntu EC2 instance (e.g., t2.micro or larger depending on model size/traffic).
    *   Ensure you select or create a key pair (`.pem` file) for SSH access.
    *   Configure the Security Group to allow **inbound SSH (Port 22)** from *your IP address* initially.

2.  **Transfer Project Files:**
    *   Use `scp` (Secure Copy) to copy your entire project directory from your local machine to the EC2 instance's home directory.
    ```bash
    scp -i /path/to/your/keypair.pem -r /path/to/local/project/folder ubuntu@your_ec2_public_ip:/home/ubuntu/
    ```
    *   Replace `/path/to/your/keypair.pem`, `/path/to/local/project/folder` (e.g., `image-project`), and `your_ec2_public_ip` with your actual values. Let's assume your project folder on EC2 will be `/home/ubuntu/image-project`.

3.  **Install Dependencies on EC2:**
    *   Connect to your EC2 instance via SSH:
        ```bash
        ssh -i /path/to/your/keypair.pem ubuntu@your_ec2_public_ip
        ```
    *   **(Option A) Using User Data (Recommended at Launch):** Provide a bash script in the EC2 "User data" field during instance launch to automate the setup below.
    *   **(Option B) Manual Installation:**
        ```bash
        # Update package list and install Python/Pip
        sudo apt update -y
        sudo apt install -y python3 python3-pip python3-venv

        # Navigate to your project directory (adjust if needed)
        cd /home/ubuntu/image-project

        # Create and activate virtual environment
        python3 -m venv myenv
        source myenv/bin/activate

        # Install dependencies
        pip install -r requirements.txt

        # Deactivate the virtual environment for now (systemd will manage it)
        # deactivate
        ```

4.  **Set up systemd Services:**
    *   Create systemd service files to manage your FastAPI and Streamlit applications as background processes.
    *   **Create FastAPI Service File:**
        ```bash
        sudo nano /etc/systemd/system/fastapi-app.service
        ```
        Paste the following content (adjust `WorkingDirectory` and `ExecStart` paths if your project folder or venv name differs):
        ```ini
        [Unit]
        Description=FastAPI Image Classification App
        After=network.target

        [Service]
        User=ubuntu
        WorkingDirectory=/home/ubuntu/image-project
        ExecStart=/home/ubuntu/image-project/myenv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
        Restart=on-failure
        RestartSec=10

        [Install]
        WantedBy=multi-user.target
        ```
        Save and close (Ctrl+X, then Y, then Enter).

    *   **Create Streamlit Service File:**
        ```bash
        sudo nano /etc/systemd/system/streamlit-app.service
        ```
        Paste the following content (adjust `WorkingDirectory` and `ExecStart` paths):
        ```ini
        [Unit]
        Description=Streamlit Frontend for Image Classification App
        After=network.target fastapi-app.service # Ensure FastAPI starts first (optional dependency)

        [Service]
        User=ubuntu
        WorkingDirectory=/home/ubuntu/image-project
        ExecStart=/home/ubuntu/image-project/myenv/bin/streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 --server.enableCORS=false --server.enableXsrfProtection=false # Added flags for potential proxy/access issues
        Restart=on-failure
        RestartSec=10

        [Install]
        WantedBy=multi-user.target
        ```
        Save and close. *Note: `--server.enableCORS=false` and `--server.enableXsrfProtection=false` might be needed depending on your setup/proxy, adjust if necessary.*

    *   **Manage Services:**
        ```bash
        # Reload systemd to recognize the new services
        sudo systemctl daemon-reload

        # Enable the services to start on boot
        sudo systemctl enable fastapi-app.service
        sudo systemctl enable streamlit-app.service

        # Start the services immediately
        sudo systemctl start fastapi-app.service
        sudo systemctl start streamlit-app.service

        # Check the status of the services
        sudo systemctl status fastapi-app.service
        sudo systemctl status streamlit-app.service
        ```

5.  **Configure EC2 Security Group for Access:**
    *   Go to the AWS EC2 console, find your instance, and navigate to its Security Group settings.
    *   Add **Inbound Rules** to allow TCP traffic on the ports your applications are listening on.
    *   **If NOT using Nginx:** Allow ports **8000** (FastAPI) and **8501** (Streamlit) from `0.0.0.0/0` (Anywhere) or your specific IP.
    *   **If using Nginx (Step 6):** Allow port **80** (HTTP) and potentially **443** (HTTPS) from `0.0.0.0/0` or your specific IP. You might choose to remove or restrict direct access to 8000 and 8501 if Nginx is the intended entry point.

6.  **Configure Nginx Reverse Proxy:**
    *   This step sets up Nginx to listen on port 80 and forward traffic to your Streamlit app running on port 8501. This specific configuration **only exposes Streamlit** via Nginx. FastAPI (on port 8000) remains accessible directly on its port if the security group allows, but is not proxied by this Nginx config. Streamlit should still communicate with FastAPI internally using `http://localhost:8000` or `http://127.0.0.1:8000`.
    *   **Install Nginx:**
        ```bash
        sudo apt update -y
        sudo apt install nginx -y
        ```
    *   **Configure Security Group:** Ensure your EC2 Security Group allows inbound traffic on **Port 80** (HTTP) from `0.0.0.0/0` or desired IPs (as mentioned in Step 5).
    *   **Check Main Nginx Configuration:** Ensure Nginx is set up to load configurations from `/etc/nginx/conf.d/`.
        ```bash
        sudo nano /etc/nginx/nginx.conf
        ```
        Look for a line like `include /etc/nginx/sites-enabled/*;`. If it exists and is *not* commented out, comment it out by adding a `#` at the beginning:
        ```nginx
        # include /etc/nginx/sites-enabled/*;
        ```
        Ensure there is an uncommented line like `include /etc/nginx/conf.d/*.conf;`. This tells Nginx to load configuration files from the `conf.d` directory. Save and exit (Ctrl+X, then Y, then Enter).

    *   **Create Nginx Configuration File for Streamlit:**
        ```bash
        sudo nano /etc/nginx/conf.d/streamlit.conf
        ```
        Paste the following configuration:
        ```nginx
        server {
            listen 80;          # Listen on standard HTTP port 80
            server_name _;      # Use _ to match any domain name/IP here (acts as default server)

            location / {
                proxy_pass http://localhost:8501; # Forward requests internally to Streamlit on localhost:8501
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "Upgrade"; # Corrected header name
                proxy_set_header Host $host;
                proxy_cache_bypass $http_upgrade;

                # Add headers for Streamlit to get client IP etc.
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }
        }
        ```
        *   `listen 80;`: Nginx listens for incoming connections on port 80.
        *   `proxy_pass http://localhost:8501;`: Sends incoming requests to Streamlit running locally on port 8501.
        Save and exit the editor.

    *   **Test Nginx Configuration:**
        ```bash
        sudo nginx -t
        ```
        This command checks for syntax errors. It should output:
        ```
        nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
        nginx: configuration file /etc/nginx/nginx.conf test is successful
        ```
        If you see errors, carefully review `/etc/nginx/nginx.conf` and `/etc/nginx/conf.d/streamlit.conf` for typos or incorrect syntax.

    *   **Restart Nginx to Apply Changes:**
        ```bash
        sudo systemctl restart nginx
        ```
        You can also check its status: `sudo systemctl status nginx`.

## Usage

Once the applications are running (either locally or on EC2):

1.  Open your web browser.
2.  Navigate to the address where your Streamlit application is accessible:
    *   **Local:** `http://localhost:8501`
    *   **EC2 (Direct Access):** `http://your_ec2_public_ip:8501` (Ensure Security Group allows port 8501)
    *   **EC2 (via Nginx):** `http://your_ec2_public_ip_or_domain` (Ensure Security Group allows port 80). Note: With the provided Nginx config, access is at the root `/`.

3.  Use the file uploader in the Streamlit interface to select an image file.
4.  Click the "Predict" button.
5.  The application will send the image to the FastAPI backend (Streamlit communicates directly with FastAPI on localhost:8000 internally on the server), which uses the Keras model to classify it, and the result will be displayed in the Streamlit frontend.
