data "template_file" "ssh_key" {
  template = "${file("~/rt.pub")}"
}

variable "iam_user_name" {
  type        = string
  default     = "dongwook.test0"
}
provider "google" {
  project     = "zinc-citron-377504"
  region      = "us-west4-b"
  zone        = "us-west4-b"
  credentials = file("${path.module}/zinc-citron-377504-4b465c7c2086.json")
}

resource "google_compute_instance" "vm_instance" {
  count       = 3
  name        = "terraform-instance-${count.index}"
  machine_type = "e2-highcpu-4"

  boot_disk {
    initialize_params {
      image  = "ubuntu-os-cloud/ubuntu-2004-lts"
      size = 50
    }
  }

  network_interface {
    network = "default"
    access_config {
    }
  }

  metadata = {
    ssh-keys = "${var.iam_user_name}:${data.template_file.ssh_key.rendered}"
  }
}

output "MYOUTPUT" {
  value = "${data.template_file.ssh_key.rendered}"
}