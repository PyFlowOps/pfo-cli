# Kubernetes Clustering (Kind)

This section documents how to build, and deploy your own Kind cluster with the PyFlowOps applications already wired up.

## Invoke the Kubernetes Command Group

```bash
pfo k8s

```

You will be presented with the menu - _subject to change_.

--create --> Creates a cluster with a `local` namespace.
--delete --> Deletes the `local` cluster.
--delete-all --> Deletes all clusters.
--update --> Updates the Kubernetes _(Kind)_ cluster.
--info --> Returns info of the current cluster - `local`.

### Create the `local` Cluster with kind

The below command will build the Kubernetes cluster locally in the `local` namespace, with PyFlowOps already wired up.

```bash
pfo k8s --create
```

You will need to forward the service port to your local machine to access the services.

Example: `kubectl port-foward [resource-type/resource-name] [local-port]:[remote-port]`

To access the documentation website (MKDocs) from the Kubernetes cluster, you will need the service:

```bash
kubectl get services
```

The Documentation site service is: `documentation`

To forward the service port:

```bash
kubectl port-forward service/documentation 8100:8100
```
