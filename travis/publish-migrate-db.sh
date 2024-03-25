#!/bin/bash -e

local_dir="$(dirname "$0")"

function deploy {
    local tag=$1

    echo "Pushing database migration image to GitHub Packages ghcr.io/${TRAVIS_REPO_SLUG}:${tag}_migrate_db"
    docker tag ${GENERATED_MIGRATION_DB_IMAGE} ghcr.io/${TRAVIS_REPO_SLUG}:${tag}_migrate_db
    docker push ghcr.io/${TRAVIS_REPO_SLUG}:${tag}_migrate_db
}

if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
  echo ${GITHUB_PACKAGE_TOKEN} | docker login ghcr.io --username "${GITHUB_PACKAGE_USER}" --password-stdin
  docker_tag=r-$TRAVIS_BRANCH-$TRAVIS_COMMIT

  if [ "$TRAVIS_BRANCH" == "master" ]; then
    echo "Pushing database migration image to GitHub Packages ghcr.io/${TRAVIS_REPO_SLUG}:latest_migrate_db"
    docker tag ${GENERATED_MIGRATION_DB_IMAGE} ghcr.io/${TRAVIS_REPO_SLUG}:latest_migrate_db
    docker push "ghcr.io/${TRAVIS_REPO_SLUG}:latest_migrate_db"

    deploy ${docker_tag}

  elif [ ! -z "$TRAVIS_TAG" ]; then
    echo "Pushing database migration image to GitHub Packages ghcr.io/${TRAVIS_REPO_SLUG}:${TRAVIS_TAG}_migrate-db"
    docker tag ${GENERATED_MIGRATION_DB_IMAGE} ghcr.io/${TRAVIS_REPO_SLUG}:${TRAVIS_TAG}_migrate_db
    docker push "ghcr.io/${TRAVIS_REPO_SLUG}:${TRAVIS_TAG}_migrate_db"

  elif [ ! -z "$TRAVIS_BRANCH" ]; then
    deploy ${docker_tag}

  else
    echo "Not deploying database migration image"
  fi
fi
