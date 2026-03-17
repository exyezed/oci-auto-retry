import oci
import time
import datetime
import os

COMPARTMENT_ID      = os.environ["OCI_COMPARTMENT_ID"]
SUBNET_ID           = os.environ["OCI_SUBNET_ID"]
IMAGE_ID            = os.environ["OCI_IMAGE_ID"]
AVAILABILITY_DOMAIN = os.environ["OCI_AD"]
SSH_PUBLIC_KEY      = os.environ["OCI_SSH_PUBLIC_KEY"]

config = {
    "user":        os.environ["OCI_USER"],
    "fingerprint": os.environ["OCI_FINGERPRINT"],
    "tenancy":     os.environ["OCI_TENANCY"],
    "region":      os.environ["OCI_REGION"],
    "key_content": os.environ["OCI_KEY_CONTENT"],
}

compute = oci.core.ComputeClient(config)

details = oci.core.models.LaunchInstanceDetails(
    availability_domain=AVAILABILITY_DOMAIN,
    compartment_id=COMPARTMENT_ID,
    display_name="easypanel",
    shape="VM.Standard.A1.Flex",
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=4,
        memory_in_gbs=24
    ),
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        image_id=IMAGE_ID
    ),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        subnet_id=SUBNET_ID,
        assign_public_ip=True
    ),
    metadata={
        "ssh_authorized_keys": SSH_PUBLIC_KEY
    }
)

now = datetime.datetime.now().strftime("%H:%M:%S")
print(f"[{now}] Trying to create instance...")
try:
    response = compute.launch_instance(details)
    print("BERHASIL! Instance sedang dibuat!")
    print(response.data)
except oci.exceptions.ServiceError as e:
    msg = str(e.message) if e.message else str(e)
    if "capacity" in msg.lower():
        print(f"No capacity yet, will retry on next schedule.")
    elif "too many" in msg.lower():
        print(f"Rate limited.")
    else:
        print(f"Error: {msg}")
        exit(1)
