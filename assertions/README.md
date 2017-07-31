Updating the model assertion
----------------------------

1. Make changes to paradrop-amd64-model.json
2. Use the output of `date -Iseconds --utc` to update the timestamp field.
3. Sign the model assertion.  You must be logged in with an Ubuntu One account.
   `cat paradrop-amd64-model.json | snap sign -k default &>paradrop-amd64.model`

Related documentation:
https://docs.ubuntu.com/core/en/guides/build-device/image-building
