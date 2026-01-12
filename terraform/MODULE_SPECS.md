<!-- BEGIN_TF_DOCS -->

---
## Providers

| Name | Version |
|------|---------|
| <a name="provider_juju"></a> [juju](#provider\_juju) | >= 1.0.0 |
---
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.6 |
| <a name="requirement_juju"></a> [juju](#requirement\_juju) | >= 1.0.0 |
---
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_model_uuid"></a> [model\_uuid](#input\_model\_uuid) | UUID of the Juju model to deploy to | `string` | n/a | yes |
| <a name="input_app_name"></a> [app\_name](#input\_app\_name) | Name of the application | `string` | `"ldap-integrator"` | no |
| <a name="input_base"></a> [base](#input\_base) | The charm base | `string` | `"ubuntu@22.04"` | no |
| <a name="input_channel"></a> [channel](#input\_channel) | Channel to use for the charm | `string` | `"latest/stable"` | no |
| <a name="input_config"></a> [config](#input\_config) | The charm config | `map(string)` | `{}` | no |
| <a name="input_constraints"></a> [constraints](#input\_constraints) | The constraints to be applied | `string` | `""` | no |
| <a name="input_revision"></a> [revision](#input\_revision) | Revision of the charm to deploy | `number` | `null` | no |
| <a name="input_units"></a> [units](#input\_units) | Number of units to deploy | `number` | `1` | no |
---
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_app_name"></a> [app\_name](#output\_app\_name) | The name of the deployed application |
| <a name="output_provides"></a> [provides](#output\_provides) | The Juju integrations that the charm provides |
<!-- END_TF_DOCS -->