data "template_file" "ssh_key" {
  template = file("${path.module}/assets/my_key.pub")
}

provider "google" {
  project     = var.my_project_id
  region      = "us-west4-b"
  zone        = "us-west4-b"
  credentials = file("${path.module}/assets/${var.my_project_id}.json")
}

resource "google_compute_instance" "vm_instance" {
  count       = 3
  name        = "terraform-instance-${count.index}"
  machine_type = "e2-standard-2"

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
  value = data.template_file.ssh_key.rendered
}
