<pre>
____    ____ ______   _______      ___     
\   \  /   //  __  \ |       \    /   \    
 \   \/   /|  |  |  ||  .--.  |  /  ^  \   
  \_    _/ |  |  |  ||  |  |  | /  /_\  \  
    |  |   |  `--'  ||  '--'  |/  _____  \ 
    |__|    \______/ |_______//__/     \__\
</pre>
Yoda provides a dynamic proxy solution using haproxy, etcd and confd. 
A lot of code/config has been ported from deis project. The etcd structure 
has been adopted based on Vulcand project. The intent of this proxy is to replace
totem proxy.

![Etcd Layout](architecture/etcd-layout.jpg) 

## Status
**In Testing**. Initial development complete. It is still not ready for production use.
Etcd structure is more or less frozen.

## Pre-Requesites
- [Docker v1.1+](https://docs.docker.com/)
- [etcd](https://coreos.com/using-coreos/etcd/)
- [etcdctl](https://github.com/coreos/etcd/releases/) (or curl or any other client for setting etcd keys)

## Running Proxy

In order to run proxy, you need docker v1.1.0+ installed on your host. 

### Execution without SNI SSL Certificates
```
sudo docker run --name yoda --rm -t -i -P -p 80:80 -p 443:443 -p 2022:22 totem/yoda-proxy
```

### Execution with SNI SSL Certificates
In order to run with SNI certificates, you need to have Amazon S3 account with
read permission on ssl certificates bucket. Your S3 certificates should be 
grouped together with key prefix (or fodler name "certs.d").  

E.g.:
yoda-s3-bucket/certs.d/default.pem   (Note: Default cert is mandatory)
yoda-s3-bucket/certs.d/certificate1.pem  
yoda-s3-bucket/certs.d/certificate2.pem  

For SNI to work, ensure that each PEM certificate consists of : 
Private Key, Public Key, CA Chain (In this order).  

Once ssl bucket is setup, simply run command below to start your proxy:  

```
sudo docker run --name yoda --rm -t -i -P -p 80:80 -p 443:443 -p 2022:22 -e AWS_ACCESS_KEY_ID=<<S3_ACCESS_KEY_ID>> -e AWS_SECRET_ACCESS_KEY=<<S3_SECRET_KEY>> -e S3_YODA_BUCKET=<<S3_BUCKET_NAME>> -e SYNC_CERTS=true totem/yoda-proxy
```

## ETCD Configuration

###Upstreams (Backend Servers)
In order to register your backend servers for your host, run command:
```
etcdctl set /yoda/upstreams/<<upstream-name>>/endpoints/<<service-name>> <<service-host>>:<<service-port>>
```
where:  
**upstream-name** is logical name for your upstream. e.g.: backend-abc.myapp.com  
**service-name** is name of your service. E.g.: node1  
**service-host** is host/ip address for your service  
**service-port** is port at which your service listens to.  

e.g: 
```
etcdctl set /yoda/upstreams/backend-abc.myapp.com/endpoints/node1 10.12.12.101:80
etcdctl set /yoda/upstreams/backend-abc.myapp.com/endpoints/node2 10.12.12.101:80
```  

If backend is of the type tcp and not http, also add the mode for the upstream.
e.g:  
```
etcdctl set /yoda/upstreams/backend-abc.myapp.com/mode tcp
```

###Host and Location Information
In order to register your hosts and location:
- **Specify allowed, denied, acls**  
  /yoda/hosts/{hostname}/locations/{location-name}/acls/allowed/{allowed-entry-name} {acl_name}
  /yoda/hosts/abc.myapp.com/locations/home/acls/denied/{denied-entry-name} {acl_name}  
  e.g.:  

```
etcdctl set /yoda/hosts/abc.myapp.com/locations/home/acls/allowed/a1 public
etcdctl set /yoda/hosts/abc.myapp.com/locations/home/acls/denied/d1 global-black-list
```  

- **Specify Proxy Path**  
  /yoda/hosts/{hostname}/locations/{location-name}/path {path_value}  
  e.g.:
```
etcdctl set /yoda/hosts/abc.myapp.com/locations/home/path /
```  

- **Specify Upstream for proxy**  
  /yoda/hosts/{hostname}/locations/{location-name}/upstream {upstream}
  e.g.:
```
etcdctl set /yoda/hosts/abc.myapp.com/locations/home/upstream backend-abc.myapp.com
```
Once you are ready to switch proxy to new upstream for doing blue-green deploys, 
simply execute command:  
```
etcdctl set /yoda/hosts/abc.myapp.com/locations/home/upstream backend-abc.myapp.com-v2
```

- **Specify Additional hosts (aliases) for proxy**  
  /yoda/hosts/{hostname}/aliases/{alias-name}  {alias}
  e.g.:
```
etcdctl set /yoda/hosts/abc.myapp.com/aliases/www www.myapp.com
```

###TCP Proxy Configuration
In order to configure tcp based proxy, add tcp listeners for the proxy. For e.g.
to add tcp listener for rabbitmq at port 5672, run commands:

```
etcdctl set /yoda/global/listeners/tcp/rabbitmq-main/bind 0.0.0.0:5672
etcdctl set /yoda/global/listeners/tcp/rabbitmq-main/upstream backend-rabbitmq
etcdctl set /yoda/global/listeners/tcp/rabbitmq-main/acls/allowed/a1 public
etcdctl set /yoda/global/listeners/tcp/rabbitmq-main/acls/denied/d1 global-black-list
```

Ensure that backend use mode as *tcp* and not *http*. 
```
etcdctl set /yoda/upstreams/backend-rabbitmq/mode tcp
```

In addition, to access listeners from outside, ensure that you provide port mapping option in docker
run command.
e.g. -p 5672:5672

## Integration Test
In order to execute integration test, you need  
- python 2.7.x  
- libffi-dev  
- libssl-dev

Install the requirements by executing following commands:  
```
cd test
pip install -r requirements.txt
```  

Once dependencies are installed, use nosetests to run the integration test from
test folder:  
```
nosetests --nocapture
```






