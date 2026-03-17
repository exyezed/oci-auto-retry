import oci
import datetime
import os
import urllib.request
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

COMPARTMENT_ID      = os.environ["OCI_COMPARTMENT_ID"]
SUBNET_ID           = os.environ["OCI_SUBNET_ID"]
IMAGE_ID            = os.environ["OCI_IMAGE_ID"]
AVAILABILITY_DOMAIN = os.environ["OCI_AD"]
SSH_PUBLIC_KEY      = os.environ["OCI_SSH_PUBLIC_KEY"]
DISCORD_WEBHOOK     = os.environ["DISCORD_WEBHOOK"]

config = {
    "user":        os.environ["OCI_USER"],
    "fingerprint": os.environ["OCI_FINGERPRINT"],
    "tenancy":     os.environ["OCI_TENANCY"],
    "region":      os.environ["OCI_REGION"],
    "key_content": os.environ["OCI_KEY_CONTENT"],
}

def send_discord(message):
    data = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req)

def try_create_instance():
    compute = oci.core.ComputeClient(config)

    # Cek apakah instance sudah ada
    instances = compute.list_instances(COMPARTMENT_ID).data
    for instance in instances:
        if instance.display_name == "easypanel" and instance.lifecycle_state not in ["TERMINATED", "TERMINATING"]:
            return f"Instance sudah ada, status: {instance.lifecycle_state}"

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
    try:
        response = compute.launch_instance(details)
        msg = f"BERHASIL! Instance easypanel dibuat!\nOCID: {response.data.id}"
        send_discord(msg)
        return msg
    except oci.exceptions.ServiceError as e:
        err = str(e.message) if e.message else str(e)
        if "capacity" in err.lower():
            return f"[{now}] No capacity yet."
        elif "too many" in err.lower():
            return f"[{now}] Rate limited."
        else:
            send_discord(f"OCI error tidak terduga: {err}")
            return f"[{now}] Error: {err}"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/retry":
            result = try_create_instance()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(result.encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress default logging

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Server running on port {port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
