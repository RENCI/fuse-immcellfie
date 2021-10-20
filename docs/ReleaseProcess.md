## Immcellfie Release Process

### Get OK from Project Manager for an update outage

### ssh into dev-immcellfie/stage-immcellfie/immcellfie
```
IMMCELLFIEUSER=immcellfie-service
IMMCELLFIEROOT= /home/immcellfie-service
```
### conditional code:

for dev-immcellfie.edc.renci.org/cellfie, use 
```
IMMCELLFIEHOST= dev-immcellfie.edc.renci.org
```
for stage-immcellfie.edc.renci.org/cellfie, use 
```
IMMCELLFIEHOST= stage-immcellfie.edc.renci.org
```
for immcellfie.edc.renci.org
```
IMMCELLFIEHOST= immcellfie.edc.renci.org
```
### For all servers:
```
ssh ${IMMCELLFIEHOST}.renci.org/cellfie
sudo cd ${IMMCELLFIEROOT}
docker-compose down
```
### Clone fuse-immcellfie repository, if it's not there already
```
git clone https://github.com/RENCI/fuse-immcellfie.git
```
### Checkout appropriate branch
```
cd ..
cd dashboard/
git branch
git fetch origin
git checkout <release-branch>
git branch    #check if you are on the right branch
```
### At this point, try to recollect the changes that were made for this release. If there are only frontend changes, check out your branch and run:
### Check if the release version is correct
```
cat docker-compose.prod.yml
```
### Deployment
```
docker-compose -f docker-compose.prod.yml up --build -d -V
```
### Ensure pipeline image version is correct
```
docker ps
```
