## Backend

### Test locally

sudo apt install python3-full python3-venv -y
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt


uvicorn app.main:app --reload --host 0.0.0.0 --port 8000