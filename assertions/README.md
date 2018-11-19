Updating the model assertion
----------------------------

Make changes to the json file, then run the following commands to update the
signed assertion. You must have created and registered a signing key through
snapcraft before running these commands.

```bash
TIMESTAMP=$(date -Iseconds --utc)
sed s/%TIMESTAMP%/$TIMESTAMP/ paradrop-amd64.json | snap sign -k default &>paradrop-amd64.model
sed s/%TIMESTAMP%/$TIMESTAMP/ paradrop-pi2.json | snap sign -k default &>paradrop-pi2.model
```

Related documentation:
https://docs.ubuntu.com/core/en/guides/build-device/image-building
