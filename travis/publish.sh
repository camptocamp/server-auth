#!/bin/bash -e

local_dir="$(dirname "$0")"

function deploy {
    local tag=$1

    echo "Pushing image to GitHub Packages ghcr.io/${TRAVIS_REPO_SLUG}:${tag}"
    docker tag ${GENERATED_IMAGE} ghcr.io/${TRAVIS_REPO_SLUG}:${tag}
    docker push ghcr.io/${TRAVIS_REPO_SLUG}:${tag}
}

if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
  echo ${GITHUB_PACKAGE_TOKEN} | docker login ghcr.io --username "${GITHUB_PACKAGE_USER}" --password-stdin
  docker_tag=r-$TRAVIS_BRANCH-$TRAVIS_COMMIT

  if [ "$TRAVIS_BRANCH" == "master" ]; then
    deploy latest
    deploy ${docker_tag}

  elif [ ! -z "$TRAVIS_TAG" ]; then
    deploy ${TRAVIS_TAG}

  elif [ ! -z "$TRAVIS_BRANCH" ]; then
    deploy ${docker_tag}

  else
    echo "Not deploying image"
  fi
fi
