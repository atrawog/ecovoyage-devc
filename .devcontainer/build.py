#!/usr/bin/env python3
import requests
import datetime
import re
import subprocess
import json
import os

# Load the configuration from devcontainer.json
with open('devcontainer.json', 'r') as file:
    devcontainer_config = json.load(file)

# Extract values from the devcontainer configuration
container_name = devcontainer_config["name"]
dockerfile_path = devcontainer_config["build"]["dockerfile"]
docker_context = devcontainer_config["build"]["context"]
docker_args = devcontainer_config["build"]["args"]
docker_cache_from = devcontainer_config["build"].get("cacheFrom", [])

# Set BUILDKIT_INLINE_CACHE environment variable
os.environ["BUILDKIT_INLINE_CACHE"] = "1"

# Define the base of the image tag (without the build number)
current_year_month = datetime.datetime.now().strftime("%Y.%m.")

def get_next_build_number():
    base_tag = f"{container_name}:{current_year_month}"

    print(f"Fetching tags from Docker registry for {container_name}")

    # Fetch tags from the Docker registry
    response = requests.get(f'https://registry.hub.docker.com/v2/repositories/{container_name}/tags')
    print (response)
    if response.status_code == 200:
        tags = response.json().get('results', [])
        print (f"Found {tags}")
        build_numbers = []

        # Regex to find matching tags
        tag_regex = re.compile(rf'^{re.escape(current_year_month)}(\d{{2}})$')

        for tag in tags:
            tag_name = tag.get('name')
            match = tag_regex.match(tag_name)
            if match:
                build_number = int(match.group(1))
                build_numbers.append(build_number)

        # Determine the next build number
        next_build_number = max(build_numbers) + 1
    else:
        next_build_number = 0

    return next_build_number

def build_and_tag_docker_image(build_number):
    image_tag = f"{container_name}:{current_year_month}{build_number:02d}"

    print(f"Next build number calculated: {build_number:02d}")
    print(f"Building Docker image with tag: {image_tag}")

    # Prepare Docker buildx build arguments
    docker_build_args = ' '.join([f'--build-arg {key}={value}' for key, value in docker_args.items()])
    cache_from_args = ' '.join([f'--cache-from={source}' for source in docker_cache_from])

    build_command = f"docker buildx build --pull --no-cache --load -f {dockerfile_path} {docker_build_args} {cache_from_args} -t {image_tag} {docker_context}"
    subprocess.run(build_command, shell=True, check=True)

    # Generate a new Dockerfile in the context directory
    new_dockerfile_path = os.path.join(docker_context, "Dockerfile")
    with open(new_dockerfile_path, "w") as file:
        file.write(f"FROM {image_tag}\n")

    print(f"Docker image built and tagged as {image_tag}. New Dockerfile created at {new_dockerfile_path}")

if __name__ == "__main__":
    build_number = get_next_build_number()
    build_and_tag_docker_image(build_number)
