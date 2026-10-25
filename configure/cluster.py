"""The two things the demo does in Agent Manager's Kubernetes cluster itself,
where Agent Manager 1.0 has no setting for them.

Agent Manager runs agents in a sandbox: they reach the model gateway, the
identity provider and the public internet, nothing else. One network rule
lets the bank's agents reach the bank's own gateways too, and only them.

Each run of Agent Manager's checks leaves objects behind in the cluster,
which slow every deployment down as they pile up; the ones whose run is
gone are cleared here."""
import json
import shlex
import subprocess

from configure.api import CONF, ORG, PROJECT

KUBECTL = shlex.split(CONF["AMP_KUBECTL"])


def kubectl(*args, stdin=None):
    return subprocess.run(KUBECTL + list(args), input=stdin, capture_output=True, text=True, check=True).stdout


def allow_bank_gateways(address, ports):
    """In each environment of the bank's project: its agents may reach this
    address on these ports."""
    namespaces = [name.split("/")[-1] for name in kubectl("get", "namespaces", "-o", "name").split()
                  if name.split("/")[-1].startswith("dp-%s-%s-" % (ORG, PROJECT))]
    for namespace in namespaces:
        kubectl("apply", "-f", "-", stdin=json.dumps({
            "apiVersion": "networking.k8s.io/v1", "kind": "NetworkPolicy",
            "metadata": {"name": "bank-gateways", "namespace": namespace},
            "spec": {"podSelector": {}, "policyTypes": ["Egress"], "egress": [{
                "to": [{"ipBlock": {"cidr": address + "/32"}}],
                "ports": [{"port": port, "protocol": "TCP"} for port in ports]}]}}))
    return len(namespaces)


def clear_leftovers():
    """Clears what finished runs of Agent Manager's checks left behind."""
    namespace = "workflows-" + ORG
    runs = {name.split("/")[-1] for name in kubectl("get", "workflows.argoproj.io", "-n", namespace, "-o", "name").split()}
    leftovers = [name.split("/")[-1] for name in kubectl("get", "externalsecrets.external-secrets.io", "-n", namespace,
                                                         "-o", "name").split()]
    leftovers = [name for name in leftovers if not any(name.startswith(run + "-") for run in runs)]
    for start in range(0, len(leftovers), 100):
        kubectl("delete", "externalsecrets.external-secrets.io", "-n", namespace, "--wait=false", *leftovers[start:start + 100])
    return len(leftovers)


def address(host):
    """The address the cluster gives to a host name it knows, such as host.k3d.internal."""
    hosts = kubectl("get", "configmap", "coredns", "-n", "kube-system", "-o", "jsonpath={.data.NodeHosts}")
    return next(line.split()[0] for line in hosts.splitlines() if host in line.split()[1:])
