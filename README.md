## Setup

### Prerequisites

*   Python 3.12+ installed.
*   `pip` installed.
*   An AWS Account and an EC2 instance (e.g., Ubuntu AMI) for EC2 Deployment.
*   SSH access to your EC2 instance and the associated `.pem` key file for EC2 Deployment.

### Local Setup

1.  **Clone the repository (or create the files):**
    *   Place `app.py` and `streamlit_app.py` in your project directory.
    *   Create the `Fruit_AI` directory and place your `fruit_cnn_model.h5` file inside it.

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv myenv
    ```

3.  **Activate the Virtual Environment:**
    *   **On Linux:**
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

1.  Activate your virtual environment.
2.  **Start the FastAPI backend:**
    *   Navigate to your project directory and run:
    ```bash
    uvicorn app:app --reload --host 127.0.0.1 --port 8000
    ```

3.  Open a **new** terminal window/tab.
4.  Activate the **same** virtual environment in the new terminal.
5.  **Start the Streamlit frontend:**
    *   Navigate to your project directory and run:
    ```bash
    streamlit run streamlit_app.py
    ```
    *   This will typically open the Streamlit app in your web browser at `http://localhost:8501`.

## Deployment on EC2

1.  **Launch an EC2 Instance:**
    *   Launch an Ubuntu EC2 instance.
    *   Ensure you select or create a key pair (`.pem` file) for SSH access.
    *   Configure the Security Group to allow inbound SSH (Port 22) from your IP address initially.

2.  **Transfer Project Files:**
    *   Use `scp` to copy your project directory to the EC2 instance.
    ```bash
    scp -i /path/to/your/keypair.pem -r /path/to/local/project/folder ubuntu@your_ec2_public_ip:/home/ubuntu/
    ```

3.  **Install Dependencies on EC2:**
    *   Connect to your EC2 instance via SSH:
        ```bash
        ssh -i /path/to/your/keypair.pem ubuntu@your_ec2_public_ip
        ```
    *   **Manual Installation:**
        ```bash
        sudo apt update -y
        sudo apt install -y python3 python3-pip python3-venv

        cd /home/ubuntu/image-project

        python3 -m venv myenv
        source myenv/bin/activate

        pip install -r requirements.txt
        ```

4.  **Set up systemd Services:**
    *   Create systemd service files for FastAPI and Streamlit.
    *   **Create FastAPI Service File:**
        ```bash
        sudo nano /etc/systemd/system/fastapi-app.service
        ```
        Paste the following content:
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
        Save and close.

    *   **Create Streamlit Service File:**
        ```bash
        sudo nano /etc/systemd/system/streamlit-app.service
        ```
        Paste the following content:
        ```ini
        [Unit]
        Description=Streamlit Frontend for Image Classification App
        After=network.target fastapi-app.service

        [Service]
        User=ubuntu
        WorkingDirectory=/home/ubuntu/image-project
        ExecStart=/home/ubuntu/image-project/myenv/bin/streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 --server.enableCORS=false --server.enableXsrfProtection=false
        Restart=on-failure
        RestartSec=10

        [Install]
        WantedBy=multi-user.target
        ```
        Save and close.

    *   **Manage Services:**
        ```bash
        sudo systemctl daemon-reload
        sudo systemctl enable fastapi-app.service
        sudo systemctl enable streamlit-app.service
        sudo systemctl start fastapi-app.service
        sudo systemctl start streamlit-app.service
        sudo systemctl status fastapi-app.service
        sudo systemctl status streamlit-app.service
        ```

5.  **Configure EC2 Security Group for Access:**
    *   Go to the AWS EC2 console, find your instance, and navigate to its Security Group settings.
    *   Add Inbound Rules to allow TCP traffic.
    *   **If NOT using Nginx:** Allow ports **8000** and **8501** from `0.0.0.0/0` or your IP.
    *   **If using Nginx:** Allow port **80** (HTTP) and potentially **443** (HTTPS) from `0.0.0.0/0` or your IP.

6.  **Configure Nginx Reverse Proxy:**
    *   This step sets up Nginx to listen on port 80 and forward traffic to Streamlit on port 8501.
    *   **Install Nginx:**
        ```bash
        sudo apt update -y
        sudo apt install nginx -y
        ```
    *   **Configure Security Group:** Ensure your EC2 Security Group allows inbound traffic on Port 80 (HTTP).
    *   **Check Main Nginx Configuration:**
        ```bash
        sudo nano /etc/nginx/nginx.conf
        ```
        Look for `include /etc/nginx/sites-enabled/*;`. If it exists and is not commented out, comment it by adding `#` at the beginning. Ensure `include /etc/nginx/conf.d/*.conf;` is uncommented. Save and exit.

    *   **Create Nginx Configuration File for Streamlit:**
        ```bash
        sudo nano /etc/nginx/conf.d/streamlit.conf
        ```
        Paste the following configuration:
        ```nginx
        server {
            listen 80;
            server_name _;

            location / {
                proxy_pass http://localhost:8501;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "Upgrade";
                proxy_set_header Host $host;
                proxy_cache_bypass $http_upgrade;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }
        }
        ```
        Save and exit.

    *   **Test Nginx Configuration:**
        ```bash
        sudo nginx -t
        ```
        The output should indicate the syntax is ok and the test is successful.

    *   **Restart Nginx to Apply Changes:**
        ```bash
        sudo systemctl restart nginx
        ```

## Usage

Once the applications are running:

1.  Open your web browser.
2.  Navigate to the address where your Streamlit application is accessible:
    *   **Local:** `http://localhost:8501`
    *   **EC2 (Direct Access):** `http://your_ec2_public_ip:8501`
    *   **EC2 (via Nginx):** `http://your_ec2_public_ip_or_domain`

3.  Use the file uploader to select an image file.
4.  Click the "Predict" button.
5.  The result will be displayed in the Streamlit frontend.
