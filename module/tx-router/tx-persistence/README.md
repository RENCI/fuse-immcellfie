[![Build Status](https://travis-ci.com/RENCI/tx-persistence.svg?token=hSyYs1SXtzNJJDmjUzHi&branch=master)](https://travis-ci.com/RENCI/tx-persistence)

## purpose
This simple container wraps an extant mongodb container to allow us to easily create a user via the environment variables. The user is created based on the '$MONGO_NON_ROOT_USERNAME', '$MONGO_NON_ROOT_PASSWORD' environmental variables provided to the Dockerfile. See Dockerfile.

## test
```
./test.sh
```

## auto-build
Every commit to a tag (e.g., 'v.0.2.0') or to master triggers an autobuild and autotest of the container on dockerhub (e.g., tx-persistence:v0.2.0 for a tag named v0.2.0, tx-persistence:v0.3.0-rc for master after latest tag v0.2.0)



