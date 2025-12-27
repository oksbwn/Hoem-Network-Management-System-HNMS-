## Backend

### Test locally

> TO install Python
sudo apt install python3-full python3-venv -y

> To set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

> To run the app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001