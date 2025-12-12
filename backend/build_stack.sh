#!/bin/bash

set -e

STACK_NAME=calendar_stack

echo "Building docker images..."

docker build -t calendar_service_image ./services/calendar
docker build -t profile_service_image ./services/profile

echo "Finised building images."

echo "Adding keycloak config..."

docker config create keycloak-realm-config ./keycloak/realm-config.json

echo "Done!"


