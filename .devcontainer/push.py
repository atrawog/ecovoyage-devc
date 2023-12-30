#!/usr/bin/env python3
import subprocess
import re
import datetime
import json
import os

# Path to devcontainer.json
devcontainer_json_path = 'devcontainer.json'

def load_devcontainer_config():
    with open(devcontainer_json_path, 'r') as file:
        return json.load(file)

def save_devcontainer_config(config):
    with open(devcontainer_json_path, 'w') as file:
        json.dump(config, file, indent=4)

def get_latest_image_tag(container_name):
    base_tag_pattern = rf"{re.escape(container_name)}:\d{{4}}\.\d{{2}}\."

    print("Checking local Docker images to find the latest image...")

    # Get the list of Docker images
    result = subprocess.run(['docker', 'images', '--format', '{{.CreatedAt}}\t{{.Repository}}:{{.Tag}}', '--no-trunc'], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("Failed to get Docker images list")

    # Extract image creation time and tag
    image_tags = []
    for line in result.stdout.strip().split('\n'):
        match = re.match(r"(.+)\t(" + base_tag_pattern + r"\d{4})", line)
        if match:
            image_time, image_tag = match.groups()
            try:
                image_time = datetime.datetime.strptime(image_time.split('+')[0].strip(), "%Y-%m-%d %H:%M:%S")
                image_tags.append((image_time, image_tag))
            except ValueError as e:
                print(f"Error parsing date: {e}")

    if not image_tags:
        return None

    # Sort the tags by creation time and build number, and return the latest
    latest_image_tag = sorted(image_tags, key=lambda x: (x[0], int(x[1].split('.')[-1])), reverse=True)[0][1]
    return latest_image_tag

def push_docker_image_to_hub(image_tag):
    print(f"Pushing Docker image to Docker Hub: {image_tag}")
    push_command = f"docker push {image_tag}"
    subprocess.run(push_command, shell=True, check=True)
    print(f"Docker image {image_tag} pushed to Docker Hub.")
    return image_tag

def update_cache_from_in_devcontainer(image_tag):
    config = load_devcontainer_config()
    config['build']['cacheFrom'] = [image_tag]
    save_devcontainer_config(config)
    print(f"Updated cacheFrom in devcontainer.json to {image_tag}")

if __name__ == "__main__":
    devcontainer_config = load_devcontainer_config()
    container_name = devcontainer_config["name"]

    image_tag = get_latest_image_tag(container_name)
    if image_tag:
        pushed_image_tag = push_docker_image_to_hub(image_tag)
        update_cache_from_in_devcontainer(pushed_image_tag)
    else:
        print("No Docker images found.")
