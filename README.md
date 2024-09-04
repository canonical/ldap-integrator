# ldap-integrator

[![CharmHub Badge](https://charmhub.io/ldap-integrator/badge.svg)](https://charmhub.io/ldap-integrator)
[![Juju](https://img.shields.io/badge/Juju%20-3.0+-%23E95420)](https://github.com/juju/juju)
[![License](https://img.shields.io/github/license/canonical/ldap-integrator?label=License)](https://github.com/canonical/ldap-integrator/blob/main/LICENSE)

[![Continuous Integration Status](https://github.com/canonical/ldap-integrator/actions/workflows/on_push.yaml/badge.svg?branch=main)](https://github.com/canonical/ldap-integrator/actions?query=branch%3Amain)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196.svg)](https://conventionalcommits.org)

## Description

This charm is used to configure an ldap client charm to use an external ldap service.

## Usage

In this section we are going to deploy the
[glauth operator](https://charmhub.io/glauth-k8s) and use the ldap integrator
to connect it to an existing LDAP server.

### Prerequisites

You will need:

- A juju deployment
- An existing LDAP server of your choice and you will need a bind_dn + password
  for glauth to use

### Deployment

First you will need to deploy the charms:

```console
juju deploy glauth-k8s --channel edge --trust
juju deploy ldap-integrator --channel edge --trust
juju deploy self-signed-certificates --channel stable --trust
```

### Configuration

Now that we have deployed our charms, we will need to configure ldap-integrator.

First we need to create a juju secret with the bind password:

```console
juju add-secret my-secret password=<bind_password>
```

Now we need to grant access to the secret to the ldap-integrator:

```console
juju grant-secret my-secret ldap-integrator
```

Then you will have to configure the ldap-integrator, eg:

```console
juju config ldap-integrator urls=ldap://path/to/somewhere base_dn=dc=glauth,dc=com bind_dn=cn=user,ou=group,dc=glauth,dc=com bind_password=my-secret
```

Now you can integrate glauth with ldap-integrator:

```console
juju integrate glauth-k8s ldap-integrator
```

Now glauth will be proxying all ldap requests to your ldap server.

## Other resources

- [Read more](https://charmhub.io/topics/canonical-identity-platform)

- [Contributing](CONTRIBUTING.md)

- See the [Juju SDK documentation](https://juju.is/docs/sdk) for more
information about developing and improving charms.
