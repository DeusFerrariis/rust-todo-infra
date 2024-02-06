"""A Python Pulumi program"""

import pulumi
from pulumi import Output
import pulumi_aws as aws
import pulumi_aws_native as aws_native
import json

class BinaryStore(pulumi.ComponentResource):
    def __init__(self, name, opts = None):
        super().__init__('pkg:index:BinaryStore', name, None, opts)

        self.binary_bucket = aws.s3.Bucket(
            "bin-store",
            acl="private",
            tags={},
        )

      
binary_store = BinaryStore("todo-binaries")

"""
    NETWORKING 
"""

vpc = aws.ec2.Vpc("my-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": "my-vpc",
    }
)

igw = aws.ec2.InternetGateway("igw-1", vpc_id=vpc.id)

public_route_table = aws.ec2.RouteTable(
    "pub_rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ) 
    ]
)

subnet = aws.ec2.Subnet(
    "my-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone="us-east-1a"
)

route_table = aws.ec2.RouteTable(
    "rt-1",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            # Route outbound traffic to igw-1
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ]
)

rt_assoc = aws.ec2.RouteTableAssociation(
    "rt_assoc",
    subnet_id=subnet.id,
    route_table_id=route_table.id
)

api_server_security_group = aws.ec2.SecurityGroup(
    "sec-group",
    vpc_id=vpc.id,
    ingress = [
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress = [
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)

"""
    API SERVER INSTANCE
"""

ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[{"name":"name","values":["amzn2-ami-hvm-*-x86_64-gp2"]}])

with open("api_server_init.sh", "r") as f:
    api_server_user_data = f.read()

api_server = aws.ec2.Instance(
    "rtfs-api-server",
    subnet_id=subnet.id,
    associate_public_ip_address=True,
    vpc_security_group_ids=[api_server_security_group.id],
    ami=ami.id,
    instance_type="t2.large",
    user_data=api_server_user_data,
)

"""
    API GATEWAY PROXY
"""

agw = aws.apigatewayv2.Api(
    "proxy-api",
    description="Proxies http requests to web server",
    protocol_type="HTTP",
    cors_configuration=aws.apigatewayv2.ApiCorsConfigurationArgs(
        allow_origins=["*"],
        allow_methods=["*"],  # Adjust if necessary to restrict to certain HTTP methods
        allow_headers=["*"],  # Adjust if necessary to restrict headers
    ),
)

api_integration = aws.apigatewayv2.Integration(
    "api-proxy-integration",
    api_id=agw.id,
    integration_type="HTTP_PROXY",
    integration_method="ANY",
    integration_uri=api_server.public_ip.apply(
        lambda ip: f"http://{ip}:80/{{proxy}}"
    ),
    timeout_milliseconds=29000,
)

api_proxy_route = aws.apigatewayv2.Route(
    "api-proxy-route",
    api_id=agw.id,
    route_key="ANY /api/{proxy+}",
    target=api_integration.id.apply(lambda id: f"integrations/{id}")
)

deployment = aws.apigatewayv2.Deployment(
    "deployment",
    api_id=agw.id,
    opts=pulumi.ResourceOptions(depends_on=[api_proxy_route]),
)

stage = aws.apigatewayv2.Stage(
    "stage",
    opts=pulumi.ResourceOptions(depends_on=[deployment]),
    api_id=agw.id,
    deployment_id=deployment.id,
    auto_deploy=True,
    name="dev"
)

"""
    WEB SERVER INSTANCE
"""

with open("web_server_init.sh", "r") as f:
    web_server_user_data = f.read()


web_server = aws.ec2.Instance(
    "rtfs-web-server",
    subnet_id=subnet.id,
    associate_public_ip_address=True,
    vpc_security_group_ids=[api_server_security_group.id],
    ami=ami.id,
    instance_type="t2.large",
    user_data=Output.all(agw.api_endpoint, stage.name).apply(
        lambda args: web_server_user_data.replace(
            "<API_URL>",
            f"{args[0]}/{args[1]}/api"
        )
    ),
)

web_proxy_integration = aws.apigatewayv2.Integration(
    "web-proxy-integration",
    api_id=agw.id,
    integration_type="HTTP_PROXY",
    integration_method="ANY",
    integration_uri=web_server.public_ip.apply(
        lambda ip: f"http://{ip}:80/{{proxy}}"
    ),
    timeout_milliseconds=29000,
)

web_proxy_route = aws.apigatewayv2.Route(
    "web-proxy-route",
    api_id=agw.id,
    route_key="ANY /web/{proxy+}",
    target=web_proxy_integration.id.apply(lambda id: f"integrations/{id}")
)

pulumi.export(
    "api_gateway_proxy_url",
    Output.all(agw.api_endpoint, stage.name).apply(
        lambda args: f"{args[0]}/{args[1]}"
    )
)
pulumi.export(
    "api_server_proxy_url",
    Output.all(agw.api_endpoint, stage.name).apply(
        lambda args: f"{args[0]}/{args[1]}/api"
    )
)
