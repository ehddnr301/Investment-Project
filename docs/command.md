# How to Start Investment-Project (Command)

## Terraform

- `cd terraform`
- `terraform init`
- `terraform apply -var-file="terraform.tfvars"`

### Terraform 준비물

```terraform.tfvars
iam_user_name = "dwlee"
my_project_id = "my-project-id-392842"
```
- `terraform.tfvars` 파일을 `terraform directory` 아래 생성합니다.
- [TerraformGuid](https://docs.google.com/presentation/d/1oTTSVRX9fK8sDZ4qC83s2BPVPV-RKry6C4TABuvN360/edit?usp=sharing)

## Ansible

- `cd ansible`
- `ansible-playbook -i hosts initial.yaml`
- `ansible-playbook -i hosts kube-dependencies.yaml`
- `ansible-playbook -i hosts master.yaml`
- `ansible-playbook -i hosts workers.yaml`
- `ansible-playbook -i hosts nfs.yaml`

### Ansible 준비물

```ansible.cfg
[defaults]
host_key_checking = False
private_key_file = ~/Investment-Project/terraform/assets/my_key
remote_user = dwlee
```
- `ansible.cfg` 파일을 `ansible directory` 아래 생성합니다.

```hosts
[masters]
master ansible_host=11.111.111.237 private_ip=10.111.0.37 ansible_user=dwlee repo_url=https://github.com/ehddnr301/Investment-Project

[workers]
worker1 ansible_host=11.111.111.254 private_ip=10.111.0.36 ansible_user=dwlee repo_url=https://github.com/ehddnr301/Investment-Project
worker2 ansible_host=11.111.111.182 private_ip=10.111.0.35 ansible_user=dwlee repo_url=https://github.com/ehddnr301/Investment-Project
```
- `hosts` 파일을 `ansible directory` 아래 생성합니다.

## In-Project

- `cd src`
- `bash create_env_file.sh`
- `bash start.sh`
- 적재 및 학습 파이프라인의 시나리오상 초반부는 실패하지만 이후에는 성공합니다.