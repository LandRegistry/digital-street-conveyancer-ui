# Digital Street UI

## Quick start

### Docker

This app supports the HM Land Registry [common dev-env](https://github.com/LandRegistry/common-dev-env) so adding the following to your dev-env config file is enough:

```YAML
  conveyancer-ui:
    repo: git@github.com:LandRegistry/digital-street-conveyancer-ui.git
    branch: master
```

The Docker image it creates (and runs) will install all necessary requirements and set all environment variables for you.

Note: Multiple instances of the repo will be spawned, with some environment variables being set in the [docker-compose-fragment.yml](fragments/docker-compose-fragment.yml) and the rest in the, regular, [Dockerfile](Dockerfile)

### Entry points for conveyancers, seller and buyer journeys

1. Conveyancer journey
    * Case list - http://localhost:xxxx/admin/case-list

2. Seller/buyer journey
    * Agreement ready for signing notification – http://localhost:xxxx/user/agreement-transfer-notify?title_id=ZQV888861&case_reference=HETC016
    * Transfer complete notification - http://localhost:xxxx/user/complete-notify?title_id=ZQV888861&case_reference=HETC016
