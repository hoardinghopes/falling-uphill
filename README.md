# Falling Upwards
---

A bunch of personal thoughts and opinions, usually about Aikido, most often generating by walking our dog in the hills around us.

## Generating the static site
`python ./buster.py generate`

This uses a local version of [buster](https://github.com/axitkhurana/buster/tree/master/buster), which has setup stripped out, as I've already set up the project.

More importantly, it has changes to the URL-creating code: `wget` does not `--convert-links` to local, and I've re-written bits to replace the localhost with the github URL.

## Deploying the site
`python ./buster.py deploy`

This already has the `git` repository details so takes place quietly.

N.B. GitHub Pages take a short while to re-build after a deployment.

## If for any reason ...
If there is any need to use the original buster script, it is already installed, so just calling `buster` will start that script rather than the local version.
