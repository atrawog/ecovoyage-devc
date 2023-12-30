#!/bin/bash

# Check if the user can execute commands with sudo
if sudo -l &>/dev/null; then
    # Define the environment variables to check
    env_vars=("KVM_DEVICE" "DOCKER_SOCKET" "CONTAINER_WORKSPACE_FOLDER")

    # Loop over the environment variables
    for env_var in "${env_vars[@]}"; do
        # Check if the environment variable is set and points to either a file, directory, socket, or character device
        if [ -n "${!env_var}" ] && ([ -f "${!env_var}" ] || [ -d "${!env_var}" ] || [ -S "${!env_var}" ] || [ -c "${!env_var}" ]); then
            # Process the file, directory, socket, or character device
            if [ -d "${!env_var}" ]; then
                # It's a directory, process all children
                find "${!env_var}" -type d -o -type f -o -type s -exec bash -c '
                    for path; do
                        # Check the ownership of the path
                        OWNER_UID=$(stat -c "%u" "$path")
                        OWNER_GID=$(stat -c "%g" "$path")

                        if [ "$OWNER_UID" -ne '"$NB_UID"' ] || [ "$OWNER_GID" -ne '"$NB_GID"' ]; then
                            echo "Changing ownership of $path"
                            sudo chown '"$NB_UID:$NB_GID"' "$path"
                        fi
                    done
                ' bash {} +
            else
                # It's a file, socket, or character device
                OWNER_UID=$(stat -c "%u" "${!env_var}")
                OWNER_GID=$(stat -c "%g" "${!env_var}")

                if [ "$OWNER_UID" -ne "$NB_UID" ] || [ "$OWNER_GID" -ne "$NB_GID" ]; then
                    echo "Changing ownership of ${!env_var}"
                    sudo chown "$NB_UID:$NB_GID" "${!env_var}"
                fi
            fi
        fi
    done
else
    echo "User does not have sudo privileges. Exiting script."
fi
