echo "Frontend can be found at http://localhost:5001"
podman pull python:3.12-rc-slim-buster
podman compose up --build
