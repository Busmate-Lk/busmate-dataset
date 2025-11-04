step 1
# Build the Docker image (this will take a few minutes)
docker build -t pdf-converter .

# Run the container with your current directory mounted
docker run -it --rm -v "$(pwd):/app" pdf-converter python3 pdf_to_csv.py

step 2 
# 4. Build & Run
docker-compose build
docker-compose run --rm bus-extractor